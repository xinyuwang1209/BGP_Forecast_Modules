#!/usr/bin/env python3

import os
import sys
import time
import pathos
import pandas as pd
import multiprocessing
from multiprocessing import Manager
import numpy as np
import ipaddress as ip
import psycopg2
import subprocess
import configparser
from psycopg2.extras        import RealDictCursor
from .ROAs_Collector        import ROAs_Collector
from .Conflict_Identifier   import Conflict_Identifier
from .Prefix_Origin 		import Prefix_Origin
from .Conflict_Classifier 	import Conflict_Classifier
from .What_If_Analysis 	    import What_If_Analysis
# from .Database              import Database as db
from .Utilities             import *


class What_If_Analysis_Evaluator():
    def __init__(self,config,debug=False):
        self.config = config

        # Initialize each module
        self.ROAs_Collector         = ROAs_Collector(self.config)
        self.Conflict_Identifier    = Conflict_Identifier(self.config)
        self.Prefix_Origin          = Prefix_Origin(self.config)
        self.Conflict_Classifier    = Conflict_Classifier(self.config)
        self.What_If_Analysis       = What_If_Analysis(self.config)
        self.debug = debug


    def run_rpki_validator(self):
        # subprocess.Popen("bash /opt/rpki-validator/blabla")
        pass

    def run_Conflict_Identifier(self,asn,table_source,table):
        self.Conflict_Identifier.init_prefix_origin_table(asn=asn,table=table_source,table_new=table)
        self.Conflict_Identifier.alter_prefix_origin_columns(asn=asn,table=table)
        # self.Conflict_Identifier.split_prefix_origin(asn=asn,table=table)
        # self.Conflict_Identifier.drop_prefix_origin(asn=asn,table=table_prefix_origin_asn)
        self.Conflict_Identifier.create_index(asn=asn,table=table,prefixorigin=False)
        # self.Conflict_Identifier.create_index(asn=asn,table=table,prefixorigin=True)
        return

    def run_Prefix_Origin(self,table):
        if int(self.config['DEFAULT']['validity']) == 1:
            self.Prefix_Origin.update_prefix_origin_validity(table=table)
        else:
            print('-------------------------not suppose-------------------------')
            self.Prefix_Origin.update_invalid_length(table=table)
            self.Prefix_Origin.update_invalid_asn(table=table)
        self.Prefix_Origin.update_hijack(table=table)
        # self.Prefix_Origin.update_time(table=table)
        self.Prefix_Origin.add_decision_columns(table=table)
        # self.Prefix_Origin.get_prefix_origin(table=table)
        return

    def run_Conflict_Classifier(self,table,datetime_format=True):
        self.Conflict_Classifier.run_policy_1_db(table=table)
        self.Conflict_Classifier.run_policy_2_db(table=table,datetime_format=datetime_format)
        self.Conflict_Classifier.run_policy_3_db(table=table)
        self.Conflict_Classifier.run_policy_4_db(table=table)
        self.Conflict_Classifier.run_policy_5_db(table=table)
        # self.Conflict_Classifier.run_policy_6_db(table=table)
        # self.Conflict_Classifier.run_policy_7_db(table=table)
        return

    def run_What_If_Analysis(self,table,asn):
        self.What_If_Analysis.fill_db(table,asn,1)
        self.What_If_Analysis.fill_db(table,asn,2)
        self.What_If_Analysis.fill_db(table,asn,3)
        self.What_If_Analysis.fill_db(table,asn,4)
        self.What_If_Analysis.fill_db(table,asn,5)
        # self.What_If_Analysis.fill_db(table,asn,6)
        # self.What_If_Analysis.fill_db(table,asn,7)
        return

    def analyze_all_asn_python(self):
        print("0: get asn list")
        # Estimation: 2 minutes
        asns = self.Conflict_Identifier.get_asn_list()
        print("1: get roas")
        roas = self.ROAs_Collector.get_ROAs()

        # Single Core Implementation
        # for index, row in asns.iterrows():
            # asn = row['asn']
        print("2: get asn")
        asn=asns['asn'][0]
        print("3: get prefix_origin")
        prefix_origin = self.Conflict_Identifier.get_prefix_origin_query(asn)
        print("4: convert prefix")
        prefix_origin['prefix'] = prefix_orign['prefix'].astype(ip.ip_network)
        print(type(prefix_origin['prefix'][0]))

    def output_message(self,msg,counter):
        if self.debug:
            print(counter, msg)
        return counter + 1

    def analyze_all_asn_memory(self):
        # mgr = Manager()
        # ns = mgr.Namespace()
        # ns.hijack = self.Prefix_Origin.get_hijack()[['prefix','origin']]
        # ns.unique_prefix_origin_history = self.Prefix_Origin.get_unique_prefix_origin_history()
        # ns.asn = asn
        hijack = self.Prefix_Origin.get_hijack()[['prefix','origin']]
        unique_prefix_origin_history = self.Prefix_Origin.get_unique_prefix_origin_history()
        asns = self.Conflict_Identifier.get_asn_list()
        if type(asns[0]) is not int:
            asns = [a['asn'] for a in asns]
        args = []
        for asn in asns:
            args.append([asn,hijack,unique_prefix_origin_history])
        # p = Process(target=worker, args=(ns, work_unit))
        pool = pathos.multiprocessing.ProcessingPool(ncpu).map
        pool(self.analyze_one_asn_memory,args)
        return ns.unique_prefix_origin_history

    def analyze_all_asn_db(self):
        asns = self.Conflict_Identifier.get_asn_list()
        start_time_entire = time.time()
        if type(asns[0]) is not int:
            asns = [a['asn'] for a in asns]
        ncpu = multiprocessing.cpu_count()
        pool = pathos.multiprocessing.ProcessingPool(ncpu).map
        pool(self.analyze_one_asn_db,asns)

        # accu = 0
        # for i in range(len(asns)):
        #     start_time = time.time()
        #     self.analyze_one_asn_db(asns[i])
        #     end_time = time.time()
        #     accu = end_time-start_time + accu
        #     print(str(i+1).zfill(5),'/',len(asns),int(end_time-start_time),'seconds, average is',accu/(i+1))
        print("Entire:", "{0:.2f}".format(time.time()-start_time_entire))
        return
    #

    def analyze_one_asn_db(self,args):
        asn,hijack,unique_prefix_origin_history=self.args
    def analyze_one_asn_db(self,asn,drop_table=True):
        start_time_total = time.time()
        procedure = 0
        procedure = self.output_message("Get table names.",procedure)
        start_time = time.time()
        table_prefix_origin = self.config['TABLES']['extrapolation_results']
        table_prefix_origin_asn = table_prefix_origin + '_' + str(asn)
        if self.debug:
            print("Time Elapsed:",int(time.time()-start_time))


        procedure = self.output_message("Conflict_Classifier",procedure)
        start_time = time.time()
        self.run_Conflict_Identifier(asn=asn,table_source=table_prefix_origin,table=table_prefix_origin_asn)
        if self.debug:
            print("Time Elapsed:",int(time.time()-start_time))

        procedure = self.output_message("Prefix_Origin",procedure)
        start_time = time.time()
        self.run_Prefix_Origin(table=table_prefix_origin_asn)
        if self.debug:
            print("Time Elapsed:",int(time.time()-start_time))

        procedure = self.output_message("Conflict_Classifier",procedure)
        start_time = time.time()
        self.run_Conflict_Classifier(table=table_prefix_origin_asn,datetime_format=True)
        if self.debug:
            print("Time Elapsed:",int(time.time()-start_time))

        procedure = self.output_message("What_If_Analysis",procedure)
        start_time = time.time()
        self.run_What_If_Analysis(table=table_prefix_origin_asn,asn=asn)
        if self.debug:
            print("Time Elapsed:",int(time.time()-start_time))
        # self.What_If_Analysis.init_what_if_analysis_db()

        if drop_table:
            self.What_If_Analysis.drop_prefix_origin(table=table_prefix_origin_asn)
        print(asn,"{0:.2f}".format(time.time()-start_time_total),'seconds')
        return

    def analyze_one_asn_python(self,asn,roas):
        # print("1: get roas")
        # print("3: get prefix_origin")
        # prefix_origin = self.Conflict_Identifier.get_prefix_origin_query(asn)
        # print("4: convert prefix")
        # prefix_origin['prefix'] = prefix_origin['prefix'].apply(ip.ip_network)
        # prefix_origin['wroa'] = False
        # prefix_origin['invalid_asn'] = False
        # prefix_origin['invalid_length'] = False
        # print(prefix_origin)
        #
        #
        # # Remove after test
        # # prefix_origin = prefix_origin.iloc[:50,:]
        # print("start timing", prefix_origin.shape[0])
        # start_time = time.time()
        # # sum(roas4['prefix'].apply(df['prefix'][5].subnet_of))
        # # Update roa information and determin=-
        # # prefix_origin[['wroa','invalid_length','invalid_asn'] = prefix_origin[['wroa','invalid_length','invalid_asn'].apply(self.Conflict_Identifier.validation)s
        # self.Conflict_Identifier.init_ROAs()
        # cum_lst = []
        # counter = 0
        # for index, row in prefix_origin.iterrows():
        #     print(counter)
        #     counter += 1
        #     cum_lst.append(self.Conflict_Identifier.local_validation(row))
        # cum_lst = pd.DataFrame(cum_lst)
        # prefix_origin['wroa']           = cum_lst['wroa']
        # prefix_origin['invalid_asn']    = cum_lst['invalid_asn']
        # prefix_origin['invalid_length'] = cum_lst['invalid_length']
        # print(prefix_origin)

        print(time.time()-start_time)
        return prefix_origin, cum_lst
