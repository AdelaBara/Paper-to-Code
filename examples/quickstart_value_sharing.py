"""
Quick Start Guide - Value Sharing Models
========================================

This is a minimal example to get you started quickly.
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BM_LEM.value_sharing import apply_value_sharing, ValueSharingMethod

# Example: 3 households, 24 hours
# Member 0: Pure consumer (no solar)
# Member 1: Small solar system
# Member 2: Large solar system

consumption = np.array([
    [2.5, 2.0, 1.8, 1.5, 1.2, 1.5, 2.0, 2.5, 2.8, 3.0, 2.8, 2.5, 2.3, 2.5, 2.8, 3.2, 3.5, 3.8, 3.5, 3.0, 2.5, 2.3, 2.0, 2.0],  # Consumer
    [1.5, 1.2, 1.0, 0.8, 0.7, 0.9, 1.2, 1.5, 1.8, 2.0, 1.9, 1.8, 1.7, 1.8, 1.9, 2.1, 2.3, 2.5, 2.3, 2.0, 1.5, 1.3, 1.2, 1.2],  # Small prosumer
    [1.8, 1.5, 1.3, 1.1, 0.9, 1.1, 1.4, 1.7, 2.0, 2.2, 2.1, 2.0, 1.9, 2.0, 2.1, 2.3, 2.6, 2.8, 2.6, 2.2, 1.7, 1.5, 1.4, 1.4],  # Large prosumer
])

generation = np.array([
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.8, 1.2, 1.5, 1.7, 1.8, 1.7, 1.5, 1.2, 0.8, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # No solar
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.2, 1.8, 2.2, 2.5, 2.6, 2.5, 2.2, 1.8, 1.2, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Small solar
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 2.0, 3.0, 3.8, 4.2, 4.4, 4.2, 3.8, 3.0, 2.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Large solar
])

# Electricity prices (€/kWh)
tou_prices = np.array([0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.25, 0.25, 0.25, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.25, 0.30, 0.30, 0.30, 0.25, 0.20, 0.15, 0.15])
fit_prices = np.ones(24) * 0.08  # Fixed feed-in tariff

print("=" * 80)
print("QUICK START: Value Sharing Models")
print("=" * 80)

# Try each method
methods = [
    ("Equal Sharing", ValueSharingMethod.EQUAL),
    ("Generation-based", ValueSharingMethod.GENERATION_BASED),
    ("Consumption-based", ValueSharingMethod.CONSUMPTION_BASED),
    ("Marginal Contribution", ValueSharingMethod.MARGINAL_CONTRIBUTION),
    ("Shapley Value", ValueSharingMethod.SHAPLEY_VALUE),
    ("Cooperative Game", ValueSharingMethod.COOPERATIVE_GAME),
]

print(f"\nCommunity Overview:")
print(f"  Total consumption: {np.sum(consumption):.2f} kWh")
print(f"  Total generation: {np.sum(generation):.2f} kWh")
print()

for name, method in methods:
    allocations, summary = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=method,
        shapley_permutations=50  # Fast computation
    )
    
    print(f"{name}:")
    print(f"  Community gain: €{summary['total_community_gain']:.2f}")
    print(f"  Allocations:")
    for i, alloc in enumerate(summary['total_allocations_per_member']):
        member_type = ["Consumer", "Small Prosumer", "Large Prosumer"][i]
        print(f"    {member_type:20s}: €{alloc:6.2f}")
    print()

print("=" * 80)
print("\nTo use in your code:")
print("""
from BM_LEM.value_sharing import apply_value_sharing, ValueSharingMethod

allocations, summary = apply_value_sharing(
    consumption,      # 2D array [members x timestamps]
    generation,       # 2D array [members x timestamps]
    tou_prices,       # 1D array [timestamps]
    fit_prices,       # 1D array [timestamps]
    method=ValueSharingMethod.EQUAL  # Choose method
)

# Access results
total_gain = summary['total_community_gain']
member_allocations = summary['total_allocations_per_member']
""")
print("=" * 80)
