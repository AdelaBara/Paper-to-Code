from __future__ import annotations
import mesa
from mesa.datacollection import DataCollector

from mesa.agent import Agent
from mesa.time import RandomActivation
import numpy as np
import pandas as pd

import warnings
warnings.filterwarnings('ignore')
import random

import LEM_utils.Utils as Utils
from LEM_utils.tariff_utils import tariff_rate_for_timestamp
from datetime import datetime, timedelta


import pymarket as pm
import BM_LEM.pricing_uniform_price as mk_models #market clearing models, other models than already implemented in Pymarket
#add UniformPrice as a Mechanism in pymarket
pm.market.MECHANISM['uniform'] = mk_models.UniformPrice

""" This section imports extended BM model for pricing mechanism in pymarket"""
import BM_LEM.pricing_UP as pricing_UP #market clearing models, other models than already implemented in Pymarket
pm.market.MECHANISM['UP'] = pricing_UP.UP
import BM_LEM.pricing_AUP as pricing_AUP #market clearing models, other models than already implemented in Pymarket
#add new Pricing Mechanism as a Mechanism in pymarket
pm.market.MECHANISM['AUP'] = pricing_AUP.AUP
import BM_LEM.pricing_MUP as pricing_MUP
pm.market.MECHANISM['MUP'] = pricing_MUP.MUP
import BM_LEM.pricing_UPNR as pricing_UPNR
pm.market.MECHANISM['UPNR'] = pricing_UPNR.UPNR
import BM_LEM.pricing_APM as pricing_APM
pm.market.MECHANISM['APM'] = pricing_APM.APM
import BM_LEM.pricing_MPAS as pricing_MPAS
pm.market.MECHANISM['MPAS'] = pricing_MPAS.MPAS
import BM_LEM.pricing_CFRM as pricing_CFRM
pm.market.MECHANISM['CFRM'] = pricing_CFRM.CFRM
import BM_LEM.pricing_WAM as pricing_WAM
pm.market.MECHANISM['WAM'] = pricing_WAM.WAM
import BM_LEM.pricing_MMP as pricing_MMP
pm.market.MECHANISM['MMP'] = pricing_MMP.MMP
import BM_LEM.pricing_IPA as pricing_IPA
pm.market.MECHANISM['IPA'] = pricing_IPA.IPA
import BM_LEM.pricing_VCG as pricing_VCG
pm.market.MECHANISM['VCG'] = pricing_VCG.VCG
import BM_LEM.pricing_NBS as pricing_NBS
pm.market.MECHANISM['NBS'] = pricing_NBS.NBS
import BM_LEM.pricing_CGT as pricing_CGT
pm.market.MECHANISM['CGT'] = pricing_CGT.CGT
import BM_LEM.pricing_CGTS as pricing_CGTS
pm.market.MECHANISM['CGTS'] = pricing_CGTS.CGTS
import BM_LEM.pricing_COLM as pricing_COLM
pm.market.MECHANISM['COLM'] = pricing_COLM.COLM
import BM_LEM.pricing_P1 as pricing_P1
import BM_LEM.pricing_P2 as pricing_P2

from core.EC_model import EnergyCommunity, Member

