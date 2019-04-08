import time
import datetime
import random
import pandas as pd
import numpy as np
from .Database import Database as DB



import pathos
import signal
import sys
import os
import time

# redefine process pool via inheritance
import multiprocess.context as context
class NoDaemonProcess(context.Process):
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

class NoDaemonPool(pathos.multiprocessing.Pool):
    def Process(self, *args, **kwds):
        return NoDaemonProcess(*args, **kwds)

def get_pid_i(x):
    return os.getpid()
def hard_kill_pool(pid_is, pool):
    for pid_i in pid_is:
        os.kill(pid_i, signal.SIGINT)  # sending Ctrl+C
    pool.terminate()

def myproc(args):
    i, max_workers = args
    l_args = [j for j in range(i)]
    mysubproc = lambda x : x
    pool = pathos.pools.ProcessPool(max_workers)
    pool.restart(force=True)
    pid_is = pool.map(get_pid_i, range(max_workers))
    try:
        l_traj_df = pool.amap(mysubproc, l_args)
        counter_i = 0
        while not l_traj_df.ready():
            time.sleep(1)
            if counter_i % 30 == 0:
                print('Waiting for children running in pool.amap() in myproc( {} ) with PIDs: {}'.format(i, pid_is))
            counter_i += 1
        l_traj_df = l_traj_df.get()
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print('Ctrl+C received in myproc( {} ), attempting to terminate pool...').format(myens)
        hard_kill_pool(pid_is, pool)  # sending Ctrl+C
        raise
    except:
        print('Attempting to close parallel after exception: {} in myproc( {} )'.format(sys.exc_info()[0], myens))
        hard_kill_pool(pid_is, pool)  # sending Ctrl+C
        raise






def get_network_version(prefix):
    return prefix.version



def random_prefix_generator():
    random_prefix = '/' + str(random.randint(0,32))
    for j in range(4):
        random_prefix = '.' + str(random.randint(0,255))  + random_prefix
    return random_prefix[1:]

def random_asn_generator():
    return random.randint(0,1000000)

def random_boolean_generator():
    return random.random() < 0.5

def time_parser(str):
    seconds = 0
    minutes = 0
    hours     = 0
    days     = 0
    weeks     = 0
    for element in str.split(":"):
        if element[-1] == 's':
            seconds = int(element[:-1])
        if element[-1] == 'm':
            minutes = int(element[:-1])
        if element[-1] == 'h':
            hours = int(element[:-1])
        if element[-1] == 'd':
            days = int(element[:-1])
        if element[-1] == 'w':
            weeks = int(element[:-1])
    return [seconds, minutes, hours, days, weeks]

def time_parser_datetime(str):
    [seconds, minutes, hours, days, weeks] = time_parser(str)
    return datetime.timedelta(
                            seconds=seconds,
                            minutes=minutes,
                            hours=hours,
                            days=days,
                            weeks=weeks
                            )

def time_parser_epoch(str):
    [seconds, minutes, hours, days, weeks] = time_parser(str)
    days = days + weeks * 7
    hours = hours + days * 24
    minutes = minutes + hours * 60
    seconds = seconds + minutes * 60
    return seconds

def random_epoch_generator():
    return random.randint(0, 2147483648)

def random_prefix_origin_generator(nrows,has_asn=False,fix_asn=None,special_one=False):
    # Generate random DataFrame
    df = pd.DataFrame()
    if has_asn:
        df['asn'] = 0
    df['prefix'] = 0
    df['origin'] = 0
    if has_asn:
        df['received_from_asn'] = 0
    df['invalid_length'] = 0
    df['invalid_asn'] = 0
    df['time'] = 0
    df['decision_1'] = 0
    df['decision_2'] = 0
    df['decision_3'] = 0
    df['decision_4'] = 0

    for i in range(nrows):
        row = []
        if has_asn:
            if fix_asn == None:
                random_asn = random_asn_generator()
            else:
                random_asn = fix_asn
            row.append(random_asn)
        random_prefix = random_prefix_generator()
        row.append(random_prefix)
        random_origin = random_asn_generator()
        row.append(random_origin)
        if has_asn:
            random_received_from_asn = random_asn_generator()
            row.append(random_received_from_asn)
        random_invalid_length = random_boolean_generator()
        row.append(random_invalid_length)
        random_invalid_asn = random_boolean_generator()
        row.append(random_invalid_asn)
        random_time = random_epoch_generator()
        row.append(random_time)
        decision_1 = None
        row.append(decision_1)
        decision_2 = None
        row.append(decision_2)
        decision_3 = None
        row.append(decision_3)
        decision_4 = None
        row.append(decision_4)

        df.loc[i] = row
    df = df.loc[(df['invalid_asn'] == True) | (df['invalid_length'] == True)]
    df.loc[nrows] = [21472,'11.11.11.11/32',13335,1234,1,1,100,None,None,None,None]
    return df

def print_time(*args):
    print(str(datetime.datetime.now())[:-7],*args)
    return

if __name__ == "__main__":
    print(random_prefix_generator())
    print(random_asn_generator())
    print(random_boolean_generator())

    # Test Time_Parser
    time_shift = "520w:1h:1s"
    print(time_parser_epoch(time_shift))
    time_current = time.time()
    print(datetime.datetime.fromtimestamp(time_current))
    print(datetime.datetime.fromtimestamp(time_current - time_parser_epoch(time_shift)))
    print(time_parser_datetime(time_shift))

    print(random_prefix_origin_generator(1,has_asn=True,fix_asn=13335,special_one=True))
