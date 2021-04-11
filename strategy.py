class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Bitfinex': {
                'pairs': ['BTC-USDT'], 
            },
        }
        self.period = 10 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([]) 
        self.ma_long = 20  ##
        self.ma_short = 5  ##
        self.UP = 1   
        self.DOWN = 2

    def on_order_state_change(self,  order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1] 
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]

        rsi_score = talib.RSI(self.close_price_trace)[-1]   

        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if rsi_score < 30 and s_ma > l_ma:
            return self.UP
        elif rsi_score > 70 and s_ma < l_ma:
            return self.DOWN

    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0] #exchange交易所 
        pair = list(information['candles'][exchange])[0] #(candles:k線資訊)交易對pair
        target_currency = pair.split('-')[0]  #ETH 當前可操作的貨幣
        base_currency = pair.split('-')[1]  #USDT
        base_currency_amount = self['assets'][exchange][base_currency] 
        target_currency_amount = self['assets'][exchange][target_currency] 
        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']

        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]

        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()
        if cur_cross is None:
            return []
        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []
        # cross up
        if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange, #此筆訂單要向哪個交易所進行交易 
                    'amount': 1, #要交易的數位貨幣數量
                    'price': -1, #多少價格進行交易 採用市價
                    'type': 'MARKET', #交易方式
                    'pair': pair, #交易貨幣對
                }
            ]
                #  Example[
                # {
                #     'exchange': 'Binance',
                #     'pair': 'ETH-USDT',
                #     'type': 'LIMIT',
                #     'amount': 1,
                #     'price': 212.42
                # }
                # ]
        # cross down
        elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -target_currency_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []