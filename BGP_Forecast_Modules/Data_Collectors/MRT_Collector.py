#! /usr/bin/env python3

import os
import wget
import time
import math
import requests
import datetime
import ipaddress
import numpy as np
import pandas as pd
import pathos
import multiprocessing
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
# # Import Utilities
# from ..Utilities.Database import *
# from ..Utilities.Utilities import *




def parse_file(string):
    file_url, file_refix, memory_dir = string.split('////')
    compressed_path = memory_dir + file_refix + file_url.split('/')[-1]
    print(file_url)
    # url = "https://bgpstream.caida.org/broker/data?human&intervals[]=1438819200,1438819200&collectors[]=route-views2&types[]=ribs"
    wget.download(file_url, compressed_path)
    # os.system('bgpscanner /tmp/mrts/bview.20150806.0000.gz > /tmp/mrts/bview.20150806.0000')
    # Run bgp scanner
    # pool = pathos.multiprocessing.ProcessingPool(8).map
    file_path = '.'.join(compressed_path.split('.')[:-1])
    cmd = "export LD_LIBRARY_PATH=/usr/local/lib;bgpscanner " + compressed_path + " > " + file_path
    os.system(cmd)
    # Delete compressed file
    if os.path.exists(compressed_path):
        os.remove(compressed_path)
    df = pd.read_csv(file_path,sep='|',header=None,low_memory=False)
    # Delete decompressed file
    if os.path.exists(file_path):
        os.remove(file_path)
    df = df[[1,2,9]]
    df.rename(columns={1:'prefix',2:'as_path',9:'first_seen'}, inplace=True)
    df = df.loc[~df['as_path'].isnull()]
    df['origin'] = df['as_path'].apply(lambda x: x.split(' ')[-1])
    df['prefix'] = df['prefix'].apply(ipaddress.ip_network)
    df = df.sort_values(by=['first_seen'])
    df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
    return df


def thread_worker(lst):
    pool = ThreadPool(len(lst))
    results = pool.map(parse_file,lst)
    pool.close()
    pool.join()
    results = [pd.DataFrame(lst_dict) for lst_dict in results]
    df = pd.concat(results,axis=0)
    df = df.sort_values(by=['first_seen'])
    df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
    return df





#
# mrt_announcements = None
# from BGP_Forecast_Modules import *
# ins = BGP_Forecast_Modules()
# roas4, roas6 = ins.BGP_Forecast_Moduels.ROAs_Collector.get_ROAs_df()


def get_mrt_announcements():
    memory_dir = '/dev/shm/mrts/'
    if not os.path.exists(memory_dir):
        os.mkdir(memory_dir)
    #
    #
    # def get_mrtfile_urls():
    url = "https://bgpstream.caida.org/broker/data"
    #
    mrts = pd.DataFrame()
    end = int(datetime.datetime.now().timestamp())
    start = end
    for i in range(24):
        start = start - 3600
        params = {'human': True,
                  'intervals': ','.join([str(start), str(end)]),
                  'types': ['ribs']
        }
        html = requests.get(url,params=params)
        current = pd.DataFrame(html.json()['data']['dumpFiles'])
        current.drop_duplicates(subset=['url'],inplace=True)
        mrts = pd.concat([mrts, current], axis=0)
        mrts.drop_duplicates(subset=['url'],inplace=True)
    #
    #
    mrts.reset_index(drop=True,inplace=True)
    mrts['url'].apply(lambda x: x.split('/')[-1])
    for i in range(mrts.shape[0]):
        mrts.loc[i,'url'] = mrts.loc[i,'url'] + '////px' + str(i) + '////' + memory_dir
    #
    #
    start_time = time.time()
    urls = mrts['url'].to_list()
    ncpu = multiprocessing.cpu_count()
    chunk_size = math.ceil(len(urls)/ncpu)
    urls = [urls[i:i+chunk_size] for i in range(0, len(urls), chunk_size)]
    pool = pathos.multiprocessing.ProcessingPool(8).map
    results = pool(thread_worker,urls,chunksize=1)
    print(time.time()-start_time)
    #
    #
    start_time = time.time()
    df = pd.concat(results,axis=0)
    print('concat complete')
    df = df.sort_values(by=['first_seen'])
    print('sort complete')
    df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
    print(time.time()-start_time)
    return df

# start_time = time.time()
# df = pd.DataFrame()
# count = 0
# for results in results:
#     print(count)
#     count += 1
#     df = pd.concat([df,result],axis=0)
#     df = df.sort_values(by=['first_seen'])
#     df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
#
# print(time.time()-start_time)
#