class LEMAgent(mesa.Agent, Member):
    """An agent representing a participant in the Local Energy Market (LEM) community.
    LEMAgent handles simulation and interaction in the environment.
    Member handles energy community modeling (states, assets)."""

    def __init__(self, model: LEMCommunity, member: Member):
        unique_id = member.member_id
        super().__init__(unique_id, model)
        self.agent_id = unique_id  # Unique identifier for the agent
        self.member=member  # Reference to the Member instance. Favor Composition Over Inheritance
        self.bid_quantity = 0  # Quantity the member is willing to buy/sell
        self.bid_price = 0  # Price at which the member is willing to buy/sell
        self.traded_quantity = 0  # Clearing quantity after market clearing
        self.traded_price = 0  # Clearing price after market clearing
        self.buying = False  # True if the member is buying, False if selling
        self.market_states=[]    # List to store market states (time_step, bid_quantity, bid_price, buying)
        self.trading_states=[]  # List to store trading states (time_step, traded_quantity, traded_price)
        self.agent_market_states = pd.DataFrame()  # DataFrame to store aggregated market states
        self.current_step = 0  # Current step index in the simulation
        self.time_step = None  # Current time step in the simulation

    def step(self, market: pm.Market):
        # Called by the model at each time step
        self.time_step = self.model.current_time
        self.current_step = self.model.time_index  # Get the current step index
        # Get prices
        TOU = tariff_rate_for_timestamp(self.model.TOU, self.time_step, price_col="tou")
        FIT = tariff_rate_for_timestamp(self.model.FIT, self.time_step, price_col="fit")
        PU_avg = (TOU + FIT) / 2
        # Generate market offer
        self.generate_market_offer( market, TOU, PU_avg, FIT)

    def generate_market_offer(self, market, TOU, PU_avg, FIT):
        self.state=self.member.get_state(self.time_step)  # Get the member's state at the current time step (df row)
        #print(f"Agent {self.agent_id} at time step {time_step} with state: {self.state}")
        # Create offer based on net_balance and bid with pymarket
        self.net_balance = self.state['net_balance'].iloc[0]  # Get net balance from the state
        if self.net_balance < 0:  # deficit
            self.bid_quantity = -self.net_balance  # Quantity to buy
            self.bid_price = round(random.uniform(PU_avg*0.8, TOU *0.99), 2)
            self.bid_price=np.clip(self.bid_price, FIT, TOU)  # Ensure bid price is within bounds
            self.buying = True  # Set buying flag
            # Offer to buy in the market
            market.accept_bid(self.bid_quantity, self.bid_price, self.agent_id, True)  # buyer
        else:
            self.bid_quantity = self.net_balance  # Quantity to sell
            self.bid_price = round(random.uniform(FIT*1.1, PU_avg*1.2), 2)
            self.bid_price=np.clip(self.bid_price, FIT, TOU)  # Ensure bid price is within bounds
            self.buying = False  # Set buying flag to False
            # Offer to sell in the market
            market.accept_bid(self.bid_quantity, self.bid_price, self.agent_id, False)  # seller
        self.market_states.append([self.time_step, self.current_step, self.bid_quantity, self.bid_price, self.buying])  # Append to market states
        #print(f"Agent {self.agent_id} offers quantity {self.bid_quantity} at price {self.bid_price} at time step {time_step}")

    def process_market_result(self, time_step, traded_quantity, traded_price):
        # Update state based on market clearing
        self.time_step = time_step  # Update the time step
        self.traded_quantity = traded_quantity  # Quantity traded in the market
        self.traded_price = traded_price  # Price at which the trade occurred
        self.trading_states.append([self.time_step, self.traded_quantity, self.traded_price])  # Append to market states

    def aggregate_agent_market_states(self):
        """Aggregate market states into a DataFrame."""
        self.agent_market_states = pd.DataFrame(self.market_states, columns=['time_step', 'step', 'bid_quantity', 'bid_price', 'buying'])
        self.agent_market_states['agent_id'] = self.agent_id
        df_trading = pd.DataFrame(self.trading_states, columns=['time_step', 'traded_quantity', 'traded_price'])
        self.agent_market_states = self.agent_market_states.merge(df_trading, on='time_step', how='left')
        self.agent_market_states['time_step'] = pd.to_datetime(self.agent_market_states['time_step'])  # Convert time_step to datetime
        self.agent_market_states.fillna({'traded_quantity': 0, 'traded_price': 0}, inplace=True)  # Fill NaN values
        return self.agent_market_states

