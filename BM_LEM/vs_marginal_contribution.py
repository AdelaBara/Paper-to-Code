"""
Marginal Contribution (MC) Value Share Model
============================================

Algorithm 4 – Marginal Contribution (MC)

FOR each timestamp h DO
    Compute G_EC,h for full set N

    FOR each member i ∈ N DO
        Compute gain without i:
            G_EC,h^(−i)
        MC_i,h ← G_EC,h − G_EC,h^(−i)
    END FOR

    Compute MC_sum ← Σ_i MC_i,h

    IF MC_sum = 0 THEN
        Apply Equal Sharing
    ELSE
        FOR each member i ∈ N DO
            G_i,h ← (MC_i,h / MC_sum) × G_EC,h
        END FOR
    END IF
END FOR
"""

import numpy as np
from typing import Dict, Tuple
from .value_sharing_utils import (
    compute_timestamp_data,
    compute_net_energy,
    compute_all_individual_payments,
    compute_community_net_energy,
    compute_community_payment,
    compute_community_gain
)
from .vs_equal_sharing import equal_sharing


def compute_gain_without_member(
    consumption: np.ndarray,
    generation: np.ndarray,
    member_idx: int,
    tou_price: float,
    fit_price: float
) -> float:
    """
    Compute community gain without a specific member.
    
    Args:
        consumption: Array of consumption values for all members
        generation: Array of generation values for all members
        member_idx: Index of member to exclude
        tou_price: Time-of-Use price
        fit_price: Feed-in tariff
    
    Returns:
        Community gain without the specified member
    """
    # Create mask to exclude member
    mask = np.ones(len(consumption), dtype=bool)
    mask[member_idx] = False
    
    # Subset without member i
    consumption_subset = consumption[mask]
    generation_subset = generation[mask]
    
    if len(consumption_subset) == 0:
        # No community without this member
        return 0.0
    
    # Compute net energy for subset
    net_energy_subset = compute_net_energy(consumption_subset, generation_subset)
    
    # Individual payments for subset
    individual_payments_subset = compute_all_individual_payments(
        net_energy_subset, tou_price, fit_price
    )
    
    # Community aggregates for subset
    community_net_energy_subset = compute_community_net_energy(net_energy_subset)
    community_payment_subset = compute_community_payment(
        community_net_energy_subset, tou_price, fit_price
    )
    
    # Gain for subset
    gain_subset = compute_community_gain(individual_payments_subset, community_payment_subset)
    
    return gain_subset


def marginal_contribution_sharing(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_price: float,
    fit_price: float
) -> np.ndarray:
    """
    Marginal Contribution value allocation.
    
    Members receive gain proportional to their marginal contribution to community gain.
    Falls back to equal sharing if sum of marginal contributions is zero.
    
    Args:
        consumption: Array of consumption values for each member [kWh]
        generation: Array of generation values for each member [kWh]
        tou_price: Time-of-Use price [€/kWh]
        fit_price: Feed-in tariff [€/kWh]
    
    Returns:
        Array of gain allocations for each member [€]
    """
    # Compute all timestamp data for full community
    data = compute_timestamp_data(consumption, generation, tou_price, fit_price)
    full_gain = data['community_gain']
    
    # Number of members
    n_members = len(consumption)
    
    # Compute marginal contribution for each member
    marginal_contributions = np.zeros(n_members)
    
    for i in range(n_members):
        # Gain without member i
        gain_without_i = compute_gain_without_member(
            consumption, generation, i, tou_price, fit_price
        )
        
        # Marginal contribution = full gain - gain without i
        marginal_contributions[i] = full_gain - gain_without_i
    
    # Sum of marginal contributions
    mc_sum = np.sum(marginal_contributions)
    
    # If MC sum is zero or very close to zero, apply equal sharing
    if abs(mc_sum) < 1e-10:
        return equal_sharing(consumption, generation, tou_price, fit_price)
    
    # Allocate gain proportional to marginal contribution
    allocations = (marginal_contributions / mc_sum) * full_gain
    
    return allocations


def marginal_contribution_sharing_timeseries(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_prices: np.ndarray,
    fit_prices: np.ndarray
) -> Tuple[np.ndarray, Dict]:
    """
    Apply Marginal Contribution Sharing across multiple timestamps.
    
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
        allocations[:, h] = marginal_contribution_sharing(
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
        
        # Check if equal sharing was applied (MC sum was zero)
        # We can detect this by checking if allocations are equal
        if np.allclose(allocations[:, h], allocations[0, h]):
            equal_sharing_count += 1
    
    # Compute summary statistics
    summary = {
        'total_allocations_per_member': np.sum(allocations, axis=1),
        'total_community_gain': np.sum(total_community_gains),
        'avg_gain_per_timestamp': np.mean(total_community_gains),
        'equal_sharing_fallback_count': equal_sharing_count,
        'method': 'Marginal Contribution (MC)'
    }
    
    return allocations, summary
