"""
Equal Sharing (EQ) Value Share Model
=====================================

Algorithm 1 – Equal Sharing (EQ)

FOR each timestamp h DO
    Compute G_EC,h
    FOR each member i ∈ N DO
        G_i,h ← G_EC,h / |N|
    END FOR
END FOR
"""

import numpy as np
from typing import Dict, Tuple
from .value_sharing_utils import compute_timestamp_data


def equal_sharing(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_price: float,
    fit_price: float
) -> np.ndarray:
    """
    Equal Sharing value allocation.
    
    Each member receives an equal share of the community gain.
    
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
    
    # Equal sharing: divide community gain equally
    gain_per_member = data['community_gain'] / n_members
    
    # Allocate equal gain to all members
    allocations = np.ones(n_members) * gain_per_member
    
    return allocations


def equal_sharing_timeseries(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_prices: np.ndarray,
    fit_prices: np.ndarray
) -> Tuple[np.ndarray, Dict]:
    """
    Apply Equal Sharing across multiple timestamps.
    
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
    
    # Track total gains
    total_community_gains = np.zeros(n_timestamps)
    
    # Process each timestamp
    for h in range(n_timestamps):
        allocations[:, h] = equal_sharing(
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
    
    # Compute summary statistics
    summary = {
        'total_allocations_per_member': np.sum(allocations, axis=1),
        'total_community_gain': np.sum(total_community_gains),
        'avg_gain_per_timestamp': np.mean(total_community_gains),
        'method': 'Equal Sharing (EQ)'
    }
    
    return allocations, summary
