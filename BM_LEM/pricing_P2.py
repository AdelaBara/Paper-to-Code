import numpy as np
import pandas as pd
import pymarket as pm

def uniform_price_clearing(bids, *args, **kwargs):
    # Step 1: Construct demand and supply curves
    demand_curve = pm.bids.demand_curve_from_bids(bids)
    supply_curve = pm.bids.supply_curve_from_bids(bids)

    # Step 2: Identify tradable bids
    tradable_bids = demand_curve.intersect_with(supply_curve)

    if len(tradable_bids) == 0:
        return pm.TransactionManager(), {}

    # Step 3: Allocate transactions to short side (fully)
    for bid in tradable_bids:
        trans = pm.TransactionManager()
        trans.add_transaction(bid.id, -1, bid.q, bid.p)

    # Step 4: Allocate transactions to long side (partially)
    q_traded = min(tradable_bids[0].q, tradable_bids[-1].q)
    q_accum = 0
    for i in range(len(tradable_bids)):
        bid = tradable_bids[i]
        if q_accum + bid.q <= q_traded:
            q_x = bid.q
        else:
            q_x = q_traded - q_accum
            break
        trans = pm.TransactionManager()
        trans.add_transaction(bid.id, 1, q_x, bid.p)
        q_accum += q_x

    # Step 5: Return results
    return trans, {'clearing quantity': q_traded, 'clearing price': bid.p}

class UniformPrice(pm.Mechanism):
    def __init__(self, bids, *args, **kwargs):
        pm.Mechanism.__init__(self, uniform_price_clearing, bids, *args, **kwargs)
