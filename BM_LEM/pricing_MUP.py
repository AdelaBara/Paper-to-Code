import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def mediation_mechanism(bids: pd.DataFrame, trans: pm.TransactionManager):
    """
    P2P mediation mechanism for matching remaining bids after UP mechanism.
    """
    # get uncovered bids: buy and sell    
    buying_bids = bids.loc[bids['buying']].sort_values('price', ascending=False)
    selling_bids = bids.loc[~bids['buying']].sort_values('price', ascending=True)

    # Find the long side of the market
    buying_quantity = buying_bids.quantity.sum()
    selling_quantity = selling_bids.quantity.sum()

    if buying_quantity > selling_quantity:
        long_side = buying_bids
        short_side = selling_bids
    else:
        long_side = selling_bids
        short_side = buying_bids
    
    q_ = 0
    # Iterate through short side and mediate with long side 
    for i, x in short_side.iterrows():
        sprice = x.price
        squantity = x.quantity
        for j, y in long_side.iterrows():
            lprice = y.price
            lquantity = y.quantity
            price = round((sprice + lprice) / 2, 4)
            if squantity < lquantity:
                quantity = squantity
                squantity = 0                 
                lquantity = lquantity - quantity
                long_side.loc[long_side.index == j, 'quantity'] = lquantity
            else:
                quantity = lquantity
                lquantity = 0
                long_side = long_side.drop(j)  # remove bid j
                squantity = squantity - quantity
                short_side.loc[short_side.index == j, 'quantity'] = squantity
            # add transaction and update bids
            t = (i, quantity, price, -1, False)
            trans.add_transaction(*t)
            t = (j, quantity, price, -1, False)
            trans.add_transaction(*t)
            q_ = q_ + quantity
            bids.loc[bids.index == i, 'quantity'] = bids.loc[bids.index == i, 'quantity'] - quantity
            bids.loc[bids.index == j, 'quantity'] = bids.loc[bids.index == j, 'quantity'] - quantity
            if squantity == 0: 
                short_side = short_side.drop(i)  # remove bid i
                break
    
    return bids, buying_bids, selling_bids, buying_quantity, selling_quantity, price, q_


def two_steps_UPM_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Uniform Price with Mediation (MUP) mechanism.
    Step 1: Run UP mechanism
    Step 2: Run mediation for uncovered bids
    """
    FIT = kwargs.pop('FIT', 0.1)
    TOU = kwargs.pop('TOU', 0.25)
    
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
    
    unsold_quantity = bidsUP.loc[bidsUP['buying'] == False, 'quantity'].sum()
    demanded_quantity = bidsUP.loc[bidsUP['buying'] == True, 'quantity'].sum()
    bids_uncovered = bidsUP.loc[bidsUP['quantity'] > 0, :]
    
    # Step 2: Mediation mechanism
    Mq_ = 0
    Mprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0: 
        bidsM, buying_bids, selling_bids, buying_quantity, selling_quantity, Mprice, Mq_ = mediation_mechanism(bids_uncovered, trans)
    
    if Mq_ is None:
        Mq_ = 0
    if Mprice is None:
        Mprice = UPprice
    if UPq_ is None:
        UPq_ = 0
    
    extra = {
        'clearing quantity UP': UPq_,
        'clearing price': UPprice,
        'mediation quantity': Mq_,
        'last price': Mprice,
        'Total quantity': UPq_ + Mq_
    }

    return trans, extra


class MUP(pm.Mechanism):
    """
    Interface for Uniform Price with Mediation mechanism.

    Parameters
    -----------
    bids
        Collection of bids to run the mechanism with.
    FIT
        Feed-in Tariff (minimum price).
    TOU
        Time-of-Use (maximum price).
    """

    def __init__(self, bids, *args, **kwargs):
        FIT = kwargs.get('FIT', 0.1)
        TOU = kwargs.get('TOU', 0.25)
        pm.Mechanism.__init__(self, two_steps_UPM_mechanism, bids, FIT=FIT, TOU=TOU, *args, **kwargs)
