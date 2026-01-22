import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def nash_bargaining_solution(bids_uncovered: pd.DataFrame, trans: pm.TransactionManager, cap: float, floor: float, theta: float, epsilon: float, MP: float):
    """
    Nash Bargaining Solution (NBS) for trading uncovered bids.
    Combines iterative price adjustment with bilateral matching.
    """
    adjusted_price = MP
    
    while True:
        new_price = adjusted_price + theta * ((bids_uncovered['price'].max() - adjusted_price) + (adjusted_price - bids_uncovered['price'].min())) / 2
        new_price = max(floor, min(new_price, cap))
        
        if abs(new_price - adjusted_price) < epsilon:
            break
        
        adjusted_price = new_price
    
    for i, row in bids_uncovered.iterrows():
        if row['buying']:
            matching_sellers = bids_uncovered.loc[~bids_uncovered['buying']]
            for j, seller in matching_sellers.iterrows():
                quantity = min(row['quantity'], seller['quantity'])
                trans.add_transaction(i, quantity, adjusted_price, -1, False)
                trans.add_transaction(j, quantity, adjusted_price, -1, False)
                bids_uncovered.at[i, 'quantity'] -= quantity
                bids_uncovered.at[j, 'quantity'] -= quantity
                if bids_uncovered.at[i, 'quantity'] == 0:
                    break
    
    return bids_uncovered, adjusted_price


def two_steps_NBS_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Nash Bargaining Solution (NBS) mechanism.
    Step 1: Run UP mechanism
    Step 2: Run NBS for uncovered bids
    """
    FIT = kwargs.pop('FIT', 0.1)
    TOU = kwargs.pop('TOU', 0.25)
    cap = kwargs.pop('cap', 100)
    floor = kwargs.pop('floor', 10)
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
    
    # Step 2: NBS
    NBSq_ = 0
    NBSprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0:
        bidsM, NBSprice = nash_bargaining_solution(bids_uncovered, trans, cap, floor, theta, epsilon, UPprice)
        NBSq_ = bidsM.quantity.sum()
    
    if NBSq_ is None:
        NBSq_ = 0
    if NBSprice is None:
        NBSprice = UPprice
    if UPq_ is None:
        UPq_ = 0
    
    extra = {
        'clearing quantity UP': UPq_,
        'clearing price': UPprice,
        'NBS quantity': NBSq_,
        'NBS price': NBSprice,
        'Total quantity': UPq_ + NBSq_
    }
    
    return trans, extra


class NBS(pm.Mechanism):
    """
    Interface for Nash Bargaining Solution mechanism.

    Parameters
    -----------
    bids
        Collection of bids to run the mechanism with.
    FIT
        Feed-in Tariff (minimum price).
    TOU
        Time-of-Use (maximum price).
    cap
        Maximum price cap (default: 100).
    floor
        Minimum price floor (default: 10).
    theta
        Adjustment step size (default: 0.1).
    epsilon
        Convergence tolerance (default: 0.01).
    """

    def __init__(self, bids, *args, **kwargs):
        FIT = kwargs.get('FIT', 0.1)
        TOU = kwargs.get('TOU', 0.25)
        cap = kwargs.get('cap', 100)
        floor = kwargs.get('floor', 10)
        theta = kwargs.get('theta', 0.1)
        epsilon = kwargs.get('epsilon', 0.01)
        pm.Mechanism.__init__(self, two_steps_NBS_mechanism, bids, FIT=FIT, TOU=TOU, cap=cap, floor=floor, theta=theta, epsilon=epsilon, *args, **kwargs)
