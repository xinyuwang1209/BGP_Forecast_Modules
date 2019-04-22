#! /usr/bin/env python3

import os
import sys
import copy
import json
import time
import math
import random
import pathos
import numpy as np
import pandas as pd
import datetime
import requests
import multiprocessing
from queue import Queue
from threading import Thread
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

# Import Utilities
from ..Utilities.Database import *
from ..Utilities.Utilities import *


def get_hijacks(mode='multithreading'):
    url = "https://bgpstream.com"
    html = requests.get(url)
    texts = html.text.split('''<td class="event_type">Possible''')[1:]
    print_time("Size of Hijack:",len(texts))
    urls = []
    for text in texts:
        href = text.split('''<a href="''')[1].split('''"''')[0]
        end_time = text.split('''<td class="endtime">\n\t\t  \t ''')[1].split('\n')[0]
        urls.append('////'.join([url + href, end_time]))
    # Single Core
    # result = []
    # for string in lst:
    #     result.append(get_hijack(string))
    if mode == 'multiprocessing':
        # Multiprocessing
        ncpu = multiprocessing.cpu_count()
        chunk_size = math.ceil(len(urls)/ncpu)
        urls = [urls[i:i+chunk_size] for i in range(0, len(urls), chunk_size)]
        print(len(urls))
        pool = pathos.multiprocessing.ProcessingPool(8).map
        result = pool(thread_worker,urls,chunksize=1)
        result = [pd.DataFrame(lst_dict) for lst_dict in result]
        df = pd.concat(result,axis=0)
    elif mode == 'multithreading':
        # Multithreading
        pool = ThreadPool(128)
        result = pool.map(get_hijack,urls)
        pool.close()
        pool.join()
        df = pd.DataFrame(result)
    return df

def thread_worker(lst):
    print_time('work starts')
    pool = ThreadPool(len(lst))
    result = pool.map(get_hijack,lst)
    pool.close()
    pool.join()
    return result

def get_hijack(string):
    # print_time(string)
    url,end_time = string.split('////')
    # print_time(url)
    # print_time(end_time)
    if end_time == ' ':
        end_time = None
    else:
        # Convert to struct_time
        end_time = time.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        # Convert to epoch
        end_time = int(time.mktime(end_time))
        #
    # print_time(end_time)
    html = requests.get(url)
    while html.status_code == 404:
        time.sleep(0.1)
        html = requests.get(url)
    # Get start_time string
    start_time = html.text.split("Start time: ")[1].split('<')[0]
    # print_time(start_time)
    # Convert to struct_time
    start_time = time.strptime(start_time, "%Y-%m-%d %H:%M:%S %Z")
    # print_time(start_time)
    # Convert to epoch
    start_time = int(time.mktime(start_time))
    # print_time(start_time)
    prefix = html.text.split("Detected advertisement: ")[1].split("<")[0]
    # print_time(prefix)
    origin = html.text.split("Detected Origin ASN ")[1].split(" <")[0].split(' ')[0]
    # print_time(origin)
    return {'prefix': prefix,
            'origin': origin,
            'start_time': start_time,
            'end_time':end_time,
            'url': url}

start_time = time.time();df = get_hijacks();print(time.time()-start_time)
