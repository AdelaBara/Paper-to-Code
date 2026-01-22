"""
Shapley Value (Approximate) Value Share Model
=============================================

Algorithm 5 – Shapley Value (Approximate)

Characteristic function:
v(S) = Pay^0(S) − Pay_EC(S)

FOR each timestamp h DO
    Initialize φ_i,h ← 0 for all i ∈ N

    FOR k = 1 to K random permutations DO
        Draw random permutation π of N
        S ← ∅

        FOR each i in order π DO
            Δ ← v(S ∪ {i}) − v(S)
            φ_i,h ← φ_i,h + Δ
            S ← S ∪ {i}
        END FOR
    END FOR

    FOR each member i ∈ N DO
        φ_i,h ← φ_i,h / K
    END FOR

    Normalize:
        G_i,h ← (φ_i,h / Σ_j φ_j,h) × G_EC,h
END FOR
"""

import numpy as np
from typing import Dict, Tuple, List
from .value_sharing_utils import (
    compute_net_energy,
    compute_all_individual_payments,
    compute_community_net_energy,
    compute_community_payment,
    compute_community_gain,
    compute_timestamp_data,
    normalize_allocations
)


def characteristic_function(
    consumption: np.ndarray,
    generation: np.ndarray,
    coalition_indices: List[int],
    tou_price: float,
    fit_price: float
) -> float:
    """
    Compute characteristic function v(S) for a coalition.
    
    v(S) = Pay^0(S) - Pay_EC(S)
    
    Args:
        consumption: Array of consumption for all members
        generation: Array of generation for all members
        coalition_indices: List of member indices in coalition S
        tou_price: Time-of-Use price
        fit_price: Feed-in tariff
    
    Returns:
        Value of coalition (gain from cooperation)
    """
    if len(coalition_indices) == 0:
        return 0.0
    
    # Subset for coalition
    consumption_coalition = consumption[coalition_indices]
    generation_coalition = generation[coalition_indices]
    
    # Compute net energy for coalition members
    net_energy = compute_net_energy(consumption_coalition, generation_coalition)
    
    # Individual payments (if acting alone)
    individual_payments = compute_all_individual_payments(net_energy, tou_price, fit_price)
    
    # Community aggregates for coalition
    community_net_energy = compute_community_net_energy(net_energy)
    community_payment = compute_community_payment(community_net_energy, tou_price, fit_price)
    
    # Coalition gain
    coalition_gain = compute_community_gain(individual_payments, community_payment)
    
    return coalition_gain


def shapley_value_sharing(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_price: float,
    fit_price: float,
    n_permutations: int = 100,
    random_seed: int = None
) -> np.ndarray:
    """
    Shapley Value allocation (approximate via sampling).
    
    Uses Monte Carlo sampling over random permutations to approximate Shapley values.
    
    Args:
        consumption: Array of consumption values for each member [kWh]
        generation: Array of generation values for each member [kWh]
        tou_price: Time-of-Use price [€/kWh]
        fit_price: Feed-in tariff [€/kWh]
        n_permutations: Number of random permutations to sample (K)
        random_seed: Random seed for reproducibility
    
    Returns:
        Array of gain allocations for each member [€]
    """
    # Set random seed if provided
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Compute all timestamp data for full community
    data = compute_timestamp_data(consumption, generation, tou_price, fit_price)
    full_gain = data['community_gain']
    
    # Number of members
    n_members = len(consumption)
    
    # Initialize Shapley values
    shapley_values = np.zeros(n_members)
    
    # Sample K random permutations
    for k in range(n_permutations):
        # Generate random permutation of member indices
        permutation = np.random.permutation(n_members)
        
        # Current coalition (starts empty)
        coalition = []
        
        # Process each member in permutation order
        for i in permutation:
            # Value of coalition before adding member i
            value_before = characteristic_function(
                consumption, generation, coalition, tou_price, fit_price
            )
            
            # Add member i to coalition
            coalition.append(i)
            
            # Value of coalition after adding member i
            value_after = characteristic_function(
                consumption, generation, coalition, tou_price, fit_price
            )
            
            # Marginal contribution of member i in this permutation
            marginal_contribution = value_after - value_before
            
            # Accumulate to Shapley value
            shapley_values[i] += marginal_contribution
    
    # Average over all permutations
    shapley_values = shapley_values / n_permutations
    
    # Normalize to distribute full gain
    allocations = normalize_allocations(shapley_values, full_gain)
    
    return allocations


def shapley_value_sharing_timeseries(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_prices: np.ndarray,
    fit_prices: np.ndarray,
    n_permutations: int = 100,
    random_seed: int = None
) -> Tuple[np.ndarray, Dict]:
    """
    Apply Shapley Value Sharing across multiple timestamps.
    
    Args:
        consumption: 2D array [n_members x n_timestamps]
        generation: 2D array [n_members x n_timestamps]
        tou_prices: Array of ToU prices for each timestamp [n_timestamps]
        fit_prices: Array of FiT prices for each timestamp [n_timestamps]
        n_permutations: Number of random permutations per timestamp
        random_seed: Random seed for reproducibility
    
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
        # Use different seed for each timestamp if base seed provided
        timestamp_seed = None if random_seed is None else random_seed + h
        
        allocations[:, h] = shapley_value_sharing(
            consumption[:, h],
            generation[:, h],
            tou_prices[h],
            fit_prices[h],
            n_permutations=n_permutations,
            random_seed=timestamp_seed
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
        'n_permutations': n_permutations,
        'method': 'Shapley Value (Approximate)'
    }
    
    return allocations, summary
