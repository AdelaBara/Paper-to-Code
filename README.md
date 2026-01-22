## Overview

This multi-agent system automates the process of extracting energy sharing (ES),  value sharing (VS) and Local Electricity Market (LEM) models from scientific papers and generating production-ready simulation code for energy communities.

## Pipeline Architecture

```
Research Paper (PDF) + Dataset Columns
    ↓
[The Architect] → Structured Spec + Dataset-Adapted Pseudocode
    ↓
Human Review & Revision
    ↓
[The Engineer] → Production Python Code
```

## Agents

### 1. The Architect (Extraction & Adaptation Agent)
- **Input**: Research paper (PDF) + Dataset column information
- **Output**: 
  - Structured specification containing:
    - Model description
    - Mathematical formulations
    - Variables and parameters
    - Constraints and assumptions
    - Algorithm steps
  - Pseudocode directly adapted to the dataset columns


### 2. The Engineer (Implementation Agent)
- **Input**: Reviewed pseudocode + Dataset metadata + Spec
- **Output**: Production Python code
- **Features**: Complete, tested, documented implementation

## Dataset Schema
For each member `i` in the energy community:
- `timestamp`: Time period `t`
- `C_i^t`: Load/consumption at time `t`
- `G_i^t`: Generation (e.g., solar PV) at time `t`
### Tariffs
- `ToU^t`: Time-of-Use tariff (grid purchase price)
- `FiT^t`: Feed-in Tariff (grid sale price)
- `P^t`: Internal tariff (optional, for internal trading)

### Parameters
- `n`: Total number of members
