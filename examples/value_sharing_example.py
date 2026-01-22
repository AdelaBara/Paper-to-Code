"""
Example Usage of Value Sharing Models
======================================

This example demonstrates how to use the value sharing models with sample data.
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BM_LEM.value_sharing import (
    apply_value_sharing,
    compare_value_sharing_methods,
    export_value_sharing_results,
    ValueSharingMethod
)


def create_sample_data(n_members=5, n_timestamps=24):
    """
    Create sample energy community data for demonstration.
    
    Args:
        n_members: Number of community members
        n_timestamps: Number of time periods (e.g., hours)
    
    Returns:
        Tuple of (consumption, generation, tou_prices, fit_prices)
    """
    np.random.seed(42)
    
    # Consumption patterns (kWh)
    # Higher during day hours, lower at night
    base_consumption = np.random.uniform(0.5, 2.0, (n_members, n_timestamps))
    day_hours = (np.arange(n_timestamps) >= 6) & (np.arange(n_timestamps) <= 22)
    base_consumption[:, day_hours] *= 1.5
    
    # Generation patterns (kWh)
    # Solar generation: zero at night, peak around midday
    generation = np.zeros((n_members, n_timestamps))
    for h in range(n_timestamps):
        if 6 <= h <= 18:  # Daylight hours
            # Bell curve peaking at hour 12
            solar_factor = np.exp(-((h - 12) ** 2) / 20)
            generation[:, h] = np.random.uniform(0, 3.0, n_members) * solar_factor
    
    # Not all members have generation
    generation[0:2, :] = 0  # First 2 members are pure consumers
    
    # Time-of-Use prices (€/kWh)
    tou_prices = np.ones(n_timestamps) * 0.20  # Base price
    peak_hours = ((np.arange(n_timestamps) >= 7) & (np.arange(n_timestamps) <= 10)) | \
                 ((np.arange(n_timestamps) >= 17) & (np.arange(n_timestamps) <= 20))
    tou_prices[peak_hours] = 0.30  # Peak price
    tou_prices[~day_hours] = 0.15  # Off-peak price
    
    # Feed-in Tariff (€/kWh)
    fit_prices = np.ones(n_timestamps) * 0.10  # Constant FiT
    
    return base_consumption, generation, tou_prices, fit_prices


def example_single_method():
    """Example: Apply a single value sharing method."""
    print("=" * 70)
    print("EXAMPLE 1: Single Value Sharing Method")
    print("=" * 70)
    
    # Create sample data
    consumption, generation, tou_prices, fit_prices = create_sample_data(
        n_members=5, n_timestamps=24
    )
    
    print(f"\nData shape: {consumption.shape[0]} members, {consumption.shape[1]} timestamps")
    print(f"Total consumption: {np.sum(consumption):.2f} kWh")
    print(f"Total generation: {np.sum(generation):.2f} kWh")
    
    # Apply Equal Sharing method
    allocations, summary = apply_value_sharing(
        consumption=consumption,
        generation=generation,
        tou_prices=tou_prices,
        fit_prices=fit_prices,
        method=ValueSharingMethod.EQUAL
    )
    
    print(f"\nMethod: {summary['method']}")
    print(f"Total community gain: €{summary['total_community_gain']:.2f}")
    print(f"Average gain per timestamp: €{summary['avg_gain_per_timestamp']:.4f}")
    
    print("\nAllocation per member:")
    for i, total_alloc in enumerate(summary['total_allocations_per_member']):
        print(f"  Member {i}: €{total_alloc:.2f}")
    
    return allocations, summary


def example_compare_methods():
    """Example: Compare all value sharing methods."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Compare All Value Sharing Methods")
    print("=" * 70)
    
    # Create sample data
    consumption, generation, tou_prices, fit_prices = create_sample_data(
        n_members=5, n_timestamps=24
    )
    
    # Compare all methods
    results = compare_value_sharing_methods(
        consumption=consumption,
        generation=generation,
        tou_prices=tou_prices,
        fit_prices=fit_prices,
        shapley_permutations=50,  # Reduced for faster computation
        random_seed=42
    )
    
    print("\nComparison of all methods:")
    print("-" * 70)
    
    # Display summary for each method
    for method_name, method_results in results.items():
        summary = method_results['summary']
        print(f"\n{summary['method']}:")
        print(f"  Total gain: €{summary['total_community_gain']:.2f}")
        print(f"  Allocations: {summary['total_allocations_per_member']}")
        
        # Calculate variance in allocations (measure of fairness)
        variance = np.var(summary['total_allocations_per_member'])
        print(f"  Variance: {variance:.4f}")
    
    return results


