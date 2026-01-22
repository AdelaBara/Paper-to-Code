# Value Sharing Models - Integration Guide

## ✅ Implementation Complete

All value sharing models have been successfully implemented, tested, and are ready to use.

### Core Modules (in BM_LEM/)
1. **value_sharing_utils.py** - Common calculations
2. **vs_equal_sharing.py** - Algorithm 1: Equal Sharing (EQ)
3. **vs_generation_based.py** - Algorithm 2: Generation-based
4. **vs_consumption_based.py** - Algorithm 3: Consumption-based
5. **vs_marginal_contribution.py** - Algorithm 4: Marginal Contribution
6. **vs_shapley_value.py** - Algorithm 5: Shapley Value
7. **vs_cooperative_game.py** - Algorithm 6: Cooperative Game
8. **value_sharing.py** - Main interface

### Documentation & Examples
- VALUE_SHARING_SUMMARY.md - Implementation summary
- examples/test_value_sharing.py - Test suite ✅ All pass
- examples/value_sharing_example.py - Usage examples
- examples/quickstart_value_sharing.py - Quick start

## 🚀 Quick Start

```python
from BM_LEM.value_sharing import apply_value_sharing, ValueSharingMethod
import numpy as np

# Your data [members x timestamps]
consumption = np.array([[...]])
generation = np.array([[...]])
tou_prices = np.array([...])  # per timestamp
fit_prices = np.array([...])  # per timestamp

# Apply method
allocations, summary = apply_value_sharing(
    consumption, generation, tou_prices, fit_prices,
    method=ValueSharingMethod.EQUAL
)
```

## 📊 Example Results

3 members, 24h → Community gain: €0.78

| Method | Consumer | Small PV | Large PV |
|--------|----------|----------|----------|
| Equal | €0.26 | €0.26 | €0.26 |
| Gen-based | €0.16 | €0.23 | €0.39 |
| Cons-based | €0.32 | €0.22 | €0.24 |
| Marg. Contrib | €0.50 | €0.00 | €0.29 |
| Shapley | €0.43 | €0.07 | €0.29 |
| Coop. Game | €0.01 | €0.29 | €0.49 |

## 📝 How to Run Examples

```bash
# Run tests
python examples/test_value_sharing.py

# Run examples  
python examples/value_sharing_example.py

# Quick start
python examples/quickstart_value_sharing.py
```


