#! /usr/bin/env python3

import os
import sys
import copy
import json
import time
import math
import random
import pathos
from urllib.parse import quote

# Pandas
import numpy as np
import pandas as pd

# Multiprocessing
import pathos.multiprocessing as mp
import logging

# Database access module import
dir_db = 'Utilities/'
path = os.path.abspath(__file__)
path_db = path.split('/')[:-2]
# print('/'.join(path_db))
# Insert path of root directory
sys.path.insert(0,'/'.join(path_db))
path_db.append(dir_db)
path_db = '/'.join(path_db)
# print(path_db)
# Insert path of Database directory
sys.path.insert(0, path_db)
from Database import Database as db
from Utilities import *

# COMPLETED
# # TODO:

class What_If_Analysis():
    def __init__(self,config,debug=False):
        logging.basicConfig(filename='What_If_Analysis.log',)
        self.config = config
        column_list = []
        column_prefix = self.config['COLUMNS']['prefix']
        column_origin = self.config['COLUMNS']['origin']
        self.debug = debug

    def sql_operation(self,sql,connection=None):
        internal_cursor = True
        if connection is None:
            internal_cursor = False
            connection = init_db(self.config['DATABASE']['path_confidential'],use_dict=False)

        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()

        if internal_cursor:
            connection.close()
        return

    def drop_prefix_origin(self,table):
        sql = "DROP TABLE IF EXISTS " + table + ";"
        self.sql_operation(sql)
        return

    def init_what_if_analysis_db(self):
        table = self.config['TABLES']['what_if_analysis']
        sql = '''DROP TABLE IF EXISTS ''' + table + ''';
                CREATE TABLE IF NOT EXISTS ''' + table + '''(
                po_id serial PRIMARY KEY,
                asn bigint,
                policy_id smallint,
                hijack integer,
                n_true_positive integer,
                n_false_positive integer,
                n_true_negative integer,
                n_false_negative integer
                );'''
        self.sql_operation(sql)
        return

    def fill_db(self,table,asn,policy_id,query=False):
        # if not query:
            # table = config['TABLE']['what_if_analysis']

        connection = init_db(self.config['DATABASE']['path_confidential'],use_dict=True)
        cursor = connection.cursor()

        # Get hijacks
        sql = "SELECT count(1) FROM " + table + ''' WHERE
            hijack=true;'''
        cursor.execute(sql)
        hijack = cursor.fetchall()[0]['count']

        # Get True Positive
        sql = "SELECT count(1) FROM " + table + ''' WHERE
            hijack=true AND decision_''' + str(policy_id) + "<2;"
        cursor.execute(sql)
        true_positive = cursor.fetchall()[0]['count']

        # Get True Negative
        sql = "SELECT count(1) FROM " + table + ''' WHERE
            hijack=false AND decision_''' + str(policy_id) + ">1;"
        cursor.execute(sql)
        true_negative = cursor.fetchall()[0]['count']

        # Get False Positive
        sql = "SELECT count(1) FROM " + table + ''' WHERE
            hijack=false AND decision_''' + str(policy_id) + "<2;"
        cursor.execute(sql)
        false_positive = cursor.fetchall()[0]['count']

        # Get True Positive
        sql = "SELECT count(1) FROM " + table + ''' WHERE
            hijack=true AND decision_''' + str(policy_id) + ">1;"
        cursor.execute(sql)
        false_negative = cursor.fetchall()[0]['count']
        sql = '''INSERT INTO ''' + self.config['TABLES']['what_if_analysis'] + '''
        (asn,policy_id,hijack,
        n_true_positive,n_true_negative,
        n_false_positive,n_false_negative) VALUES
         (%(asn)s, %(policy_id)s, %(hijack)s,
        %(n_true_positive)s,%(n_true_negative)s,
        %(n_false_positive)s,%(n_false_negative)s)'''
        file = {'asn':str(asn),'policy_id':str(policy_id),
                'hijack':hijack,
                'n_true_positive':true_positive,
                'n_true_negative':true_negative,
                'n_false_positive':false_positive,
                'n_false_negative':false_negative}
        cursor.execute(sql,file)
        connection.commit()
        connection.close()
        return

    def what_if_report_generator(self,asn):
        decisions = self.get_column_decisions()
        results = sel.get_analysis_for_all_policies(asn,decisions)
        pass

    def get_column_decisions(self):
        decisions = []
        for i in len(self.config['POLICIES']):
            decisions.append(self.config['COLUMNS']['decision_'+ str(i)])
        return decisions

    def get_analysis_for_all_policies(self,asn,decisions):
        params_list = []

        for i in range(len(decisions)):
            # True Negative
            # Hijack is False and Decision is 0 or 1
            params_list.append([asn,False,False,decisions[i]])
            # True Positive
            # Hijack is True and Decision is 2 or 3
            params_list.append([asn,True,True,decisions[i]])
            # False Positive
            # Hijack is False and Decision is 2 or 3
            params_list.append([asn,False,True,decisions[i]])
            # False Negative
            # Hijack is True and Decision is 0 or 1
            params_list.append([asn,True,False,decisions[i]])

        pool = pathos.multiprocessing.ProcessingPool().imap
        results = pool(
            self.get_analysis_for_each_policy,
            params_list)
        results_list = []
        count = 0
        decision_count = -1
        for element in results:
            if count % len(decisions) == 0:
                result_list[decision_count] = []
            result_list[decision_count].append(element)
            count += 1
        return results_list

    def get_analysis_for_each_policy(self,params):
        # Parameter 1: asn
        asn = params[0]
        # Parameter 2: is hijacked
        hijacked = params[1]
        # Parameter 3: policy decision
        # If enforce or deprefer, decision should be 0 or 1
        if params[2]:
            decision = "<2"
        else:
            decision = ">1"
        # Parameter 4: column name of decision
        column_decision = params[3]

        # Initiate Database
        connection = init_db(self.config['DATABASE']['path_confidential'],use_dict=True)
        cursor = connection.cursor()

        table_prefix_origin = self.config['TABLES']['prefix_origin']
        column_hijack = self.config['COLUMNS']['origin']
        column_asn = self.config['COLUMNS']['asn']
        sql = "SELECT count(1) FROM " + table_prefix_origin + '''
         WHERE ''' + column_asn + "=" + asn + '''
         AND ''' + column_hijack + "=" + str(hijacked) + '''
         AND ''' + column_decision + decision + ";"

        size_result = cursor.fetchall()[0]['count']
        return size_result

    def get_size_of_prefix_origin(self,asn):
        # Initiate Database
        connection = init_db(self.config['DATABASE']['path_confidential'],use_dict=True)
        cursor = connection.cursor()

        sql = "SELECT count(1) FROM " + prefix_origin + '''
         WHERE ''' + column_asn + "=" + asn + ";"
        cursor.execute(sql)
        size_prefix_origin = cursor.fetchall()[0]['count']

        return size_prefix_origin

