import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def iterative_price_adjustment(bids_uncovered: pd.DataFrame, trans: pm.TransactionManager, theta: float, epsilon: float, MP: float, FIT: float, TOU: float):
    """
    Iterative Price Adjustment (IPA) for trading uncovered bids.
    Iteratively adjusts price until convergence.
    """
    adjusted_price = MP
    
    while True:
        new_price = adjusted_price + theta * ((bids_uncovered['price'].max() - adjusted_price) + (adjusted_price - bids_uncovered['price'].min())) / 2
        new_price = max(FIT, min(new_price, TOU))
        
        if abs(new_price - adjusted_price) < epsilon:
            break
        
        adjusted_price = new_price
    
    buying_bids = bids_uncovered.loc[bids_uncovered['buying']].sort_values('price', ascending=False)
    selling_bids = bids_uncovered.loc[~bids_uncovered['buying']].sort_values('price', ascending=True)
    
    buying_quantity = buying_bids.quantity.sum()
    selling_quantity = selling_bids.quantity.sum()
    
    if buying_quantity > selling_quantity:
        long_side, short_side = buying_bids, selling_bids
    else:
        long_side, short_side = selling_bids, buying_bids
    
    traded_quantity = short_side.quantity.sum()
    
    for i, x in short_side.iterrows():
        if traded_quantity <= 0:
            break
        trade_qty = min(x.quantity, traded_quantity)
        trans.add_transaction(i, trade_qty, adjusted_price, -1, False)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] -= trade_qty
        traded_quantity -= trade_qty
    
    quantity_added = 0
    for i, x in long_side.iterrows():
        if traded_quantity <= 0:
            break
        x_quantity = min(x.quantity, traded_quantity - quantity_added)
        trans.add_transaction(i, x_quantity, adjusted_price, -1, False)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] -= x_quantity
        quantity_added += x_quantity
    
    return bids_uncovered, adjusted_price


def two_steps_IPA_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Iterative Price Adjustment (IPA) mechanism.
    Step 1: Run UP mechanism
    Step 2: Run IPA for uncovered bids
    """
    FIT = kwargs.pop('FIT', 0.1)
    TOU = kwargs.pop('TOU', 0.25)
    theta = kwargs.pop('theta', 0.1)
    epsilon = kwargs.pop('epsilon', 0.01)
    
    trans = pm.TransactionManager()
    bidsUP = bids.copy()
    
    # Step 1: UP mechanism
    trans_UP, result_UP = uniform_price_mechanism(bids)
    UPprice = result_UP['clearing price']
    UPq_ = result_UP['clearing quantity']
    
    # Merge UP transactions
    for _, row in trans_UP.get_df().iterrows():
        trans.add_transaction(row['bid'], row['quantity'], row['price'], row['source'], row['active'])
    
    # Update remaining quantities
    for _, row in trans_UP.get_df().iterrows():
        bid_index = row['bid']
        quantity = row['quantity']
        if bid_index in bidsUP.index:
            bidsUP.loc[bid_index, 'quantity'] -= quantity
    
    unsold_quantity = bidsUP.loc[~bidsUP['buying'], 'quantity'].sum()
    demanded_quantity = bidsUP.loc[bidsUP['buying'], 'quantity'].sum()
    bids_uncovered = bidsUP.loc[bidsUP['quantity'] > 0, :]
    
    # Step 2: IPA
    IPAq_ = 0
    IPAprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0:
        bidsM, IPAprice = iterative_price_adjustment(bids_uncovered, trans, theta, epsilon, UPprice, FIT, TOU)
        IPAq_ = bidsM.quantity.sum()
    
    if IPAq_ is None:
        IPAq_ = 0
    if IPAprice is None:
        IPAprice = UPprice
    if UPq_ is None:
        UPq_ = 0
    
    extra = {
        'clearing quantity UP': UPq_,
        'clearing price': UPprice,
        'IPA quantity': IPAq_,
        'IPA price': IPAprice,
        'Total quantity': UPq_ + IPAq_
    }
    
    return trans, extra


class IPA(pm.Mechanism):
    """
    Interface for Iterative Price Adjustment mechanism.

    Parameters
    -----------
    bids
        Collection of bids to run the mechanism with.
    FIT
        Feed-in Tariff (minimum price).
    TOU
        Time-of-Use (maximum price).
    theta
        Adjustment step size (default: 0.1).
    epsilon
        Convergence tolerance (default: 0.01).
    """

    def __init__(self, bids, *args, **kwargs):
        FIT = kwargs.get('FIT', 0.1)
        TOU = kwargs.get('TOU', 0.25)
        theta = kwargs.get('theta', 0.1)
        epsilon = kwargs.get('epsilon', 0.01)
        pm.Mechanism.__init__(self, two_steps_IPA_mechanism, bids, FIT=FIT, TOU=TOU, theta=theta, epsilon=epsilon, *args, **kwargs)
