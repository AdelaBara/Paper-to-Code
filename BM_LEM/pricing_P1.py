import pymarket as pm

from . import pricing_UP


def pricingP1(bids):
    """
    Fallback pricing mechanism for P1 using uniform price logic.
    """
    return pricing_UP.uniform_price_mechanism(bids)
