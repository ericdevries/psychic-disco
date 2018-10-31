import urllib.parse
import requests
import json

def fetch_currency(market):
    url = 'https://bittrex.com/Api/v2.0/pub/market/GetTicks'
    args = {
            'marketName': market,
            'tickInterval': 'day',
    }

    url = url + '?' + urllib.parse.urlencode(args)

    data = requests.get(url)
    currency = market.split('-')[1]

    with open('per_day/{}.json'.format(currency), 'w') as f:
        f.write(json.dumps(data.json()['result']))

def fetch_markets():
    data = requests.get('https://bittrex.com/api/v1.1/public/getmarkets')
    data = data.json()
    
    results = []

    for row in data['result']:
        if row['BaseCurrency'] == 'BTC' or row['MarketCurrency'] == 'BTC':
            results.append(row['MarketName'])

    return results

markets = fetch_markets()

for m in markets:
    print('fetching: {}'.format(m))
    fetch_currency(m)



