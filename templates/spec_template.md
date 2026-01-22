# Structured Specification Template

## Model Information

**Title:** [Model Name]  
**Type:** [self_consumption / bill_pooling / p2p_trading / etc.]  
**Authors:** [Author names]  
**Year:** [Publication year]  
**DOI:** [DOI if available]

## Objective

[What the model aims to achieve]

## Summary

[High-level description of the approach]

## Variables

### Decision Variables

| Variable | Description | Unit | Type |
|----------|-------------|------|------|
| `var_name` | Description | kWh | continuous |

### Parameters

| Variable | Description | Unit | Type |
|----------|-------------|------|------|
| `C_i^t` | Load of member i at time t | kWh | continuous |
| `G_i^t` | Generation of member i at time t | kWh | continuous |
| `ToU^t` | Time-of-use tariff at time t | €/kWh | continuous |
| `FiT^t` | Feed-in tariff at time t | €/kWh | continuous |

## Mathematical Formulation

### Objective Function

```latex
\min \sum_{t=1}^T \sum_{i=1}^N \text{Cost}_i^t
```

**Description:** Minimize total costs across all members and time periods.

### Constraints

#### Energy Balance

```latex
C_i^t = G_i^t + P_{grid,i}^t - P_{feed,i}^t \quad \forall i,t
```

**Description:** Energy consumed equals generation plus grid purchase minus feed-in.

#### Non-negativity

```latex
P_{grid,i}^t, P_{feed,i}^t \geq 0 \quad \forall i,t
```

## Algorithm

### Main Steps

1. **Load Data**: Read member consumption, generation, and tariffs
2. **Initialize**: Set up decision variables and parameters
3. **For each time period t:**
   - Calculate energy balances
   - Compute costs/benefits
   - Apply sharing mechanism
4. **Aggregate Results**: Sum over time and members
5. **Return**: Final allocations and savings

### Computational Complexity

O(N × T) where N = number of members, T = number of time periods

## Data Requirements

### Required Inputs

- Member consumption: `C_i^t` for all members i and times t
- Member generation: `G_i^t` for all members i and times t
- Grid purchase tariff: `ToU^t` for all times t
- Feed-in tariff: `FiT^t` for all times t

### Optional Inputs

- Internal tariff: `P^t` for internal trading
- Battery capacity: if storage is included
- EV charging profiles: if EVs are included

## Assumptions

1. Perfect forecast of consumption and generation
2. No network constraints or losses
3. Instantaneous energy sharing
4. Price-taker behavior (no market power)

## Limitations

1. Does not account for network congestion
2. Assumes cooperative behavior
3. Requires complete data availability

