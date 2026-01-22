import pandas as pd
import pymarket as pm

import pandas as pd
import pymarket as pm

def find_clearing_price_and_quantity(bids: pd.DataFrame):
    """
    Determine the uniform clearing price and quantity based on aggregated
    supply and demand where cumulative demand >= cumulative supply.
    """
    # Separate buy/sell
    buyers = bids[bids['buying']].copy()
    sellers = bids[~bids['buying']].copy()

    if buyers.empty or sellers.empty:
        return None, None

    # Candidate clearing prices = unique sorted prices from both sides
    candidate_prices = sorted(set(buyers['price']).union(sellers['price']))

    best_price = None
    best_quantity = 0

    for p in candidate_prices:
        # Demand: total quantity where bid price ≥ p
        demand_qty = buyers.loc[buyers['price'] >= p, 'quantity'].sum()
        # Supply: total quantity where ask price ≤ p
        supply_qty = sellers.loc[sellers['price'] <= p, 'quantity'].sum()
        # Traded quantity = min of both
        traded_qty = min(demand_qty, supply_qty)

        if traded_qty > best_quantity:
            best_quantity = traded_qty
            best_price = p

    if best_quantity == 0:
        return None, None

    return best_quantity, best_price

def uniform_price_mechanism(bids: pd.DataFrame):
    trans = pm.TransactionManager()

    clearing_quantity, clearing_price = find_clearing_price_and_quantity(bids)

    if clearing_price is None or clearing_quantity is None:
        print("No intersection found between supply and demand curves.")
        return trans, {'clearing quantity': 0, 'clearing price': None}
    else:
        print(f"Clearing price: {clearing_price}, Clearing quantity: {clearing_quantity}")

    # Filter bids willing to trade at clearing price
    buyers = bids[(bids['buying']) & (bids['price'] >= clearing_price)].copy()
    sellers = bids[(~bids['buying']) & (bids['price'] <= clearing_price)].copy()

    # Sort for matching
    buyers.sort_values(by='price', ascending=False, inplace=True)
    sellers.sort_values(by='price', ascending=True, inplace=True)

    # Traded quantity = min of demand/supply sides
    traded_quantity = min(buyers['quantity'].sum(), sellers['quantity'].sum())

    # Execute seller trades (short side)
    qty_left = traded_quantity
    for i, row in sellers.iterrows():
        q = min(row['quantity'], qty_left)
        if q <= 0:
            continue
        trans.add_transaction(i, q, clearing_price, -1, False)
        qty_left -= q
        if qty_left <= 0:
            break

    # Execute buyer trades
    qty_left = traded_quantity
    for i, row in buyers.iterrows():
        q = min(row['quantity'], qty_left)
        if q <= 0:
            continue
        trans.add_transaction(i, q, clearing_price, -1, False)
        qty_left -= q
        if qty_left <= 0:
            break

    return trans, {
        'clearing quantity': round(traded_quantity, 4),
        'clearing price': round(clearing_price, 4)
    }



class UP(pm.Mechanism):
    """
    Interface for our new uniform price mechanism.

    Parameters
    -----------
    bids
        Collection of bids to run the mechanism
        with.
    """

    def __init__(self, bids, *args, **kwargs):
        """TODO: to be defined1. """
        pm.Mechanism.__init__(self, uniform_price_mechanism, bids, *args, **kwargs)