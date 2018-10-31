import pandas as pd
import numpy as np
import os
import random


def getLinearData():
    seed = 1
    files = os.listdir('per_day')

    currencies = {}

    for f in files:
        data = pd.read_json('per_day/%s' % f)

        if 'T' not in data:
            continue

        data['date'] = pd.to_datetime(data['T'])
        data = data.set_index('date')

        del data['T']
        
        currencies[f.lower()] = data


    df = pd.Panel(currencies)
    df = df.fillna(method='ffill')
    df = df.fillna(0)

    df['btc'] = df['btc.json']
    df['btc.json'] = 1

    return df
