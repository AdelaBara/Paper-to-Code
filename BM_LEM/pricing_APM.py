import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def average_price_method(bids_uncovered: pd.DataFrame, trans: pm.TransactionManager):
    """
    Average Price Method (APM) for trading uncovered bids.
    Trades at the average of buyer and seller prices.
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
    
    for i, x in short_side.iterrows():
        if traded_quantity <= 0:
            break
        trade_qty = min(x.quantity, traded_quantity)
        avg_price = (x.price + long_side.iloc[0].price) / 2
        trans.add_transaction(i, trade_qty, avg_price, -1, False)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] -= trade_qty
        traded_quantity -= trade_qty
    
    quantity_added = 0
    for i, x in long_side.iterrows():
        if traded_quantity <= 0:
            break
        x_quantity = min(x.quantity, traded_quantity - quantity_added)
        avg_price = (x.price + short_side.iloc[0].price) / 2
        trans.add_transaction(i, x_quantity, avg_price, -1, False)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] -= x_quantity
        quantity_added += x_quantity
    
    return bids_uncovered


def two_steps_APM_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Average Price Method (APM) mechanism.
    Step 1: Run UP mechanism
    Step 2: Run APM for uncovered bids
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
    
    # Step 2: Average Price Method
    APMq_ = 0
    APMprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0:
        bidsM = average_price_method(bids_uncovered, trans)
        APMq_ = bidsM.quantity.sum()
        APMprice = bidsM['price'].mean() if not bidsM.empty else UPprice
    
    if APMq_ is None:
        APMq_ = 0
    if APMprice is None:
        APMprice = UPprice
    if UPq_ is None:
        UPq_ = 0
    
    extra = {
        'clearing quantity UP': UPq_,
        'clearing price': UPprice,
        'APM quantity': APMq_,
        'last price': APMprice,
        'Total quantity': UPq_ + APMq_
    }
    
    return trans, extra


class APM(pm.Mechanism):
    """
    Interface for Average Price Method mechanism.

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
        pm.Mechanism.__init__(self, two_steps_APM_mechanism, bids, FIT=FIT, TOU=TOU, *args, **kwargs)
