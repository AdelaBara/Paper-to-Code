import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def vickrey_clarke_groves(bids_uncovered: pd.DataFrame, trans: pm.TransactionManager, cap: float, floor: float, MP: float):
    """
    Vickrey-Clarke-Groves (VCG) mechanism for trading uncovered bids.
    Uses welfare-based pricing with individual prices for buyers and sellers.
    """
    def calculate_welfare(bids):
        return (bids.loc[bids['buying'], 'price'] - bids.loc[~bids['buying'], 'price']).sum()
    
    total_welfare = calculate_welfare(bids_uncovered)
    VCG_price = MP
    
    for i, row in bids_uncovered.iterrows():
        if row['buying']:
            welfare_without_i = calculate_welfare(bids_uncovered.drop(i))
            MC = row['price']
            P_Bi = MP - (welfare_without_i - total_welfare - MC)
            P_Bi = max(floor, min(P_Bi, cap))
            
            matching_sellers = bids_uncovered.loc[~bids_uncovered['buying']]
            for j, seller in matching_sellers.iterrows():
                welfare_without_j = calculate_welfare(bids_uncovered.drop(j))
                MU = seller['price']
                P_Sj = MP - (welfare_without_j - total_welfare - MU)
                P_Sj = max(floor, min(P_Sj, cap))
                
                quantity = min(row['quantity'], seller['quantity'])
                trans.add_transaction(i, quantity, P_Bi, -1, False)
                trans.add_transaction(j, quantity, P_Sj, -1, False)
                bids_uncovered.at[i, 'quantity'] -= quantity
                bids_uncovered.at[j, 'quantity'] -= quantity
                VCG_price = (P_Bi + P_Sj) / 2
                if bids_uncovered.at[i, 'quantity'] == 0:
                    break
    
    return bids_uncovered, VCG_price


def two_steps_VCG_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Vickrey-Clarke-Groves (VCG) mechanism.
    Step 1: Run UP mechanism
    Step 2: Run VCG for uncovered bids
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
    
    # Step 2: VCG
    VCGq_ = 0
    VCGprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0:
        bidsM, VCGprice = vickrey_clarke_groves(bids_uncovered, trans, cap, floor, UPprice)
        VCGq_ = bidsM.quantity.sum()
    
    if VCGq_ is None:
        VCGq_ = 0
    if VCGprice is None:
        VCGprice = UPprice
    if UPq_ is None:
        UPq_ = 0
    
    extra = {
        'clearing quantity UP': UPq_,
        'clearing price': UPprice,
        'VCG quantity': VCGq_,
        'VCG price': VCGprice,
        'Total quantity': UPq_ + VCGq_
    }
    
    return trans, extra


class VCG(pm.Mechanism):
    """
    Interface for Vickrey-Clarke-Groves mechanism.

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
    """

    def __init__(self, bids, *args, **kwargs):
        FIT = kwargs.get('FIT', 0.1)
        TOU = kwargs.get('TOU', 0.25)
        cap = kwargs.get('cap', 100)
        floor = kwargs.get('floor', 10)
        pm.Mechanism.__init__(self, two_steps_VCG_mechanism, bids, FIT=FIT, TOU=TOU, cap=cap, floor=floor, *args, **kwargs)
