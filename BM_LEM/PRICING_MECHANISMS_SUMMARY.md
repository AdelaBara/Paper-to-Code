# Pricing Mechanisms Summary

This document provides an overview of some of the pricing mechanisms that have been extracted into separate files in the `BM_LEM` folder.

## Extracted Mechanisms

All mechanisms follow a two-step approach:
1. **Step 1**: Run the Uniform Price (UP) mechanism
2. **Step 2**: Apply a specific pricing adjustment or matching algorithm for uncovered bids

### 1. MUP - Uniform Price with Mediation (`pricing_MUP.py`)
- **File**: `BM_LEM/pricing_MUP.py`
- **Class**: `MUP`
- **Description**: Applies peer-to-peer mediation for uncovered bids after UP mechanism
- **Parameters**: `FIT`, `TOU`
- **Second-step logic**: Matches buyers and sellers bilaterally using average of their bid prices

### 2. UPNR - Uniform Price with Newton-Raphson (`pricing_UPNR.py`)
- **File**: `BM_LEM/pricing_UPNR.py`
- **Class**: `UPNR`
- **Description**: Uses Newton-Raphson optimization for price discovery
- **Parameters**: `FIT`, `TOU`
- **Second-step logic**: Iteratively adjusts price using Newton-Raphson method to find equilibrium

### 3. APM - Average Price Method (`pricing_APM.py`)
- **File**: `BM_LEM/pricing_APM.py`
- **Class**: `APM`
- **Description**: Trades uncovered bids at average of buyer and seller prices
- **Parameters**: `FIT`, `TOU`
- **Second-step logic**: Simple averaging of bid prices

### 4. MPAS - Marginal Price Adjusted by Spread (`pricing_MPAS.py`)
- **File**: `BM_LEM/pricing_MPAS.py`
- **Class**: `MPAS`
- **Description**: Adjusts price based on bid-ask spread
- **Parameters**: `FIT`, `TOU`, `alpha` (spread adjustment factor, default: 0.5)
- **Second-step logic**: Price = (max_buy + min_sell) / 2 + alpha * spread

### 5. CFRM - Cap and Floor Range Midpoint (`pricing_CFRM.py`)
- **File**: `BM_LEM/pricing_CFRM.py`
- **Class**: `CFRM`
- **Description**: Uses midpoint between average buying and selling prices
- **Parameters**: `FIT`, `TOU`
- **Second-step logic**: Midpoint of mean buyer and seller prices

### 6. WAM - Weighted Average Method (`pricing_WAM.py`)
- **File**: `BM_LEM/pricing_WAM.py`
- **Class**: `WAM`
- **Description**: Uses quantity-weighted average prices
- **Parameters**: `FIT`, `TOU`
- **Second-step logic**: Weighted average by quantity

### 7. MMP - Modified Marginal Price (`pricing_MMP.py`)
- **File**: `BM_LEM/pricing_MMP.py`
- **Class**: `MMP`
- **Description**: Uses midpoint between max buy and min sell prices
- **Parameters**: `FIT`, `TOU`
- **Second-step logic**: (max_buy_price + min_sell_price) / 2

### 8. IPA - Iterative Price Adjustment (`pricing_IPA.py`)
- **File**: `BM_LEM/pricing_IPA.py`
- **Class**: `IPA`
- **Description**: Iteratively adjusts price until convergence
- **Parameters**: `FIT`, `TOU`, `theta` (step size, default: 0.1), `epsilon` (tolerance, default: 0.01)
- **Second-step logic**: Iterative adjustment with convergence criteria

### 9. VCG - Vickrey-Clarke-Groves (`pricing_VCG.py`)
- **File**: `BM_LEM/pricing_VCG.py`
- **Class**: `VCG`
- **Description**: Welfare-based mechanism with individual buyer/seller prices
- **Parameters**: `FIT`, `TOU`, `cap` (default: 100), `floor` (default: 10)
- **Second-step logic**: Uses welfare calculations to determine individual prices

### 10. NBS - Nash Bargaining Solution (`pricing_NBS.py`)
- **File**: `BM_LEM/pricing_NBS.py`
- **Class**: `NBS`
- **Description**: Combines iterative price adjustment with bilateral matching
- **Parameters**: `FIT`, `TOU`, `cap`, `floor`, `theta`, `epsilon`
- **Second-step logic**: Nash bargaining approach with price iteration

### 11. CGT - Cooperative Game Theory with Shapley Values (`pricing_CGT.py`)
- **File**: `BM_LEM/pricing_CGT.py`
- **Class**: `CGT`
- **Description**: Uses full permutation-based Shapley values (computationally expensive)
- **Parameters**: `FIT`, `TOU`, `cap`, `floor`
- **Second-step logic**: Computes exact Shapley values using all permutations
- **Warning**: Computationally expensive for large numbers of participants

### 12. CGTS - CGT Simplified with Monte Carlo (`pricing_CGTS.py`)
- **File**: `BM_LEM/pricing_CGTS.py`
- **Class**: `CGTS`
- **Description**: Efficient Monte Carlo approximation of Shapley values
- **Parameters**: `FIT`, `TOU`, `cap`, `floor`, `num_samples` (default: 100)
- **Second-step logic**: Monte Carlo sampling for Shapley value approximation
- **Note**: More efficient than CGT for large participant sets

### 13. COLM - Constrained Optimization with Lagrange Multipliers (`pricing_COLM.py`)
- **File**: `BM_LEM/pricing_COLM.py`
- **Class**: `COLM`
- **Description**: Optimization framework with Monte Carlo Shapley values
- **Parameters**: `FIT`, `TOU`, `cap`, `floor`, `num_samples` (default: 100)
- **Second-step logic**: Uses scipy.optimize with constraint handling


## Usage Example

```python
import pandas as pd
from BM_LEM.pricing_MUP import MUP
from BM_LEM.pricing_UPNR import UPNR
from BM_LEM.pricing_APM import APM
# ... etc

# Create your bids DataFrame
bids = pd.DataFrame({
    'price': [0.15, 0.20, 0.12, 0.18],
    'quantity': [10, 15, 8, 12],
    'buying': [True, True, False, False]
})

# Use any mechanism
mechanism = MUP(bids, FIT=0.1, TOU=0.25)
transactions, results = mechanism.transactions, mechanism.extra

# Or use UPNR
mechanism = UPNR(bids, FIT=0.1, TOU=0.25)

# Or APM
mechanism = APM(bids, FIT=0.1, TOU=0.25)
```


