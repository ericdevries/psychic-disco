import data
import matplotlib.pyplot as plt

def doBacktest(startDate, endDate, currencyFilter=None):
    records = data.getLinearData()

    bitcoinusd = records['btc']
    del records['btc']

    currencies = records.items

    if currencyFilter:
        currencies = [c + '.json' for c in currencyFilter]

    records = records.swapaxes(0, 1)
    records = records[startDate:endDate]
    bitcoinusd = bitcoinusd[startDate:endDate]
    date = records.items[-1]

    balancer = Balancer(currencies, bitcoinusd)
    balancer.balance(records)

    return balancer, date

CURRENCIES = ['btc', 'ltc', 'eth', 'dash', 'xmr', 'xrp']
DATE = '2017-07-01'

class Balancer():

    def __init__(self, currencies, btc, amount=1):
        self.values = { k: 0 for k in currencies }
        self.buyandhold = { k: 0 for k in currencies }
        self.fee = 0.9975
        self.cutoff = 1.1
        self.btc = btc
        self.amount = amount
        self.data = None
        self.buyin = 0.99
        self.selloff = 1.01
        self.sellamount = 1 # 0 - 1
        self.currencies = currencies

        self.buyorders = []
        self.sellorders = []
        self.orders = 0
        self.failedorders = 0

        self.performance = { k: 0 for k in currencies }
        self.worth = []
        self.buyandholdworth = []


    def getTotalBitcoinBalance(self, prices):
        total = 0

        for k, v in prices['C'].iteritems():
            if v > 0 and k in self.values:
                price = v
                total += v * self.values[k]

        return total


    def handleSellOrders(self, date, frame):
        bitcoin = 0

        for currency, amount, price in self.sellorders:
            if price <= frame.loc[currency, 'H']:
                self.values[currency] -= amount
                bitcoin += (price * amount * self.fee)
                self.orders += 1
                self.debug('sold %s %s at %s' % (amount, currency, price,))
                #self.performance[currency] += (price * amount * self.fee * btcusd)

            else:
                self.failedorders += 1

        # cancel remaining orders
        self.sellorders = []

        return bitcoin


    def handleBuyOrders(self, date, frame):
        bitcoin = 0

        for currency, amount, price in self.buyorders:
            if price >= frame.loc[currency, 'L']:
                self.values[currency] += (amount * self.fee)
                bitcoin += (price * amount)
                self.orders += 1

                self.debug('bought %s %s at %s' % (amount, currency, price,))
                #self.performance[currency] -= (price * amount * btcusd)
            else:
                self.failedorders += 1

        # cancel remaining orders
        self.buyorders = []

        return bitcoin


    def balanceFrame(self, date, frame, nextFrame):
        # calculate total holdings
        total = self.getTotalBitcoinBalance(frame)
        tradeable = 0

        gained = self.handleSellOrders(date, frame)
        sold = self.handleBuyOrders(date, frame)

        self.values['btc.json'] += (gained - sold)

        shares = []
        bitcoin = 0

        for k, v in frame['C'].iteritems():
            if v == 0 or k not in self.values:
                continue

            share = v * self.values[k] / total
            shares.append((k, share, v,))

            tradeable += 1

        target = 1 / tradeable

        # 0 = lowest share
        shares = sorted(shares, key=lambda x: x[1])

        for currency, share, price in shares:
            if currency not in self.currencies:
                continue

            cutoff = self.cutoff
            # check if we have too much of this one
            if share > (target * cutoff):
                price = price * self.selloff
                perc = (share - target) / share
                sell = self.values[currency] * perc * self.sellamount

                if currency == 'btc.json':
                    bitcoin = sell
                else:
                    self.sellorders.append((currency, sell, price,))

        # now buy some other shitcoin
        if bitcoin > 0:
            for currency, share, price in shares:
                if currency == 'btc.json':
                    continue

                price = price * self.buyin

                amount = 0

                if share > 0:
                    amount = ((target / share) - 1) * self.values[currency]
                else:
                    amount = (target * total) / price

                if amount > 0:
                    if amount * price > bitcoin:
                        amount = bitcoin / price

                    bitcoin -= (amount * price)

                    # if self.values[currency] == 0:
                    #     self.debug('currency %s is now tradable on %s' % (currency, date,))

                    self.buyorders.append((currency, amount, price,))

                    # if currency == 'ltc.json':
                    #     self.debug('buying %s ltc out of %s for price %s, share is %s' % (sell, self.values[currency], price, share,))

                    if bitcoin < 0.0001:
                        break

        btcusd = self.btc.loc[date, 'C']
        total = 0
        totalbh = 0

        for k, v in frame['C'].iteritems():
            if v == 0 or k not in self.values:
                continue

            total += (v * self.values[k] * btcusd)

        for k, v in frame['C'].iteritems():
            if v == 0 or k not in self.buyandhold:
                continue

            totalbh += (v * self.buyandhold[k] * btcusd)

        self.worth.append(total)
        self.buyandholdworth.append(totalbh)

    def initPortfolio(self, frame):
        tradeable = 0

        for currency, f in frame.iterrows():
            if f['C'] > 0 and currency in self.currencies:
                tradeable += 1

        target = 1 / tradeable

        for currency, f in frame.iterrows():
            if f['C'] > 0 and currency in self.currencies:
                self.values[currency] = (target * self.amount) / f['C']
                self.debug('set %s to have %s coins' % (currency, self.values[currency]))

        self.buyandhold = self.values.copy()

    def balance(self, data):
        lastFrame = None
        lastDate = None

        # make the date the primary item
        self.data = data

        for date, row in data.iteritems():
            self.orders = 0
            self.failedorders = 0

            if lastFrame is None:
                self.initPortfolio(row)
            else:
                self.balanceFrame(lastDate, lastFrame, row)

            lastFrame = row
            lastDate = date

            total = self.getTotalBitcoinBalance(row)

            self.debug('total value in btc: %s - %s orders (%s failed)' % (total, self.orders, self.failedorders,))

        prices = lastFrame
        total = 0

        for k, v in self.buyandhold.items():
           # import pdb; pdb.set_trace()
            price = v * prices.loc[k, 'C']
            total += price

        self.buyandholdResult = total


    def printValues(self, date):
        btc = self.btc.loc[date, 'C']
        prices = self.data[date, :, 'C']
        total = 0

        for k, v in self.values.items():
            price = prices[k]
            amount = price * v * btc
            total += amount

            #print('%s \t - %s' % (k, v))

        print('(%s, %s, %s, %s) -> grand total: %s (bh: %s)' % (self.cutoff, self.selloff, self.buyin, self.sellamount, total, self.buyandholdResult*btc,))

        #self.printPerformance(date)

        #import pdb; pdb.set_trace()

    def printPerformance(self, date):
        btc = self.btc.loc[date, 'C']

        results = self.performance.items()
        results = sorted(results, key=lambda x: x[1])

        for r in results:
            print('%s \t %s' % r)

        print('total: %s' % sum([x[1] for x in results]))

    def debug(self, text):
        if False:
            print(text)



if __name__ == '__main__':
    balancer, date = doBacktest('2017-07-01', '2017-12-31', ['btc', 'xmr', 'ltc', 'xrp', 'xlm', 'eth', 'dash', 'neo'])
    balancer.printValues(date)


    balancer = Balancer(currencies, bitcoinusd)
    balancer.balance(records)
    balancer.printValues(date)

    plt.plot(balancer.worth, color='blue')
    plt.plot(balancer.buyandholdworth, color='red')
    plt.show()