class LEMCommunity(mesa.Model):
    def __init__(self, EC: EnergyCommunity, time_window: tuple = None, target_date: pd.Timestamp.date = None):
        super().__init__()
        self.num_agents = len(EC.members)
        self.schedule = mesa.time.RandomActivation(self)
        self.has_market=False
        self.market = pm.Market() 
        self.market_states=EC.compute_community_states()
        self.step_logs = []  # to store logs from each step
        # Initialize time
        self.time_index = 0
        self.time_steps = list(self.market_states['Timestamp'])  # List of time steps from the community states
        self.TOU=EC.TOU
        self.FIT=EC.FIT
        self.all_market_states= pd.DataFrame()  # DataFrame to store aggregated market states
        
        # Filter time_steps if time_window is provided as tuple of (start_time, end_time)
        # Example: time_window = (datetime.time(6, 0), datetime.time(22, 0))
        if time_window is not None:
            self.time_steps = self._filter_time_steps(time_window)
            print(f"Filtered time steps to {len(self.time_steps)} intervals based on time_window={time_window}")
        
        if target_date is not None: #target_date = pd.Timestamp("2025-06-06").date()
            self.time_steps = [
                ts for ts in self.time_steps if ts.date() == target_date]

        for i in range(self.num_agents):
            agent = LEMAgent(self, EC.members[i])  # Create a LEMAgent for each member
            self.schedule.add(agent)
            print(f"Added agent {agent.agent_id} of type {agent.member.member_type} with assets: {[asset.asset_name for asset in agent.member.assets]}")

        self.datacollector = DataCollector(
            agent_reporters={"agent_id":lambda agent: agent.agent_id, 
                             "time_step": lambda agent: agent.time_step,
                             "bid_quantity": lambda agent: agent.bid_quantity, 
                             "bid_price": lambda agent: agent.bid_price                             
                           })
    
    def _filter_time_steps(self, time_window):
        """Filters self.time_steps to include only those within the specified time window.
           time_window: tuple of (start_time, end_time), where each is a datetime.time or pd.Timestamp.
           start_time = datetime.time(6, 0)
           end_time = datetime.time(22, 0)
           """
        start, end = time_window
        filtered_steps = []
        for ts in self.time_steps:
            ts_time = ts.time() if isinstance(ts, pd.Timestamp) else ts
            if start <= ts_time <= end:
                filtered_steps.append(ts)
        return filtered_steps

    @property
    def current_time(self):
        return self.time_steps[self.time_index]
    def set_pricing_mechanism(self, pricing_mechanism: str):
        """Sets the pricing mechanism for the market clearing.
           pricing_mechanism: 'uniform' or 'AUP' (adjusted uniform price) or other extended mechanisms."""
        if pricing_mechanism not in pm.market.MECHANISM:
            raise ValueError(f"Pricing mechanism '{pricing_mechanism}' is not supported.")
        self.pricing_mechanism = pricing_mechanism
        print(f"Pricing mechanism set to {self.pricing_mechanism}")

    def step(self):
        self.market = pm.Market()
        print(f"Current step {self.time_index} and time step: {self.current_time}")
        log = {"step": self.time_index, "time": str(self.current_time), "events": [], "extras":[]}
        log["events"].append(f"Current step {self.time_index} and time step: {self.current_time}")
        # For each agent, call their step method with self.market
        for agent in self.schedule.agents:
            agent.step(self.market)
        # Run market clearing only if there are agents with surplus
        # Check for agents with surplus
        agents_with_surplus = [agent for agent in self.schedule.agents if agent.net_balance > 0]
        if agents_with_surplus:
            print(f"There are {len(agents_with_surplus)} prosumers with surplus in this step.")
            log["events"].append(f"There are {len(agents_with_surplus)} prosumers with surplus in this step.")
            self.has_market = True
            # Run the market
            self.transactions, self.extras = self.market.run(self.pricing_mechanism)
            df_transactions=self.transactions.get_df()
            total_traded_quantity = df_transactions['quantity'].sum() if not df_transactions.empty else 0
            
            
            # Process market results for each agent
            for agent in self.schedule.agents:
                if agent.agent_id in df_transactions['bid'].values:
                    # If the agent is in the transactions, get the traded quantity and price for the agent
                    traded_quantity = df_transactions.loc[df_transactions['bid'] == agent.agent_id, 'quantity'].sum()
                    traded_price = df_transactions.loc[df_transactions['bid'] == agent.agent_id, 'price'].values[0]
                    agent.process_market_result(self.current_time, traded_quantity, traded_price)               
            print(f"Market cleared at time step {self.current_time} with {len(df_transactions)} transactions and total traded quantity: {total_traded_quantity}")
            log["events"].append(f"Market cleared at time step {self.current_time} with {len(df_transactions)} transactions")
            log['extras'].append(self.extras)
        # If no agents with surplus, set has_market to False
        else:
            self.has_market = False
            print("No prosumers with surplus in this step, skipping market clearing.")
            log["events"].append("No prosumers with surplus in this step, skipping market clearing.")
            log["extras"] = {}
        self.datacollector.collect(self)
        # Advance to the next time step (if available)
        if self.time_index < len(self.time_steps) - 1:
            self.time_index += 1
        else:
            print("Simulation complete: all time steps processed.")
            log["events"].append("Simulation complete: all time steps processed.")
            self.time_index += 1  # force exit on the next loop
        self.step_logs.append(log)
    def aggregate_market_states(self):
        # Aggregate market states of all agents into a single DataFrame
        for agent in self.schedule.agents:
            agent.aggregate_agent_market_states()
        self.all_market_states = pd.concat([a.agent_market_states for a in self.schedule.agents if not a.agent_market_states.empty])
        self.all_market_states.rename(columns={'time_step':'Timestamp', 'agent_id':'member_id'}, inplace=True)
        self.all_market_states['traded_deficit'] = 0  # Initialize column
        self.all_market_states.loc[self.all_market_states['buying'] == True, 'traded_deficit'] = \
        self.all_market_states.loc[self.all_market_states['buying'] == True, 'traded_quantity']
        self.all_market_states['traded_surplus']=0
        self.all_market_states.loc[self.all_market_states['buying'] == False, 'traded_surplus'] = \
        self.all_market_states.loc[self.all_market_states['buying'] == False, 'traded_quantity']
        return self.all_market_states
    
