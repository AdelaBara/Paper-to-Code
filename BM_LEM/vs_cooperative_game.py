"""
Cooperative Game (CG) Value Share Model
=======================================

Algorithm 6 – Cooperative Game (CG)

Net energy already defined:
W_i,h^net = W_i,h^c − W_i,h^g

FOR each timestamp h DO
    Compute G_EC,h
    n ← |N|
    base ← G_EC,h / n

    Define:
        D ← {i | W^net_i,h > 0}   (deficit members)
        S ← {i | W^net_i,h < 0}   (surplus members)

    Compute:
        D_sum ← Σ_{i∈D} W^net_i,h
        S_sum ← Σ_{i∈S} W^net_i,h   (negative)

    FOR each member i ∈ N DO
        IF i ∈ D THEN
            q_D,i ← W^net_i,h / D_sum
            G_i,h ← (1 − q_D,i) × base
        ELSE IF i ∈ S THEN
            q_S,i ← W^net_i,h / S_sum
            G_i,h ← (1 + q_S,i) × base
        ELSE
            G_i,h ← base
        END IF
    END FOR

    Normalize allocations so that:
        Σ_i G_i,h = G_EC,h
END FOR
"""

import numpy as np
from typing import Dict, Tuple
from .value_sharing_utils import compute_timestamp_data, normalize_allocations


def cooperative_game_sharing(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_price: float,
    fit_price: float
) -> np.ndarray:
    """
    Cooperative Game value allocation.
    
    Allocates gain based on net energy position:
    - Deficit members (consumers) receive less than base share
    - Surplus members (generators) receive more than base share
    - Balanced members receive base share
    
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
    
    # Base allocation (equal sharing)
    base = data['community_gain'] / n_members
    
    # Net energy for each member
    net_energy = data['net_energy']
    
    # Classify members
    deficit_mask = net_energy > 0  # Positive net energy = deficit (consuming more)
    surplus_mask = net_energy < 0  # Negative net energy = surplus (generating more)
    balanced_mask = net_energy == 0  # Balanced
    
    # Compute sums for deficit and surplus groups
    deficit_sum = np.sum(net_energy[deficit_mask]) if np.any(deficit_mask) else 0
    surplus_sum = np.sum(net_energy[surplus_mask]) if np.any(surplus_mask) else 0  # Will be negative
    
    # Initialize allocations
    allocations = np.zeros(n_members)
    
    # Allocate to each member based on their position
    for i in range(n_members):
        if deficit_mask[i]:
            # Deficit member: receives less than base
            if deficit_sum > 0:
                q_D_i = net_energy[i] / deficit_sum
                allocations[i] = (1 - q_D_i) * base
            else:
                allocations[i] = base
                
        elif surplus_mask[i]:
            # Surplus member: receives more than base
            if surplus_sum < 0:
                q_S_i = net_energy[i] / surplus_sum  # Both are negative, ratio is positive
                allocations[i] = (1 + q_S_i) * base
            else:
                allocations[i] = base
                
        else:
            # Balanced member: receives base
            allocations[i] = base
    
    # Normalize allocations to ensure they sum to total gain
    allocations = normalize_allocations(allocations, data['community_gain'])
    
    return allocations


def cooperative_game_sharing_timeseries(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_prices: np.ndarray,
    fit_prices: np.ndarray
) -> Tuple[np.ndarray, Dict]:
    """
    Apply Cooperative Game Sharing across multiple timestamps.
    
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
    
    # Track total gains and member classifications
    total_community_gains = np.zeros(n_timestamps)
    deficit_count = np.zeros(n_timestamps)
    surplus_count = np.zeros(n_timestamps)
    balanced_count = np.zeros(n_timestamps)
    
    # Process each timestamp
    for h in range(n_timestamps):
        allocations[:, h] = cooperative_game_sharing(
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
        
        # Count member types
        net_energy = data['net_energy']
        deficit_count[h] = np.sum(net_energy > 0)
        surplus_count[h] = np.sum(net_energy < 0)
        balanced_count[h] = np.sum(net_energy == 0)
    
    # Compute summary statistics
    summary = {
        'total_allocations_per_member': np.sum(allocations, axis=1),
        'total_community_gain': np.sum(total_community_gains),
        'avg_gain_per_timestamp': np.mean(total_community_gains),
        'avg_deficit_members': np.mean(deficit_count),
        'avg_surplus_members': np.mean(surplus_count),
        'avg_balanced_members': np.mean(balanced_count),
        'method': 'Cooperative Game (CG)'
    }
    
    return allocations, summary
