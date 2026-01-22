import numpy as np
import pandas as pd
import pymarket as pm
import itertools
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def cooperative_game_theory_shapley(bids_uncovered: pd.DataFrame, trans: pm.TransactionManager, cap: float, floor: float):
    """
    Cooperative Game Theory (CGT) with Shapley values for trading uncovered bids.
    Uses full permutation-based Shapley value calculation.
    Warning: Computationally expensive for large numbers of participants.
    """
    def calculate_welfare(bids):
        return (bids.loc[bids['buying'], 'price'] - bids.loc[~bids['buying'], 'price']).sum()
    
    total_welfare = calculate_welfare(bids_uncovered)
    shapley_values = {}
    participants = list(bids_uncovered.index)
    
    for p in participants:
        marginal_contributions = []
        for perm in itertools.permutations([x for x in participants if x != p]):
            S = list(perm)
            W_S = calculate_welfare(bids_uncovered.loc[S]) if S else 0
            W_S_plus_p = calculate_welfare(bids_uncovered.loc[S + [p]])
            marginal_contributions.append(W_S_plus_p - W_S)
        
        shapley_values[p] = sum(marginal_contributions) / len(marginal_contributions)
    
    for i, row in bids_uncovered.iterrows():
        if row['buying']:
            matching_sellers = bids_uncovered.loc[~bids_uncovered['buying']]
            for j, seller in matching_sellers.iterrows():
                price = max(floor, min((shapley_values[i] + shapley_values[j]) / 2, cap))
                quantity = min(row['quantity'], seller['quantity'])
                trans.add_transaction(i, quantity, price, -1, False)
                trans.add_transaction(j, quantity, price, -1, False)
                bids_uncovered.at[i, 'quantity'] -= quantity
                bids_uncovered.at[j, 'quantity'] -= quantity
                if bids_uncovered.at[i, 'quantity'] == 0:
                    break
    
    return bids_uncovered, sum(shapley_values.values()) / len(shapley_values)


def two_steps_CGT_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Cooperative Game Theory (CGT) mechanism with Shapley values.
    Step 1: Run UP mechanism
    Step 2: Run CGT with Shapley values for uncovered bids
    """
    FIT = kwargs.pop('FIT', 0.1)
    TOU = kwargs.pop('TOU', 0.25)
    cap = kwargs.pop('cap', 100)
    floor = kwargs.pop('floor', 10)
    
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
    
    # Step 2: CGT
    CGTq_ = 0
    CGTprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0:
        bidsM, CGTprice = cooperative_game_theory_shapley(bids_uncovered, trans, cap, floor)
        CGTq_ = bidsM.quantity.sum()
    
    if CGTq_ is None:
        CGTq_ = 0
    if CGTprice is None:
        CGTprice = UPprice
    if UPq_ is None:
        UPq_ = 0
    
    extra = {
        'clearing quantity UP': UPq_,
        'clearing price': UPprice,
        'CGT quantity': CGTq_,
        'CGT price': CGTprice,
        'Total quantity': UPq_ + CGTq_
    }
    
    return trans, extra


class CGT(pm.Mechanism):
    """
    Interface for Cooperative Game Theory mechanism with Shapley values.

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
    
    Note: This mechanism uses full permutation-based Shapley value calculation
    which is computationally expensive for large numbers of participants.
    Consider using CGTS (simplified version) for better performance.
    """

    def __init__(self, bids, *args, **kwargs):
        FIT = kwargs.get('FIT', 0.1)
        TOU = kwargs.get('TOU', 0.25)
        cap = kwargs.get('cap', 100)
        floor = kwargs.get('floor', 10)
        pm.Mechanism.__init__(self, two_steps_CGT_mechanism, bids, FIT=FIT, TOU=TOU, cap=cap, floor=floor, *args, **kwargs)
