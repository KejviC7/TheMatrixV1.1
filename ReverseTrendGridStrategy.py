import pandas as pd
import numpy as np
import config_auth
import ccxt
import sys


# Exchange Initialization
exchange = ccxt.gate({
    'apiKey': config_auth.API_KEY,
    'secret': config_auth.SECRET_KEY,
    "options": {
        'defaultType': 'swap'
    }
})

class configuration():
    def __init__(self, symbol, contract_size, num_buy_grid_lines, num_sell_grid_lines, grid_size):
        # Parameters
        self.SYMBOL = symbol
        self.CONTRACT_SIZE = contract_size
        # Gridbot Settings
        self.NUM_BUY_GRID_LINES = num_buy_grid_lines
        self.NUM_SELL_GRID_LINES = num_sell_grid_lines
        self.GRID_SIZE = grid_size
        

class ReverseGridStrategy(): 
    
    PARAMS = {"marginMode": "isolated"}
    STARTING_BALANCE = 1000
    CURRENT_BALANCE = None
    STOP_BALANCE = 1000
    TAKE_PROFIT_BALANCE = 1400


    def __init__(self, symbol, contract_size, num_buy_grid_lines, num_sell_grid_lines, grid_size, leverage):
        self.symbol = symbol
        self.contract_size = contract_size
        self.num_buy_grid_lines = num_buy_grid_lines
        self.num_sell_grid_lines = num_sell_grid_lines
        self.grid_size = grid_size
        self.LEVERAGE = leverage
        self.BUY_ORDERS = []
        self.SELL_ORDERS  = []
        self.CLOSED_ORDERS = []
        self.CLOSED_ORDERS_IDS = []
        self.THRESHOLD_POSITION = contract_size * num_buy_grid_lines
        self.config = configuration(self.symbol, self.contract_size, self.num_buy_grid_lines, self.num_sell_grid_lines, self.grid_size)
    
    def set_leverage(self):
        try:
            exchange.set_leverage(leverage=self.LEVERAGE, symbol = self.symbol)
            print(f" ==============  Set New Leverage of {self.symbol} to {self.LEVERAGE}. ====================")
        except:
            print(f" <<<<<<<<<<<<  UNABLE TO SET LEVERAGE TO {self.LEVERAGE}. ")
    
    def create_buy_orders(self):
        for i in range(self.config.NUM_BUY_GRID_LINES):
            try:
                _, ask_price = self.fetch_latest_prices()
            except:
                print(" \n<<<<<<<<<<<<<<<<  ERROR FETCHING THE LATEST BID/ASK PRICES! >>>>>>>>>>>>>>>>>>>>> ")
            price = ask_price - (self.config.GRID_SIZE * (i+1))
            print(f" ======== Submitting market limit buy order at ${price} ======== ")
            # Amount = 1 => actual size 0.01
            try:
                order = exchange.create_order(symbol=self.config.SYMBOL, type = "limit", side = "buy", amount = self.config.CONTRACT_SIZE, price = price, params = self.PARAMS)
            except:
                print(" \n<<<<<<<<<<<<<<<<  ERROR CREATING A LIMIT BUY ORDER! >>>>>>>>>>>>>>>>>>>>> ")
            #print(order)
            self.BUY_ORDERS.append(order)

    def create_sell_orders(self):
        for i in range(self.config.NUM_SELL_GRID_LINES):
            try:
                bid_price, _ = self.fetch_latest_prices()
            except:
                print(" \n<<<<<<<<<<<<<<<<  ERROR FETCHING THE LATEST BID/ASK PRICES! >>>>>>>>>>>>>>>>>>>>> ")
            price = bid_price + (self.config.GRID_SIZE * (i+1))
            print(f" ======== Submitting market limit sell order at ${price} ======== ")
            try:
                order = exchange.create_order(symbol=self.config.SYMBOL, type = "limit", side = "sell", amount = self.config.CONTRACT_SIZE, price = price, params=self.PARAMS)
            except:
                print(" \n<<<<<<<<<<<<<<<<  ERROR CREATING A LIMIT SELL ORDER! >>>>>>>>>>>>>>>>>>>>> ")
            self.SELL_ORDERS.append(order)

    def fetch_latest_prices(self):
        try:
            ticker = exchange.fetch_order_book(self.config.SYMBOL)
        except:
            print(" \n<<<<<<<<<<<<<<<<  ERROR FETCHING THE ORDER BOOK! >>>>>>>>>>>>>>>>>>>>> ")

        return float(ticker['bids'][0][0]), float(ticker['asks'][0][0])

    def cancel_all_existing_orders(self):
        try:
            exchange.cancel_all_orders(symbol=self.config.SYMBOL)
        except:
            print(" \n<<<<<<<<<<<<<<<<  ERROR CANCELLING ALL ORDERS! >>>>>>>>>>>>>>>>>>>>> ")
        
        return

    def cancel_all_existing_trigger_orders(self):
        try:
            exchange.cancel_all_orders(symbol=self.config.SYMBOL, params={'stop': True})
        except:
            print(" \n<<<<<<<<<<<<<<<<  ERROR CANCELLING ALL TRIGGER ORDERS! >>>>>>>>>>>>>>>>>>>>> ")
        
        return

    def check_buy_orders(self):
        if len(self.BUY_ORDERS) == 0:
            print(" ======== There are no buy orders currently. Creating the Buy Orders ======== ")
            self.create_buy_orders()
        else:
            print(' ======== Buy orders exist. Continue! ======== ')
        return 

    def check_sell_orders(self):
        if len(self.SELL_ORDERS) == 0:
            print(" ======== There are no sell orders currently. Creating the Sell Orders ======== ")
            self.create_sell_orders()
        else:
            print(' ======== Sell orders exist. Continue! ======== ')

    def check_open_buy_orders(self):
        for buy_order in self.BUY_ORDERS:
            print(f" ======== Checking Limit Buy Order {buy_order['info']['id']} ======== ")
            try:
                order = exchange.fetch_order(buy_order['id'])
            except:
                print(f" \n<<<<<<<<<<<<<<<<  ERROR CHECKING THE LIMIT BUY ORDER! {buy_order['info']['orderId']} >>>>>>>>>>>>>>>>>>>>> ")
                continue 

            if order['status'] == 'closed':
                self.CLOSED_ORDERS.append(order['info'])
                self.CLOSED_ORDERS_IDS.append(order['info']['id'])
                print(f" ======== Limit Buy Order was executed at {order['info']['price']} ======== ")
                #_, new_ask_price = self.fetch_latest_prices()
                new_sell_price = float(order['info']['price']) + self.config.GRID_SIZE
                print(f" ************** Creating New Limit Sell Order at {new_sell_price} ***************** ")
                try:
                    new_sell_order = exchange.create_order(symbol=self.config.SYMBOL, type = "limit", side = "sell", amount = self.config.CONTRACT_SIZE, price = new_sell_price, params = self.PARAMS)
                except:
                    print(" \n<<<<<<<<<<<<<<<<  ERROR CREATING A REPLACEMENT LIMIT SELL ORDER! >>>>>>>>>>>>>>>>>>>>> ")
                self.SELL_ORDERS.append(new_sell_order)
            

    def check_open_sell_orders(self):
        for sell_order in self.SELL_ORDERS:
            print(f" ======== Checking Limit Sell Order {sell_order['info']['id']} ========")
            try:
                order = exchange.fetch_order(sell_order['id'])
            except:
                print(f" \n<<<<<<<<<<<<<<<<  ERROR CHECKING THE LIMIT SELL ORDER! {sell_order['info']['orderId']} >>>>>>>>>>>>>>>>>>>>> ")
                continue 
            #print(order)
            if order['status'] == 'closed':
                self.CLOSED_ORDERS.append(order['info'])
                self.CLOSED_ORDERS_IDS.append(order['info']['id'])
                print(f" ======== Limit Sell Order was executed at {order['info']['price']} ========")
                #new_bid_price, _ = self.fetch_latest_prices()
                new_buy_price = float(order['info']['price']) - self.config.GRID_SIZE
                print(f" ************** Creating New Limit Buy Order at {new_buy_price} *************** ")
                try:
                    new_buy_order = exchange.create_order(symbol=self.config.SYMBOL, type = "limit", side = "buy", amount = self.config.CONTRACT_SIZE, price = new_buy_price, params = self.PARAMS)
                except:
                    print(" \n<<<<<<<<<<<<<<<<  ERROR CREATING A REPLACEMENT LIMIT BUY ORDER! >>>>>>>>>>>>>>>>>>>>> ")
                self.BUY_ORDERS.append(new_buy_order)

    def send_data():
        # Concatenate 3 order lists and send as jsonified
        #ws.send(json.dumps(BUY_ORDERS + SELL_ORDERS + CLOSED_ORDERS))
        return

    def clear_order_lists(self):
        #global BUY_ORDERS
        #global SELL_ORDERS
        for order_id in self.CLOSED_ORDERS_IDS:
            self.BUY_ORDERS = [buy_order for buy_order in self.BUY_ORDERS if buy_order['info']['id'] != order_id]
            self.SELL_ORDERS = [sell_order for sell_order in self.SELL_ORDERS if sell_order['info']['id'] != order_id]
        return
    
    def get_current_balance(self):
        try:
            current_bal = exchange.fetch_balance()['USDT']['total']
        except:
            print(" \n<<<<<<<<<<<<<<<<  ERROR FETCHING THE BALANCE! >>>>>>>>>>>>>>>>>>>>> ")
        
        return current_bal

    def check_take_profit(self):
        if self.CURRENT_BALANCE > self.TAKE_PROFIT_BALANCE:
            print("======== TAKE PROFIT REACHED! Closing all Positions and Open Orders")
            self.cancel_all_existing_orders() 
            self.close_all_positions()
            print("======== THE GRID BOT WILL RESTART SOON ========")
            return
        else:
            print(" ======== TAKE PROFIT CONDITION NOT MET YET. GRIDBOT STILL RUNNING ========")
            return 

    def check_stop_condition(self):
        if self.CURRENT_BALANCE < self.STOP_BALANCE:
            print("======== STOP LOSS REACHED. Closing all Positions and Open Orders")
            self.cancel_all_existing_orders()
            self.close_all_positions()
            print(" ======== SHUTTING DOWN THE GRIDBOT =========")
            sys.exit()
        else:
            print(" ======== STOP CONDITION NOT MET YET. GRIDBOT STILL RUNNING ========")
            return

    def fetch_position(self):
        try:
            positions = exchange.fetch_positions()
        except:
            print(" \n<<<<<<<<<<<<<<<<  ERROR FETCHING THE POSITION! >>>>>>>>>>>>>>>>>>>>> ")
        for position in positions:
            if position['info']['contract'] == self.config.SYMBOL:
                return position['side'], float(position['contracts']) 


    def close_all_positions(self):
        # Get current position
        pos_side, size = self.fetch_position()
        bid, ask = self.fetch_latest_prices()
        if pos_side == 'long':
        
            try:
                exchange.create_order(symbol=self.config.SYMBOL, type = "limit", side = 'short', amount = 0, price = 0.99 * ask, params = {"marginMode": "isolated", "close": True})
            except:
                print(" \n<<<<<<<<<<<<<<<<  ERROR CREATING A LIMIT SELL ORDER TO CLOSE ALL POSITIONS! >>>>>>>>>>>>>>>>>>>>> ")
            
        elif pos_side == "short":
            try:
                exchange.create_order(symbol=self.config.SYMBOL, type = "limit", side = 'long', amount = 0, price = 1.01 * ask, params = {"marginMode": "isolated", "close": True})
            except:
                print(" \n<<<<<<<<<<<<<<<<  ERROR CREATING A LIMIT BUY ORDER TO CLOSE ALL POSITIONS! >>>>>>>>>>>>>>>>>>>>> ")
        else:
            print(" ======== THERE WERE NO OPEN POSITIONS ================ ")
        
        return

    def threshold_checker(self):
    
        '''
        We check if the current open position is not oversized.
        An oversized position can lead to significant losses if the trend continues. 
        Therefore, it is important to have some threshhold in place in order to close/reduce the position and refresh the orders.
        '''

        #global BUY_ORDERS, SELL_ORDERS
        # Get current position
        pos_side, size = self.fetch_position()
        if size > self.THRESHOLD_POSITION:
            print(" \n========== Grid Bot is currently in an oversized {pos_side} position. Closing the Position and refreshing the orders. ===========")
            self.close_all_positions()
            self.cancel_all_existing_orders()
            self.BUY_ORDERS = []
            self.SELL_ORDERS = []
        
        return