import pymarket as pm

from . import pricing_UP


class UniformPrice(pm.Mechanism):
    """
    Uniform price mechanism wrapper for pymarket.
    """

    def __init__(self, bids, *args, **kwargs):
        pm.Mechanism.__init__(self, pricing_UP.uniform_price_mechanism, bids, *args, **kwargs)
