import pandas as pd
import numpy as np
import config_auth
import ccxt
import sys
import FollowTrendGridStrategy
import choppiness_index
import matplotlib.pyplot as plt
import ReverseTrendGridStrategy
import time
from datetime import datetime
from datetime import timedelta

# Exchange Initialization
exchange = ccxt.gate({
    'apiKey': config_auth.API_KEY,
    'secret': config_auth.SECRET_KEY,
    "options": {
        'defaultType': 'swap'
    }
})
# ******************  GLOBAL DICTIONARIES ******************
BOT_TREND_FOLLOWING= {"BTC_USDT": FollowTrendGridStrategy.TrendGridStrategy("BTC_USDT", 10, 5, 5, 500, 20), "ETC_USDT": FollowTrendGridStrategy.TrendGridStrategy("ETC_USDT", 10, 5, 5, 2, 10),
                                         "LTC_USDT": FollowTrendGridStrategy.TrendGridStrategy("LTC_USDT", 10, 5, 5, 2, 20)}

BOT_AGAINST_TREND= {"BTC_USDT": ReverseTrendGridStrategy.ReverseGridStrategy("BTC_USDT", 10, 5, 5, 500, 20), "ETC_USDT": ReverseTrendGridStrategy.ReverseGridStrategy("ETC_USDT", 10, 5, 5, 2, 10),
                                         "LTC_USDT": ReverseTrendGridStrategy.ReverseGridStrategy("LTC_USDT", 10, 5, 5, 2, 20)}

BOT_TREND = {"TRENDING" : BOT_TREND_FOLLOWING, "RANGING": BOT_AGAINST_TREND}

# GLOBAL VARIABLES

# Redundant
#DEPLOYED_BOTS = {}
#GRIDBOTS_TREND = {}
#DEPLOYED_BOTS_SWITCH = {}


DEPLOYED_BOTS_SWITCH = {}
PAIRS = ["LTC_USDT"]
DEPLOYMENT_LIST = []
GRIDBOTS = {} # Class Object, Current Mode of Operation, Trend, Switch
TIMEFRAME = "1h"
LOOKBACK = 5

# HELPER FUNCTIONS

def populate_deployment_list():
    for pair in PAIRS:
        curr = datetime.now()
        prev = datetime.now() - timedelta(hours=10)
        search_pair = str(pair).replace("_", "") 
        pair_ci = choppiness_index.Choppiness_Indicator(search_pair, prev, curr, TIMEFRAME, LOOKBACK)
        pair_ci_trend = pair_ci.compute_trend()
        DEPLOYMENT_LIST.append((pair, pair_ci_trend))
        print(pair_ci.trend)


def populate_global_var():
    
    for deployment in DEPLOYMENT_LIST:
        if deployment[1] == "TRENDING":
            GRIDBOTS[deployment[0]] = [BOT_TREND_FOLLOWING[deployment[0]], "TRENDING", "TRENDING", False]
            
            #GRIDBOTS_TREND[deployment[0]] = "TRENDING"
            #DEPLOYED_BOTS[deployment[0]] = "TRENDING"
        elif deployment[1] == "RANGING":
            GRIDBOTS[deployment[0]] = [BOT_AGAINST_TREND[deployment[0]], "RANGING", "RANGING", False]
            
            #GRIDBOTS_TREND[deployment[0]] = "RANGING"
            #DEPLOYED_BOTS[deployment[0]] = "RANGING"

def chop_index_checker():
    
    for pair in PAIRS:
        curr = datetime.now()
        prev = datetime.now() - timedelta(hours=10)
        search_pair = str(pair).replace("_", "") 
        pair_ci = choppiness_index.Choppiness_Indicator(search_pair, prev, curr, TIMEFRAME, LOOKBACK)
        pair_ci_trend = pair_ci.compute_trend()
            
        if pair_ci_trend == GRIDBOTS[pair][2]:
            print(f"Trend hasn't changed. The {pair} bot is {pair_ci_trend}.")
            #DEPLOYED_BOTS_SWITCH[pair] = False
        else:
            print(f'Previous Trend was {GRIDBOTS[pair][1]}, and now it is {pair_ci_trend}. Changing the BOT DEPLOYMENT TREND')
            GRIDBOTS[pair][1], GRIDBOTS[pair][2], GRIDBOTS[pair][3] = pair_ci_trend, pair_ci_trend, True
            
            #DEPLOYED_BOTS[pair] = pair_ci_trend
            #GRIDBOTS_TREND[pair] = pair_ci_trend
            #DEPLOYED_BOTS_SWITCH[pair] = True

