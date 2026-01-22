"""
Value Sharing Utilities
========================
Common utilities and calculations for all Value Sharing models.
"""

import numpy as np
from typing import Dict, List, Tuple


def compute_net_energy(consumption: np.ndarray, generation: np.ndarray) -> np.ndarray:
    """
    Compute net energy for each member.
    
    W_i,h^net = W_i,h^c - W_i,h^g
    
    Args:
        consumption: Array of consumption values for each member [kWh]
        generation: Array of generation values for each member [kWh]
    
    Returns:
        Net energy array (positive = deficit, negative = surplus)
    """
    return consumption - generation


def compute_individual_payment(
    net_energy: float, 
    tou_price: float, 
    fit_price: float
) -> float:
    """
    Compute individual payment without community.
    
    Pay_i,h^0 = max(W_i,h^net, 0) * λ_h^ToU - max(-W_i,h^net, 0) * λ_h^FiT
    
    Args:
        net_energy: Net energy (consumption - generation) [kWh]
        tou_price: Time-of-Use price [€/kWh]
        fit_price: Feed-in tariff [€/kWh]
    
    Returns:
        Individual payment [€]
    """
    if net_energy > 0:
        # Deficit: pay for net consumption
        return net_energy * tou_price
    else:
        # Surplus: receive payment for net generation
        return net_energy * fit_price  # net_energy is negative, fit_price is positive


def compute_community_net_energy(net_energy: np.ndarray) -> float:
    """
    Compute community net energy.
    
    W_EC,h^net = Σ_i W_i,h^net
    
    Args:
        net_energy: Array of net energy for each member
    
    Returns:
        Community net energy
    """
    return np.sum(net_energy)


def compute_community_payment(
    community_net_energy: float, 
    tou_price: float, 
    fit_price: float
) -> float:
    """
    Compute community payment.
    
    Pay_EC,h = max(W_EC,h^net, 0) * λ_h^ToU - max(-W_EC,h^net, 0) * λ_h^FiT
    
    Args:
        community_net_energy: Community net energy [kWh]
        tou_price: Time-of-Use price [€/kWh]
        fit_price: Feed-in tariff [€/kWh]
    
    Returns:
        Community payment [€]
    """
    if community_net_energy > 0:
        return community_net_energy * tou_price
    else:
        return community_net_energy * fit_price


def compute_community_gain(
    individual_payments: np.ndarray, 
    community_payment: float
) -> float:
    """
    Compute community gain.
    
    G_EC,h = Σ_i Pay_i,h^0 - Pay_EC,h
    
    Args:
        individual_payments: Array of individual payments
        community_payment: Community payment
    
    Returns:
        Community gain (cost savings)
    """
    return np.sum(individual_payments) - community_payment


def compute_all_individual_payments(
    net_energy: np.ndarray, 
    tou_price: float, 
    fit_price: float
) -> np.ndarray:
    """
    Compute individual payments for all members.
    
    Args:
        net_energy: Array of net energy for each member
        tou_price: Time-of-Use price
        fit_price: Feed-in tariff
    
    Returns:
        Array of individual payments
    """
    n_members = len(net_energy)
    payments = np.zeros(n_members)
    
    for i in range(n_members):
        payments[i] = compute_individual_payment(net_energy[i], tou_price, fit_price)
    
    return payments


def normalize_allocations(allocations: np.ndarray, target_sum: float) -> np.ndarray:
    """
    Normalize allocations to sum to target value.
    
    Args:
        allocations: Array of allocation values
        target_sum: Target sum value
    
    Returns:
        Normalized allocations
    """
    current_sum = np.sum(allocations)
    
    if current_sum == 0:
        # Equal distribution if all zeros
        return np.ones(len(allocations)) * (target_sum / len(allocations))
    
    return allocations * (target_sum / current_sum)


def compute_timestamp_data(
    consumption: np.ndarray,
    generation: np.ndarray,
    tou_price: float,
    fit_price: float
) -> Dict:
    """
    Compute all derived quantities for a single timestamp.
    
    Args:
        consumption: Array of consumption values
        generation: Array of generation values
        tou_price: Time-of-Use price
        fit_price: Feed-in tariff
    
    Returns:
        Dictionary containing:
            - net_energy: array
            - individual_payments: array
            - community_net_energy: float
            - community_payment: float
            - community_gain: float
    """
    # Net energy for each member
    net_energy = compute_net_energy(consumption, generation)
    
    # Individual payments
    individual_payments = compute_all_individual_payments(net_energy, tou_price, fit_price)
    
    # Community aggregates
    community_net_energy = compute_community_net_energy(net_energy)
    community_payment = compute_community_payment(community_net_energy, tou_price, fit_price)
    community_gain = compute_community_gain(individual_payments, community_payment)
    
    return {
        'net_energy': net_energy,
        'individual_payments': individual_payments,
        'community_net_energy': community_net_energy,
        'community_payment': community_payment,
        'community_gain': community_gain
    }