def example_specific_methods():
    """Example: Use specific methods with different parameters."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Specific Methods with Parameters")
    print("=" * 70)
    
    # Create sample data
    consumption, generation, tou_prices, fit_prices = create_sample_data(
        n_members=10, n_timestamps=48  # 2 days, hourly data
    )
    
    print(f"\nData: {consumption.shape[0]} members, {consumption.shape[1]} timestamps")
    
    # 1. Generation-based sharing
    print("\n1. Generation-based Sharing:")
    alloc_gen, summary_gen = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=ValueSharingMethod.GENERATION_BASED
    )
    print(f"   Total gain: €{summary_gen['total_community_gain']:.2f}")
    print(f"   Equal sharing fallbacks: {summary_gen.get('equal_sharing_fallback_count', 0)}")
    
    # 2. Shapley value with different permutations
    print("\n2. Shapley Value (100 permutations):")
    alloc_shap, summary_shap = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=ValueSharingMethod.SHAPLEY_VALUE,
        shapley_permutations=100,
        random_seed=42
    )
    print(f"   Total gain: €{summary_shap['total_community_gain']:.2f}")
    print(f"   Permutations used: {summary_shap['n_permutations']}")
    
    # 3. Cooperative Game
    print("\n3. Cooperative Game:")
    alloc_cg, summary_cg = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=ValueSharingMethod.COOPERATIVE_GAME
    )
    print(f"   Total gain: €{summary_cg['total_community_gain']:.2f}")
    print(f"   Avg deficit members: {summary_cg['avg_deficit_members']:.1f}")
    print(f"   Avg surplus members: {summary_cg['avg_surplus_members']:.1f}")


def example_export_results():
    """Example: Export results in structured format."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Export Structured Results")
    print("=" * 70)
    
    # Create sample data
    consumption, generation, tou_prices, fit_prices = create_sample_data(
        n_members=3, n_timestamps=24
    )
    
    # Apply a method
    allocations, summary = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=ValueSharingMethod.MARGINAL_CONTRIBUTION
    )
    
    # Export with custom member IDs
    member_ids = ["House_A", "House_B", "House_C"]
    timestamps = [f"{h:02d}:00" for h in range(24)]
    
    export_data = export_value_sharing_results(
        allocations=allocations,
        summary=summary,
        member_ids=member_ids,
        timestamps=timestamps
    )
    
    print(f"\nMethod: {export_data['method']}")
    print(f"Total community gain: €{export_data['total_community_gain']:.2f}")
    print(f"Number of members: {export_data['n_members']}")
    print(f"Number of timestamps: {export_data['n_timestamps']}")
    
    print("\nPer-member results:")
    for member_id, member_data in export_data['member_results'].items():
        print(f"  {member_id}:")
        print(f"    Total allocation: €{member_data['total_allocation']:.2f}")
        print(f"    Average allocation: €{member_data['average_allocation']:.4f}")
    
    # This export_data can be easily converted to JSON or CSV
    import json
    print("\n(Results can be exported to JSON)")
    # Uncomment to save:
    # with open('value_sharing_results.json', 'w') as f:
    #     json.dump(export_data, f, indent=2)


if __name__ == "__main__":
    # Run all examples
    example_single_method()
    example_compare_methods()
    example_specific_methods()
    example_export_results()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