def check_reset_bot():
    
    for bot in GRIDBOTS:
        if GRIDBOTS[bot][3] == True:
            current_bot = BOT_TREND[GRIDBOTS[bot][2]][bot]
            GRIDBOTS[bot][0] = current_bot
            # Reset the Switch flag to False
            GRIDBOTS[bot][3] = False
            print(f'{bot} Bot Reset. Closing all positions and existing orders.')
            current_bot.cancel_all_existing_orders() 
            current_bot.cancel_all_existing_trigger_orders() 
            current_bot.close_all_positions()
            # RESETING BUY/SELL/CLOSED ORDERS. Since we are instatiating a new object these will be empty either way. 
            current_bot.CURRENT_BALANCE = round(current_bot.get_current_balance(), 2)
            current_bot.BUY_ORDERS = []
            current_bot.SELL_ORDERS = []
            current_bot.CLOSED_ORDERS = []
            current_bot.CLOSED_ORDERS_IDS = []
        else:
            print(f'{bot} Bot Switch Condition is False. Keeping current mode of operation.')


if __name__ == "__main__":
    
    #**************************************************
    # Populate Deployment List. (bot/trend) based on Chop Index. 
    populate_deployment_list()

    # Populate needed global variables for controlling the bot transitions.
    populate_global_var()

    for gridbot in GRIDBOTS:
    
        print(f" \n======== STARTING {GRIDBOTS[gridbot][2]} {gridbot} GRIDBOT ========")
        print(f" ======== STARTING BALANCE: ${GRIDBOTS[gridbot][0].STARTING_BALANCE} ======== ")
        GRIDBOTS[gridbot][0].CURRENT_BALANCE = round(GRIDBOTS[gridbot][0].get_current_balance(), 2)
        print(f' ======== CURRENT BALANCE: ${GRIDBOTS[gridbot][0].CURRENT_BALANCE} ======== ')
        print(" ======== Cancelling all existing orders! ========")
        GRIDBOTS[gridbot][0].cancel_all_existing_orders() 
        GRIDBOTS[gridbot][0].cancel_all_existing_trigger_orders() 
        GRIDBOTS[gridbot][0].close_all_positions()
        GRIDBOTS[gridbot][0].set_leverage()
        print(" ======== Proceeding to the Main Logic! ========")
    

    while True:
        # Note: Utilize multithreading so each thread is handling one gridbot instead of going through one at a time

        # Re-check Chop Index for each Pair Bot and see if there has been a change in Trend
        chop_index_checker()

        # If the Trend for a Pair has changed reset the bot for that pair. 
        check_reset_bot()
        
        for gridbot in GRIDBOTS:

            print(f" ********************************************** {GRIDBOTS[gridbot][2]} {gridbot} BOT ************************************************************ ")
            GRIDBOTS[gridbot][0].threshold_checker() 
            GRIDBOTS[gridbot][0].check_take_profit() 
            GRIDBOTS[gridbot][0].check_stop_condition()
            GRIDBOTS[gridbot][0].check_buy_orders()
            GRIDBOTS[gridbot][0].check_sell_orders()
            print(" ======== Checking for Open Limit Buy Orders! ======== ")
            GRIDBOTS[gridbot][0].check_open_buy_orders()
            #time.sleep(1)
            print(" ======== Checking for Open Limit Sell Orders! ======== ")
            GRIDBOTS[gridbot][0].check_open_sell_orders() 
            #time.sleep(1)
            print(" ======== Clearing Order Lists from Closed Orders! ======== ")
            GRIDBOTS[gridbot][0].clear_order_lists()
          


 


