import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def weighted_average_method(bids_uncovered: pd.DataFrame, trans: pm.TransactionManager):
    """
    Weighted Average Method (WAM) for trading uncovered bids.
    Uses quantity-weighted average prices.
    """
    buying_bids = bids_uncovered.loc[bids_uncovered['buying']].sort_values('price', ascending=False)
    selling_bids = bids_uncovered.loc[~bids_uncovered['buying']].sort_values('price', ascending=True)
    
    buying_quantity = buying_bids.quantity.sum()
    selling_quantity = selling_bids.quantity.sum()
    
    if buying_quantity > selling_quantity:
        long_side, short_side = buying_bids, selling_bids
    else:
        long_side, short_side = selling_bids, buying_bids
    
    traded_quantity = short_side.quantity.sum()
    weighted_price = (buying_bids.price.multiply(buying_bids.quantity).sum() + selling_bids.price.multiply(selling_bids.quantity).sum()) / (buying_quantity + selling_quantity)
    
    for i, x in short_side.iterrows():
        if traded_quantity <= 0:
            break
        trade_qty = min(x.quantity, traded_quantity)
        trans.add_transaction(i, trade_qty, weighted_price, -1, False)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] -= trade_qty
        traded_quantity -= trade_qty
    
    quantity_added = 0
    for i, x in long_side.iterrows():
        if traded_quantity <= 0:
            break
        x_quantity = min(x.quantity, traded_quantity - quantity_added)
        trans.add_transaction(i, x_quantity, weighted_price, -1, False)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] -= x_quantity
        quantity_added += x_quantity
    
    return bids_uncovered, weighted_price


def two_steps_WAM_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Weighted Average Method (WAM) mechanism.
    Step 1: Run UP mechanism
    Step 2: Run WAM for uncovered bids
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
    
    unsold_quantity = bidsUP.loc[~bidsUP['buying'], 'quantity'].sum()
    demanded_quantity = bidsUP.loc[bidsUP['buying'], 'quantity'].sum()
    bids_uncovered = bidsUP.loc[bidsUP['quantity'] > 0, :]
    
    # Step 2: WAM
    WAMq_ = 0
    WAMprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0:
        bidsM, WAMprice = weighted_average_method(bids_uncovered, trans)
        WAMq_ = bidsM.quantity.sum()
    
    if WAMq_ is None:
        WAMq_ = 0
    if WAMprice is None:
        WAMprice = UPprice
    if UPq_ is None:
        UPq_ = 0
    
    extra = {
        'clearing quantity UP': UPq_,
        'clearing price': UPprice,
        'WAM quantity': WAMq_,
        'WAM price': WAMprice,
        'Total quantity': UPq_ + WAMq_
    }
    
    return trans, extra


class WAM(pm.Mechanism):
    """
    Interface for Weighted Average Method mechanism.

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
        pm.Mechanism.__init__(self, two_steps_WAM_mechanism, bids, FIT=FIT, TOU=TOU, *args, **kwargs)
