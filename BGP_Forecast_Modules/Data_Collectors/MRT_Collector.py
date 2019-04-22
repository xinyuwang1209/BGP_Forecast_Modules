#! /usr/bin/env python3

import os
import wget
import time
import requests
import datetime
import numpy as np
import pandas as pd
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










def get_mrt_announcements():

mrt_announcements = None
from BGP_Forecast_Modules import *
ins = BGP_Forecast_Modules()
roas4, roas6 = ins.BGP_Forecast_Moduels.ROAs_Collector.get_ROAs_df()


memory_dir = '/dev/shm/mrts/'
if not os.path.exists(memory_dir):
    os.mkdir(memory_dir)


# def get_mrtfile_urls():
url = "https://bgpstream.caida.org/broker/data"

mrts = pd.DataFrame()
end = int(datetime.datetime.now().timestamp())
start = end
for i in range(12):
    start = start - 7200
    params = {'human': True,
              'intervals': ','.join([str(start), str(end)]),
              'types': ['ribs']
    }
    html = requests.get(url,params=params)
    current = pd.DataFrame(html.json()['data']['dumpFiles'])
    current.drop_duplicates(subset=['url'],inplace=True)
    mrts = pd.concat([mrts, current], axis=0)
    mrts.drop_duplicates(subset=['url'],inplace=True)


mrts.reset_index(drop=True,inplace=True)
mrts['url'].apply(lambda x: x.split('/')[-1])

for i in range(mrts.shape[0]):
    mrts.loc[i,'url'] = mrts.loc[i,'url'] + '////px' + str(i) + '////' + memory_dir
# Multithreading:
# mrts = mrts.iloc[:10,:]

start_time = time.time()
pool = ThreadPool(mrts.shape[0])
results = pool.map(parse_file,mrts['url'])
pool.close()
pool.join()
print(time.time()-start_time)



# start_time = time.time()
# df = pd.DataFrame()
# count = 0
# for result in results:
#     print(count)
#     count += 1
#     df = pd.concat([df,result],axis=0)
#     df = df.sort_values(by=['first_seen'])
#     df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
#
# print(time.time()-start_time)
#


start_time = time.time()
df = pd.concat(results,axis=0)
df2 = df.copy(deep=True)
print('concat complete')
df = df.sort_values(by=['first_seen'])
print('sort complete')
df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
print(time.time()-start_time)
