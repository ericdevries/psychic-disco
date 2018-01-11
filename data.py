import pandas as pd
import numpy as np
import os
import random


def getLinearData():
    seed = 1
    files = os.listdir('day')

    currencies = {}

    for f in files:
        data = pd.read_json('day/%s' % f)
        data['date'] = pd.to_datetime(data['T'])
        data = data.set_index('date')

        del data['T']

        currencies[f] = data


    df = pd.Panel(currencies)
    df = df.fillna(method='ffill')
    df = df.fillna(0)

    df['btc'] = df['btc.json']
    df['btc.json'] = 1

    return df
