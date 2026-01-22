# [Model Name] - Pseudocode

**Version:** 1.0  
**Adapted from:** [Paper reference]  
**Review Status:** [pending / approved / needs_revision]

## Constants

- `N_MEMBERS` = Total number of energy community members
- `TIME_PERIODS` = Number of time steps in simulation
- `EPSILON` = 1e-6 (small value for numerical stability)

## Global Variables

- `dataset`: DataFrame containing all member data
- `tariffs`: DataFrame containing ToU and FiT values
- `results`: Dictionary to store simulation results

---

## Function: load_data

**Description**: Load and validate the energy community dataset

**Inputs**: 
- `dataset_path`: str - Path to CSV file
- `column_mappings`: dict - Mapping of standard to actual column names

**Outputs**: 
- `data`: DataFrame - Validated and formatted data

```
FUNCTION load_data(dataset_path, column_mappings):
  // Read CSV file
  data ← read_csv(dataset_path)
  
  // Validate required columns exist
  FOR EACH required_col IN ['timestamp', 'member_id', 'consumption', 'generation']:
    IF required_col NOT IN column_mappings:
      RAISE MissingColumnError(required_col)
  
  // Rename columns to standard names
  data ← rename_columns(data, column_mappings)
  
  // Convert timestamp to datetime
  data['timestamp'] ← to_datetime(data['timestamp'])
  
  // Validate data types and ranges
  IF ANY(data['consumption'] < 0):
    RAISE ValueError("Consumption cannot be negative")
  IF ANY(data['generation'] < 0):
    RAISE ValueError("Generation cannot be negative")
  
  // Sort by timestamp and member
  data ← sort(data, by=['timestamp', 'member_id'])
  
  RETURN data
```

---

## Function: compute_net_load

**Description**: Calculate net load for each member (consumption - generation)

**Inputs**: 
- `consumption`: array - Member consumption values
- `generation`: array - Member generation values

**Outputs**: 
- `net_load`: array - Net load (positive = deficit, negative = surplus)

```
FUNCTION compute_net_load(consumption, generation):
  net_load ← consumption - generation
  RETURN net_load
```

---

## Function: apply_energy_sharing

**Description**: Apply the energy sharing mechanism

**Inputs**: 
- `net_loads`: array - Net loads for all members
- `sharing_coefficients`: array - Sharing factors (optional)

**Outputs**: 
- `shared_energy`: dict - Energy exchanges between members

```
FUNCTION apply_energy_sharing(net_loads, sharing_coefficients):
  n_members ← length(net_loads)
  shared_energy ← initialize_dict()
  
  // Separate producers and consumers
  producers ← [i for i WHERE net_loads[i] < 0]
  consumers ← [i for i WHERE net_loads[i] > 0]
  
  // Calculate total surplus and deficit
  total_surplus ← sum(abs(net_loads[i]) for i IN producers)
  total_deficit ← sum(net_loads[i] for i IN consumers)
  
  // Determine shareable energy (minimum of surplus and deficit)
  shareable ← min(total_surplus, total_deficit)
  
  // Allocate shared energy
  FOR EACH consumer IN consumers:
    IF total_deficit > EPSILON:
      // Proportional allocation based on consumption
      share_ratio ← net_loads[consumer] / total_deficit
      shared_energy[consumer] ← shareable * share_ratio
    ELSE:
      shared_energy[consumer] ← 0
  
  RETURN shared_energy
```

---

## Function: calculate_costs

**Description**: Calculate costs for each member with and without sharing

**Inputs**: 
- `net_loads`: array - Net loads for all members
- `shared_energy`: dict - Shared energy allocations
- `tou_tariff`: float - Grid purchase price
- `fit_tariff`: float - Grid feed-in price
- `internal_tariff`: float - Internal trading price (optional)

**Outputs**: 
- `costs`: dict - Costs for each member (baseline and with sharing)

```
FUNCTION calculate_costs(net_loads, shared_energy, tou_tariff, fit_tariff, internal_tariff):
  costs ← initialize_dict()
  n_members ← length(net_loads)
  
  FOR member IN range(n_members):
    // Baseline cost (without sharing)
    IF net_loads[member] > 0:
      // Member is a consumer
      baseline_cost ← net_loads[member] * tou_tariff
    ELSE:
      // Member is a producer (negative cost = revenue)
      baseline_cost ← net_loads[member] * fit_tariff
    
    // Cost with sharing
    remaining_load ← net_loads[member] - shared_energy.get(member, 0)
    
    IF remaining_load > 0:
      // Still purchasing from grid
      grid_cost ← remaining_load * tou_tariff
    ELSE:
      // Feeding to grid
      grid_cost ← remaining_load * fit_tariff
    
    // Internal trading cost
    IF internal_tariff IS NOT NULL:
      internal_cost ← shared_energy.get(member, 0) * internal_tariff
    ELSE:
      internal_cost ← 0
    
    shared_cost ← grid_cost + internal_cost
    
    // Store results
    costs[member] ← {
      'baseline': baseline_cost,
      'with_sharing': shared_cost,
      'savings': baseline_cost - shared_cost
    }
  
  RETURN costs
```

---

## Main Algorithm

```
FUNCTION run_simulation(dataset_path, config):
  // Initialize
  column_mappings ← config['column_mappings']
  output_path ← config['output_path']
  
  // Phase 1: Load and validate data
  data ← load_data(dataset_path, column_mappings)
  
  // Get unique timestamps and members
  timestamps ← unique(data['timestamp'])
  members ← unique(data['member_id'])
  n_members ← length(members)
  n_periods ← length(timestamps)
  
  // Initialize results storage
  all_results ← []
  
  // Phase 2: Simulate for each time period
  FOR EACH t IN timestamps:
    // Get data for this time period
    period_data ← filter(data, timestamp == t)
    
    // Extract consumption and generation
    consumption ← period_data['consumption'].values
    generation ← period_data['generation'].values
    
    // Get tariffs for this period
    tou_t ← get_tariff(period_data, 'tou')
    fit_t ← get_tariff(period_data, 'fit')
    internal_t ← get_tariff(period_data, 'internal', default=NULL)
    
    // Calculate net loads
    net_loads ← compute_net_load(consumption, generation)
    
    // Apply energy sharing
    shared_energy ← apply_energy_sharing(net_loads, sharing_coefficients=NULL)
    
    // Calculate costs
    costs ← calculate_costs(net_loads, shared_energy, tou_t, fit_t, internal_t)
    
    // Store results for this period
    period_results ← {
      'timestamp': t,
      'member_costs': costs,
      'total_shared': sum(shared_energy.values()),
      'total_savings': sum(costs[m]['savings'] for m IN members)
    }
    
    append(all_results, period_results)
  
  // Phase 3: Aggregate results
  summary ← aggregate_results(all_results)
  
  // Phase 4: Export results
  save_results(all_results, summary, output_path)
  
  // Return summary
  RETURN summary
```

---

## Review Comments

[To be filled during human review]

## Revisions

[List of revisions made after review]
