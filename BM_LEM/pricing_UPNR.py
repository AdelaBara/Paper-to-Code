import numpy as np
import pandas as pd
import pymarket as pm
from BM_LEM.pricing_UP import find_clearing_price_and_quantity, uniform_price_mechanism

def newton_raphson_adjustment(bids_uncovered: pd.DataFrame, trans: pm.TransactionManager, FIT: float, TOU: float):
    """
    Newton-Raphson adjustment mechanism for price discovery on uncovered bids.
    """
    # get uncovered bids: buy and sell    
    buyers = bids_uncovered.loc[bids_uncovered['buying']].sort_values('price', ascending=False)
    sellers = bids_uncovered.loc[~bids_uncovered['buying']].sort_values('price', ascending=True)
    
    # Find the long side of the market
    QS = sellers['quantity'].sum()
    QB = buyers['quantity'].sum()
    maxQt = min(QS, QB)
    k = 0.0005
    
    # Define the function and Newton-Raphson implementation
    def fprice(k, buyers, sellers, maxQt):
        price = (sellers['price'].mean() * (1 - k) + buyers['price'].mean() * (1 + k)) / 2
        demand = buyers.loc[buyers['price'] * (1 + k) > price, 'quantity'].sum()
        supply = sellers.loc[sellers['price'] * (1 - k) < price, 'quantity'].sum()
        Qt = min(demand, supply)
        if demand > maxQt:
            demand = maxQt
        if supply > maxQt:
            supply = maxQt
        fprice = maxQt - Qt
        return fprice
    
    def numerical_derivative(f, buyers, sellers, maxQt, initial_h=1e-5, max_iterations=100):
        h = initial_h
        for i in range(max_iterations):
            derivative = (f(k + h, buyers, sellers, maxQt) - f(k, buyers, sellers, maxQt)) / h
            if derivative != 0:
                return derivative  # Return the derivative if it's non-zero
            # Adjust h if derivative is zero
            h *= 10  # Increase h by a factor of 10       
        # If all adjustments result in a zero derivative, return zero
        return 0
    
    # Refined Newton-Raphson implementation 
    def find_equilibrium_newton_raphson(k, buyers, sellers, tolerance=0.01, max_iterations=100, epsilon=1e-5):
        for i in range(max_iterations):
            f_p = fprice(k, buyers, sellers, maxQt)
            f_prime_p = numerical_derivative(fprice, buyers, sellers, maxQt)
            
            if abs(f_p) < tolerance:
                price = round((sellers['price'].mean() * (1 - k) + buyers['price'].mean() * (1 + k)) / 2, 4)
                print(f"Converged in {i} iterations: Price = {price}, k={k}")
                return price  # Convergence achieved
   
            # Newton-Raphson update
            k = k - 0.1 * f_p / (f_prime_p + epsilon)  
            price = round((sellers['price'].mean() * (1 - k) + buyers['price'].mean() * (1 + k)) / 2, 4)
        return price  # Return the best guess after max iterations
    
    # Apply the refined Newton-Raphson method to find the equilibrium price
    price = find_equilibrium_newton_raphson(k, buyers, sellers)
    
    # Check if price exceeds TOU or FIT and return 0
    if price > TOU or price < FIT:
        return bids_uncovered, buyers, sellers, QB, QS, 0, 0 
    
    # otherwise update buyers and sellers with price. Update price and quantity similar to UP  
    if QB > QS:
        long_side = buyers
        short_side = sellers
    else:
        long_side = sellers
        short_side = buyers
    traded_quantity = maxQt
    
    # All the short side will trade at `price`
    for i, x in short_side.iterrows():
        t = (i, x.quantity, price, -1, False)
        trans.add_transaction(*t)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] = bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] - x.quantity

    # The long side has to trade only up to the short side
    quantity_added = 0
    for i, x in long_side.iterrows():
        if quantity_added == traded_quantity:
            break
        if x.quantity + quantity_added <= traded_quantity:
            x_quantity = x.quantity
        else:
            x_quantity = traded_quantity - quantity_added
        t = (i, x_quantity, price, -1, False)
        trans.add_transaction(*t)
        bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] = bids_uncovered.loc[bids_uncovered.index == i, 'quantity'] - x_quantity
        quantity_added += x_quantity

    return bids_uncovered, buyers, sellers, QB, QS, price, traded_quantity


def two_steps_UPNR_mechanism(bids: pd.DataFrame, *args, **kwargs):
    """
    Two-step Uniform Price with Newton-Raphson (UPNR) mechanism.
    Step 1: Run UP mechanism
    Step 2: Run Newton-Raphson adjustment for uncovered bids
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
    
    # Step 2: Newton-Raphson adjustment mechanism
    Mq_ = 0
    Mprice = UPprice
    if unsold_quantity > 0 and demanded_quantity > 0:
        bidsM, buying_bids, selling_bids, buying_quantity, selling_quantity, Mprice, Mq_ = newton_raphson_adjustment(bids_uncovered, trans, FIT, TOU)
    
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


class UPNR(pm.Mechanism):
    """
    Interface for Uniform Price with Newton-Raphson adjustment mechanism.

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
        pm.Mechanism.__init__(self, two_steps_UPNR_mechanism, bids, FIT=FIT, TOU=TOU, *args, **kwargs)
