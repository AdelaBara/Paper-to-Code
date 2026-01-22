"""
Basic Tests for Value Sharing Models
====================================

Run these tests to verify the implementation is working correctly.
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BM_LEM.value_sharing import apply_value_sharing, ValueSharingMethod


def test_basic_functionality():
    """Test basic functionality with simple data."""
    print("Testing basic functionality...")
    
    # Simple 2-member, 2-timestamp case
    consumption = np.array([[1.0, 2.0], [2.0, 1.0]])
    generation = np.array([[0.5, 0.5], [0.0, 0.0]])
    tou_prices = np.array([0.25, 0.25])
    fit_prices = np.array([0.10, 0.10])
    
    # Test each method
    methods = [
        ValueSharingMethod.EQUAL,
        ValueSharingMethod.GENERATION_BASED,
        ValueSharingMethod.CONSUMPTION_BASED,
        ValueSharingMethod.MARGINAL_CONTRIBUTION,
        ValueSharingMethod.SHAPLEY_VALUE,
        ValueSharingMethod.COOPERATIVE_GAME
    ]
    
    for method in methods:
        try:
            allocations, summary = apply_value_sharing(
                consumption, generation, tou_prices, fit_prices,
                method=method,
                shapley_permutations=10  # Small number for speed
            )
            
            # Verify allocations sum equals community gain
            total_allocated = np.sum(allocations)
            community_gain = summary['total_community_gain']
            
            if abs(total_allocated - community_gain) < 1e-6:
                print(f"  ✓ {method.value}: PASS")
            else:
                print(f"  ✗ {method.value}: FAIL - Allocation mismatch")
                print(f"    Total allocated: {total_allocated}")
                print(f"    Community gain: {community_gain}")
        except Exception as e:
            print(f"  ✗ {method.value}: ERROR - {str(e)}")
    
    print()


def test_edge_cases():
    """Test edge cases."""
    print("Testing edge cases...")
    
    # Case 1: No generation
    consumption = np.array([[1.0, 2.0], [2.0, 1.0]])
    generation = np.array([[0.0, 0.0], [0.0, 0.0]])
    tou_prices = np.array([0.25, 0.25])
    fit_prices = np.array([0.10, 0.10])
    
    try:
        allocations, summary = apply_value_sharing(
            consumption, generation, tou_prices, fit_prices,
            method=ValueSharingMethod.GENERATION_BASED
        )
        print("  ✓ No generation: PASS")
    except Exception as e:
        print(f"  ✗ No generation: FAIL - {str(e)}")
    
    # Case 2: No consumption
    consumption = np.array([[0.0, 0.0], [0.0, 0.0]])
    generation = np.array([[1.0, 2.0], [2.0, 1.0]])
    
    try:
        allocations, summary = apply_value_sharing(
            consumption, generation, tou_prices, fit_prices,
            method=ValueSharingMethod.CONSUMPTION_BASED
        )
        print("  ✓ No consumption: PASS")
    except Exception as e:
        print(f"  ✗ No consumption: FAIL - {str(e)}")
    
    # Case 3: Single member
    consumption = np.array([[1.0, 2.0]])
    generation = np.array([[0.5, 0.5]])
    
    try:
        allocations, summary = apply_value_sharing(
            consumption, generation, tou_prices, fit_prices,
            method=ValueSharingMethod.EQUAL
        )
        print("  ✓ Single member: PASS")
    except Exception as e:
        print(f"  ✗ Single member: FAIL - {str(e)}")
    
    print()


def test_allocation_properties():
    """Test mathematical properties of allocations."""
    print("Testing allocation properties...")
    
    np.random.seed(42)
    n_members = 5
    n_timestamps = 10
    
    consumption = np.random.uniform(1, 3, (n_members, n_timestamps))
    generation = np.random.uniform(0, 2, (n_members, n_timestamps))
    tou_prices = np.random.uniform(0.20, 0.30, n_timestamps)
    fit_prices = np.random.uniform(0.08, 0.12, n_timestamps)
    
    methods = [
        ValueSharingMethod.EQUAL,
        ValueSharingMethod.GENERATION_BASED,
        ValueSharingMethod.CONSUMPTION_BASED,
        ValueSharingMethod.MARGINAL_CONTRIBUTION,
        ValueSharingMethod.COOPERATIVE_GAME
    ]
    
    for method in methods:
        allocations, summary = apply_value_sharing(
            consumption, generation, tou_prices, fit_prices,
            method=method
        )
        
        # Property 1: Sum of allocations equals community gain
        total_allocated = np.sum(allocations)
        community_gain = summary['total_community_gain']
        
        if abs(total_allocated - community_gain) < 1e-6:
            print(f"  ✓ {method.value}: Budget balance OK")
        else:
            print(f"  ✗ {method.value}: Budget balance FAIL")
            print(f"    Difference: {abs(total_allocated - community_gain)}")
    
    print()


def test_equal_sharing_property():
    """Test that Equal Sharing gives equal allocations."""
    print("Testing Equal Sharing property...")
    
    consumption = np.array([[1.0, 2.0], [2.0, 1.0], [1.5, 1.5]])
    generation = np.array([[0.5, 0.5], [0.0, 0.0], [1.0, 0.5]])
    tou_prices = np.array([0.25, 0.25])
    fit_prices = np.array([0.10, 0.10])
    
    allocations, summary = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=ValueSharingMethod.EQUAL
    )
    
    # Check if all members get equal total allocation
    member_totals = summary['total_allocations_per_member']
    
    if np.allclose(member_totals, member_totals[0]):
        print("  ✓ Equal allocations: PASS")
    else:
        print("  ✗ Equal allocations: FAIL")
        print(f"    Member totals: {member_totals}")
    
    print()


def test_reproducibility():
    """Test that Shapley value is reproducible with same seed."""
    print("Testing Shapley reproducibility...")
    
    consumption = np.array([[1.0, 2.0], [2.0, 1.0]])
    generation = np.array([[0.5, 0.5], [0.0, 0.0]])
    tou_prices = np.array([0.25, 0.25])
    fit_prices = np.array([0.10, 0.10])
    
    # Run twice with same seed
    alloc1, _ = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=ValueSharingMethod.SHAPLEY_VALUE,
        shapley_permutations=50,
        random_seed=42
    )
    
    alloc2, _ = apply_value_sharing(
        consumption, generation, tou_prices, fit_prices,
        method=ValueSharingMethod.SHAPLEY_VALUE,
        shapley_permutations=50,
        random_seed=42
    )
    
    if np.allclose(alloc1, alloc2):
        print("  ✓ Shapley reproducibility: PASS")
    else:
        print("  ✗ Shapley reproducibility: FAIL")
        print(f"    Max difference: {np.max(np.abs(alloc1 - alloc2))}")
    
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("Running Value Sharing Model Tests")
    print("=" * 70)
    print()
    
    test_basic_functionality()
    test_edge_cases()
    test_allocation_properties()
    test_equal_sharing_property()
    test_reproducibility()
    
    print("=" * 70)
    print("All tests completed!")
    print("=" * 70)
