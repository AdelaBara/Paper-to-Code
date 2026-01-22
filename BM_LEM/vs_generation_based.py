"""
Generation-based Sharing (G-based) Value Share Model
====================================================

Algorithm 2 – Generation-based Sharing (G-based)

Adaptation: no exogenous quota → use observed generation share.

FOR each timestamp h DO
    Compute G_EC,h
    Compute total generation:
        G_tot ← Σ_i W^g_i,h

    IF G_tot = 0 THEN
        Apply Equal Sharing
    ELSE
        FOR each member i ∈ N DO
            q_i,h ← W^g_i,h / G_tot
            G_i,h ← q_i,h × G_EC,h
        END FOR
    END IF
END FOR
"""

import numpy as np
from typing import Dict, Tuple
from .value_sharing_utils import compute_timestamp_data
from .vs_equal_sharing import equal_sharing


def generation_based_sharing(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_price: float,
    fit_price: float
) -> np.ndarray:
    """
    Generation-based Sharing value allocation.
    
    Members receive gain proportional to their generation contribution.
    Falls back to equal sharing if no generation.
    
    Args:
        consumption: Array of consumption values for each member [kWh]
        generation: Array of generation values for each member [kWh]
        tou_price: Time-of-Use price [€/kWh]
        fit_price: Feed-in tariff [€/kWh]
    
    Returns:
        Array of gain allocations for each member [€]
    """
    # Compute all timestamp data
    data = compute_timestamp_data(consumption, generation, tou_price, fit_price)
    
    # Number of members
    n_members = len(consumption)
    
    # Compute total generation
    total_generation = np.sum(generation)
    
    # If no generation, apply equal sharing
    if total_generation == 0:
        return equal_sharing(consumption, generation, tou_price, fit_price)
    
    # Compute generation share for each member
    generation_shares = generation / total_generation
    
    # Allocate gain proportional to generation share
    allocations = generation_shares * data['community_gain']
    
    return allocations


def generation_based_sharing_timeseries(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_prices: np.ndarray,
    fit_prices: np.ndarray
) -> Tuple[np.ndarray, Dict]:
    """
    Apply Generation-based Sharing across multiple timestamps.
    
    Args:
        consumption: 2D array [n_members x n_timestamps]
        generation: 2D array [n_members x n_timestamps]
        tou_prices: Array of ToU prices for each timestamp [n_timestamps]
        fit_prices: Array of FiT prices for each timestamp [n_timestamps]
    
    Returns:
        Tuple of:
            - allocations: 2D array of gain allocations [n_members x n_timestamps]
            - summary: Dictionary with aggregated metrics
    """
    n_members, n_timestamps = consumption.shape
    
    # Initialize allocations array
    allocations = np.zeros((n_members, n_timestamps))
    
    # Track total gains and fallback counts
    total_community_gains = np.zeros(n_timestamps)
    equal_sharing_count = 0
    
    # Process each timestamp
    for h in range(n_timestamps):
        allocations[:, h] = generation_based_sharing(
            consumption[:, h],
            generation[:, h],
            tou_prices[h],
            fit_prices[h]
        )
        
        # Record community gain for this timestamp
        data = compute_timestamp_data(
            consumption[:, h],
            generation[:, h],
            tou_prices[h],
            fit_prices[h]
        )
        total_community_gains[h] = data['community_gain']
        
        # Check if equal sharing was applied
        if np.sum(generation[:, h]) == 0:
            equal_sharing_count += 1
    
    # Compute summary statistics
    summary = {
        'total_allocations_per_member': np.sum(allocations, axis=1),
        'total_community_gain': np.sum(total_community_gains),
        'avg_gain_per_timestamp': np.mean(total_community_gains),
        'equal_sharing_fallback_count': equal_sharing_count,
        'method': 'Generation-based Sharing (G-based)'
    }
    
    return allocations, summary
