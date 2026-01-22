import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism
def adjusted_uniform_price_mechanism(bids: pd.DataFrame, *args, **kwargs):
    FIT = kwargs.pop('FIT', 0.1)
    TOU = kwargs.pop('TOU', 0.25)
    step = kwargs.pop('step', 0.1)
    max_iterations = kwargs.pop('max_iterations', 10)

    results_log = []
    current_bids = bids.copy()
    trans_all = pm.TransactionManager()

    for iteration in range(1, max_iterations + 1):
        print(f"AUP Iteration {iteration}")

        # Run uniform price mechanism
        trans_iter, result = uniform_price_mechanism(current_bids)
        df=trans_iter.get_df()
        #print(f'transactions quantity: {df["quantity"].sum()}')
        # Merge this iteration's transactions
        for _, row in trans_iter.get_df().iterrows():
            trans_all.add_transaction(row['bid'], row['quantity'], row['price'], row['source'], row['active'])

        # Log current result
        total_demand = current_bids[current_bids['buying']]['quantity'].sum()
        total_supply = current_bids[~current_bids['buying']]['quantity'].sum()

        results_log.append({
            "iteration": iteration,
            "clearing_price": result['clearing price'],
            "clearing_quantity": result['clearing quantity'],
            "demand_quantity": total_demand,
            "supply_quantity": total_supply
        })


        # Update remaining quantities
        updated_bids = current_bids.copy()
        for _, row in trans_iter.get_df().iterrows():
            bid_index = row['bid']
            quantity = row['quantity']
            if bid_index in updated_bids.index:
                updated_bids.loc[bid_index, 'quantity'] -= quantity
        updated_bids.index = updated_bids.index.astype(int)

        
        unsold_quantity = updated_bids.loc[~updated_bids['buying'], 'quantity'].sum()
        demanded_quantity = updated_bids.loc[updated_bids['buying'], 'quantity'].sum()
        if unsold_quantity == 0 or demanded_quantity == 0:
            print("No unsold or demanded quantities left, breaking the loop.")
            break
        # Price adjustment
        #print(f'Adjusting prices for unsold bids: {unsold_quantity}, demanded bids: {demanded_quantity}')
        updated_bids.loc[updated_bids['buying'], 'price'] = updated_bids.loc[updated_bids['buying'], 'price']*(1+step)
        updated_bids.loc[~updated_bids['buying'], 'price'] =updated_bids.loc[~updated_bids['buying'], 'price']*(1-step)
        

        # Enforce FIT/TOU constraints
        updated_bids.loc[updated_bids['buying'], 'price'] = updated_bids.loc[updated_bids['buying'], 'price'].clip(lower=FIT, upper=TOU)
        updated_bids.loc[~updated_bids['buying'], 'price'] = updated_bids.loc[~updated_bids['buying'], 'price'].clip(lower=FIT, upper=TOU)

        current_bids = updated_bids.copy()
    total_traded_quantity=round(trans_all.get_df()['quantity'].sum(), 4)
    print(f'Final clearing price: {result["clearing price"]}, Final clearing quantity: {total_traded_quantity}')
    return trans_all, {
        'clearing quantity': total_traded_quantity,
        'clearing price': result['clearing price'],
        'results_log': results_log
    }



class AUP(pm.Mechanism):
    """
    Interface for our new uniform price mechanism.

    Parameters
    -----------
    bids
        Collection of bids to run the mechanism
        with.
    """

    def __init__(self, bids, *args, **kwargs):
            FIT = kwargs.get('FIT', 0.1)
            TOU = kwargs.get('TOU', 0.25)
            pm.Mechanism.__init__(self, adjusted_uniform_price_mechanism, bids, FIT, TOU, *args, **kwargs)