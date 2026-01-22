"""
Value Sharing Models - Main Interface
=====================================

This module provides a unified interface for all value sharing models.

Available Models:
1. Equal Sharing (EQ)
2. Generation-based Sharing (G-based)
3. Consumption-based Sharing (C-based)
4. Marginal Contribution (MC)
5. Shapley Value (Approximate)
6. Cooperative Game (CG)
"""

import numpy as np
from typing import Dict, Tuple, Optional
from enum import Enum

from .vs_equal_sharing import equal_sharing_timeseries
from .vs_generation_based import generation_based_sharing_timeseries
from .vs_consumption_based import consumption_based_sharing_timeseries
from .vs_marginal_contribution import marginal_contribution_sharing_timeseries
from .vs_shapley_value import shapley_value_sharing_timeseries
from .vs_cooperative_game import cooperative_game_sharing_timeseries


class ValueSharingMethod(Enum):
    """Enumeration of available value sharing methods."""
    EQUAL = "EQ"
    GENERATION_BASED = "G-based"
    CONSUMPTION_BASED = "C-based"
    MARGINAL_CONTRIBUTION = "MC"
    SHAPLEY_VALUE = "Shapley"
    COOPERATIVE_GAME = "CG"


def apply_value_sharing(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_prices: np.ndarray,
    fit_prices: np.ndarray,
    method: ValueSharingMethod = ValueSharingMethod.EQUAL,
    shapley_permutations: int = 100,
    random_seed: Optional[int] = None
) -> Tuple[np.ndarray, Dict]:
    """
    Apply a value sharing method to energy community data.
    
    Args:
        consumption: 2D array [n_members x n_timestamps] of consumption data [kWh]
        generation: 2D array [n_members x n_timestamps] of generation data [kWh]
        tou_prices: Array [n_timestamps] of Time-of-Use prices [€/kWh]
        fit_prices: Array [n_timestamps] of Feed-in Tariff prices [€/kWh]
        method: Value sharing method to apply
        shapley_permutations: Number of permutations for Shapley value (default: 100)
        random_seed: Random seed for reproducibility (used in Shapley)
    
    Returns:
        Tuple of:
            - allocations: 2D array [n_members x n_timestamps] of gain allocations [€]
            - summary: Dictionary with aggregated metrics and method information
    
    Raises:
        ValueError: If method is not recognized or inputs have incompatible shapes
    """
    # Validate inputs
    if consumption.shape != generation.shape:
        raise ValueError("Consumption and generation arrays must have the same shape")
    
    n_members, n_timestamps = consumption.shape
    
    if len(tou_prices) != n_timestamps:
        raise ValueError(f"ToU prices length ({len(tou_prices)}) must match number of timestamps ({n_timestamps})")
    
    if len(fit_prices) != n_timestamps:
        raise ValueError(f"FiT prices length ({len(fit_prices)}) must match number of timestamps ({n_timestamps})")
    
    # Apply selected method
    if method == ValueSharingMethod.EQUAL:
        return equal_sharing_timeseries(consumption, generation, tou_prices, fit_prices)
    
    elif method == ValueSharingMethod.GENERATION_BASED:
        return generation_based_sharing_timeseries(consumption, generation, tou_prices, fit_prices)
    
    elif method == ValueSharingMethod.CONSUMPTION_BASED:
        return consumption_based_sharing_timeseries(consumption, generation, tou_prices, fit_prices)
    
    elif method == ValueSharingMethod.MARGINAL_CONTRIBUTION:
        return marginal_contribution_sharing_timeseries(consumption, generation, tou_prices, fit_prices)
    
    elif method == ValueSharingMethod.SHAPLEY_VALUE:
        return shapley_value_sharing_timeseries(
            consumption, generation, tou_prices, fit_prices,
            n_permutations=shapley_permutations,
            random_seed=random_seed
        )
    
    elif method == ValueSharingMethod.COOPERATIVE_GAME:
        return cooperative_game_sharing_timeseries(consumption, generation, tou_prices, fit_prices)
    
    else:
        raise ValueError(f"Unknown value sharing method: {method}")


def compare_value_sharing_methods(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_prices: np.ndarray,
    fit_prices: np.ndarray,
    methods: Optional[list] = None,
    shapley_permutations: int = 100,
    random_seed: Optional[int] = None
) -> Dict:
    """
    Compare multiple value sharing methods side-by-side.
    
    Args:
        consumption: 2D array [n_members x n_timestamps] of consumption data
        generation: 2D array [n_members x n_timestamps] of generation data
        tou_prices: Array [n_timestamps] of Time-of-Use prices
        fit_prices: Array [n_timestamps] of Feed-in Tariff prices
        methods: List of ValueSharingMethod to compare (default: all methods)
        shapley_permutations: Number of permutations for Shapley value
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with results for each method:
            - allocations: gain allocations array
            - summary: method summary statistics
    """
    if methods is None:
        methods = list(ValueSharingMethod)
    
    results = {}
    
    for method in methods:
        allocations, summary = apply_value_sharing(
            consumption, generation, tou_prices, fit_prices,
            method=method,
            shapley_permutations=shapley_permutations,
            random_seed=random_seed
        )
        
        results[method.value] = {
            'allocations': allocations,
            'summary': summary
        }
    
    return results


def export_value_sharing_results(
    allocations: np.ndarray,
    summary: Dict,
    member_ids: Optional[list] = None,
    timestamps: Optional[np.ndarray] = None
) -> Dict:
    """
    Export value sharing results in a structured format.
    
    Args:
        allocations: 2D array [n_members x n_timestamps] of gain allocations
        summary: Summary dictionary from value sharing method
        member_ids: List of member identifiers (default: numeric indices)
        timestamps: Array of timestamp identifiers (default: numeric indices)
    
    Returns:
        Dictionary with structured results ready for export
    """
    n_members, n_timestamps = allocations.shape
    
    if member_ids is None:
        member_ids = [f"Member_{i}" for i in range(n_members)]
    
    if timestamps is None:
        timestamps = list(range(n_timestamps))
    
    # Per-member results
    member_results = {}
    for i, member_id in enumerate(member_ids):
        member_results[member_id] = {
            'allocations_per_timestamp': allocations[i, :].tolist(),
            'total_allocation': float(summary['total_allocations_per_member'][i]),
            'average_allocation': float(np.mean(allocations[i, :]))
        }
    
    # Aggregate results
    return {
        'method': summary['method'],
        'total_community_gain': float(summary['total_community_gain']),
        'avg_gain_per_timestamp': float(summary['avg_gain_per_timestamp']),
        'n_members': n_members,
        'n_timestamps': n_timestamps,
        'member_results': member_results,
        'additional_info': {k: v for k, v in summary.items() 
                           if k not in ['method', 'total_community_gain', 
                                       'avg_gain_per_timestamp', 'total_allocations_per_member']}
    }