if __name__ == "__main__":
    from main import lib_rpki_forecast_modules
    config_source = lib_rpki_forecast_modules()
    config = config_source.get_config()
    # print(config['Policy_1']['Length_1'])
    # test = copy.deepcopy(config)
    # test['Policy_1']['Length_1'] = '10s'
    # print(config['Policy_1']['length_1'])
    Instance = What_If_Analysis(config,debug=False)
    # # ASes = Instance.get_extrapolator_data()
    # # New_ASes = Instance.what_if_simulation()
    # df = random_prefix_origin_generator(0,has_asn=True,fix_asn=21267,special_one=True)
    # print(df)
    # # print(df.columns['asn'])
    #
    # # print(df)
    # # df = Instance.run_policy_1(df)
    #
    #
    #
    # start = time.time()
    #
    # df = Instance.run_policy_2(df,df['asn'][0],mp_prefix_origin=True,mp_exist_alternative=False,exists_alternative_method=False,neighbor_threshold=1000000)
    # print(round(time.time() - start))
    #
    # # df = Instance.run_policy_3(df)def fname(arg):
    # # print(df[['invalid_asn','invalid_length','decision_1','decision_2','decision_3']])
    # print(df)
    #
    #
    # #
    # # start = time.time()
    # # df = Instance.run_policy_2(df,df['asn'][0],mp_prefix_origin=True,mp_exist_alternative=False)
    # # print(round(time.time() - start))
    # #
    # # # df = Instance.run_policy_3(df)def fname(arg):
    # # # print(df[['invalid_asn','invalid_length','decision_1','decision_2','decision_3']])
    # # print(df)
    # # # print(df[df[decision_1]==2][df.columns[4:]])
    # #
    # #
    # #

    asn_list = pd.read_csv("saved_asn_list.csv", index_col=0)
    for i in range(asn_list.shape[0]):
        start_time=time.time()
        df = Instance.get_extrapolator_results_by_asn(asn_list['asn'][i])
        print("Current:",i+1,"/",asn_list.shape[0],"Size of prefix-origin:", df.shape[0], "neighbors:", Instance.get_neighbors_pool(df['asn'][0]))
        if df.shape[0] < 6000:
            df = Instance.run_policy_2(df,df['asn'][0],neighbor_threshold=0,mp_prefix_origin=True,mp_exist_alternative=False,exists_alternative_method=0)
            print(time.time()-start_time)

    #
    #
    #
    #
    #
    # # df = Instance.get_extrapolator_results(0,500)
    # total_start_time = time.time()
    # # asn_list = Instance.get_asn_list()
    # # asn_list.to_csv("saved_asn_list.csv")
    # asn_list = pd.read_csv("saved_asn_list.csv", index_col=0)
    #
    # for i in range(asn_list.shape[0]):
    #     print("Running", i+1, "/", asn_list.shape[0])
    #     # print("Test single-core:")
    #     start_time = time.time()
    #     df = Instance.get_extrapolator_results_by_asn(asn_list['asn'][i])
    #     if df.shape[0] < 10000:
    #         df = Instance.run_policy_2(df,mp_prefix_origin=True,mode_search_alternative=0)
    #         print("Elapsed time:", round(time.time()-start_time))
    # print("Total Elapsed Time:", time.time()-total_start_time)
    #
    #
    #
    # # #
    # # df2 = Instance.get_extrapolator_results(0,50)
    # # print("Test multi-core:")
    # # start_time = time.time()
    # # df2 = Instance.run_policy_2(df2,mp_prefix_origin=False,mode_search_alternative=0)
    # # print("Elapsed time:", round(time.time()-start_time))
    #
    #
    # # Instance.get_asn_list()
