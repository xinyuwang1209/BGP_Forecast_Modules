#! /usr/bin/env python3

import numpy as np
import pandas as pd
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
# Import Utilities
from ..Utilities.Database import *
from ..Utilities.Utilities import *


def mrt2dataframe(mrt):

    return df

dir = '/tmp/mrts/'
if not os.path.exists(dir):
    os.makedir(dir)

# def get_mrtfile_urls():

params = {'human': True,
          'intervals': ','.join(start, end),
          'types': ['ribs']
}

mrt_announcements = None
from BGP_Forecast_Modules import *
ins = BGP_Forecast_Modules()
roas4, roas6 = ins.BGP_Forecast_Moduels.ROAs_Collector.get_ROAs_df()

url = "https://bgpstream.caida.org/broker/data?human&intervals[]=1438819200,1438819200&types[]=ribs"
html = requets.get(url)

mrts = pd.DataFrame(html.json()['data']['dumpFiles'])
mrts.drop_duplicates(subset=['url'])


# Multithreading:

mrts['url'][0]

start_time = time.time()
pool = ThreadPool(mrts.shape[0])
results = pool.map(parse_file,mrts['url'].apply(lambda x: x + '////' + dir))
pool.close()
pool.join()
print(time.time()-start_time)



start_time = time.time()
df = pd.DataFrame()
count = 0
for result in results:
    print(count)
    count += 1
    df = pd.concat([df,result],axis=0)
    df = df.sort_values(by=['first_seen'])
    df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)

print(time.time()-start_time)

start_time = time.time()
df = pd.concat(results,axis=0)
df2 = df.copy(deep=True)
print('concat complete')
df = df.sort_values(by=['first_seen'])
print('sort complete')
df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
print(time.time()-start_time)


def parse_file(string):
    file_url, dir = string.split('////')
    compressed_path = dir + file_url.split('/')[-1]
    print(compressed_path)
    # url = "https://bgpstream.caida.org/broker/data?human&intervals[]=1438819200,1438819200&collectors[]=route-views2&types[]=ribs"
    wget.download(file_url, compressed_path)
    # os.system('bgpscanner /tmp/mrts/bview.20150806.0000.gz > /tmp/mrts/bview.20150806.0000')
    # Run bgp scanner
    pool = pathos.multiprocessing.ProcessingPool(8).map
    file_path = '.'.join(compressed_path.split('.')[:-1])
    cmd = "export LD_LIBRARY_PATH=/usr/local/lib;bgpscanner " + compressed_path + " > " + file_path
    os.system(cmd)
    df = pd.read_csv(file_path,sep='|',header=None)
    df = df[[1,2,9]]
    df.rename(columns={1:'prefix',2:'as_path',9:'first_seen'}, inplace=True)
    df = df.loc[~df['as_path'].isnull()]
    df['origin'] = df['as_path'].apply(lambda x: x.split(' ')[-1])
    df['prefix'] = df['prefix'].apply(ipaddress.ip_network)
    df = df.sort_values(by=['first_seen'])
    df.drop_duplicates(subset=['prefix','origin','as_path'],inplace=True)
    return df
    # df['as_path'] = df['as_path'].apply(as_path2lst)

def as_path2lst(string):
    return string.split(' ')

def get_origin(lst):
    return lst[-1]
