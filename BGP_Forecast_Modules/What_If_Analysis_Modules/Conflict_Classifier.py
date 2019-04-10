#! /usr/bin/env python3

import os
import sys
import copy
import json
import time
import math
import random
import pathos
import datetime
from urllib.parse import quote

# Pandas
import numpy as np
import pandas as pd

# Multiprocessing
import pathos.multiprocessing as mp
import logging

# Import Utilities
from ..Utilities.Database import *
from ..Utilities.Utilities import *

# We denote all the BGP announcements as A
# we denote a BGP announcement as a

# Policy 1: Simple Time-based Heuristic
# Policy 2: Deprefer if no available alternative, Enforce otherwise
# Policy 3: Enforce if origin is invalid, pass otherwise
# TODO
# Policy 4: Complex Time-based Heuristic

# decision:
# None: Undecided
# 0: Enforce
# 1: Deprefer
# 2: Pass
# 3: Whitelist

class Conflict_Classifier():
    def __init__(self,config,debug=False):
        logging.basicConfig(filename='What_If_Analysis.log',)
        self.config = config
        self.debug = debug
        self.df_neighboors = None
        self.mp_exist_alternative =False
        self.exists_alternative_method = 0

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

    # Policy 1: ROV
    def run_policy_1_db(self,table):
        sql = '''UPDATE ''' + table + '''
            SET decision_1=0
            WHERE invalid_length=true
            OR invalid_asn=true;
            '''

        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_1=2
            WHERE invalid_length=false
            AND invalid_asn=false;
            '''
        self.sql_operation(sql)
        return

    def run_policy_2_db(self,table,datetime_format=True,params=None):
        # Init column names
        if params == None:
            params = self.config['POLICY_2']
        table_names = self.config['TABLES']
        time_current = int(time.time())

        # Create decision_2 column if not exists
        # Init boundary parameters
        if datetime_format:
            length_1 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['length_1']))).date())
            length_2 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['length_2']))).date())
            length_3 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['length_3']))).date())
            asn_1 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['asn_1']))).date())
            asn_2 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['asn_2']))).date())
            asn_3 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['asn_3']))).date())
            both_1 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['both_1']))).date())
            both_2 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['both_2']))).date())
            both_3 = str(datetime.datetime.fromtimestamp((time_current - time_parser_epoch(params['both_3']))).date())
        else:
            length_1 = str(time_current - time_parser_epoch(params['length_1']))
            length_2 = str(time_current - time_parser_epoch(params['length_2']))
            length_3 = str(time_current - time_parser_epoch(params['length_3']))
            asn_1 = str(time_current - time_parser_epoch(params['asn_1']))
            asn_2 = str(time_current - time_parser_epoch(params['asn_2']))
            asn_3 = str(time_current - time_parser_epoch(params['asn_3']))
            both_1 = str(time_current - time_parser_epoch(params['both_1']))
            both_2 = str(time_current - time_parser_epoch(params['both_2']))
            both_3 = str(time_current - time_parser_epoch(params['both_3']))

        sql = '''UPDATE ''' + table + '''
            SET decision_2=0
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen>\'''' + length_1 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=1
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<\'''' + length_1 + '''\'::date AND
            first_seen>=\'''' + length_2 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=2
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<\'''' + length_2 + '''\'::date AND
            first_seen>=\'''' + length_3 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=3
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<=\'''' + length_3 + '''\'::date);'''
        self.sql_operation(sql)


        sql = '''UPDATE ''' + table + '''
            SET decision_2=0
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen>\'''' + asn_1 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=1
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<\'''' + asn_1 + '''\'::date AND
            first_seen>=\'''' + asn_2 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=2
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<\'''' + asn_2 + '''\'::date AND
            first_seen>=\'''' + asn_3 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=3
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<=\'''' + asn_3 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=0
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen>\'''' + both_1 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=1
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<\'''' + both_1 + '''\'::date AND
            first_seen>=\'''' + both_2 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=2
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<\'''' + both_2 + '''\'::date AND
            first_seen>=\'''' + both_3 + '''\'::date);'''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_2=3
            WHERE
            (invalid_asn=true OR invalid_length=true)
            AND
            (first_seen<=\'''' + both_3 + '''\'::date);'''
        self.sql_operation(sql)
        return


    # Policy 3: length
    def run_policy_3_db(self,table):
        sql = '''UPDATE ''' + table + '''
            SET decision_3=0
            WHERE invalid_length=true
            OR invalid_asn=true;
            '''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_3=2
            WHERE invalid_length=false
            AND invalid_asn=false;
            '''
        self.sql_operation(sql)
        return

    # Policy 4: asn
    def run_policy_4_db(self,table):
        sql = '''UPDATE ''' + table + '''
            SET decision_4=0
            WHERE invalid_asn=true;
            '''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_4=2
            WHERE invalid_asn=false;
            '''
        self.sql_operation(sql)
        return


    # Policy 5: both
    def run_policy_5_db(self,table):
        sql = '''UPDATE ''' + table + '''
            SET decision_5=0
            WHERE invalid_length=true
            AND invalid_asn=true;
            '''
        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_5=2
            WHERE invalid_length=false
            OR invalid_asn=false;
            '''
        self.sql_operation(sql)
        return

    def run_policy_6_db(self,table):
        sql = '''UPDATE ''' + table + '''
            SET decision_1=1
            WHERE next_best_as!=0;
            '''

        self.sql_operation(sql)

        sql = '''UPDATE ''' + table + '''
            SET decision_1=2
            WHERE next_best_as=0;
            '''
        self.sql_operation(sql)
        return

    def run_policy_7_db(self,table):
        self.run_policy_6_db(table)

        sql = '''UPDATE ''' + table + '''
            SET decision_1=1
            FROM ''' + table + '''
            WHERE prefix << prefix;
            '''
        self.sql_operation(sql)
        return

    # Policy 2: Simple Time-based Heuristic
    def run_policy_2(self,df,params=None):
        # Init column names
        if params == None:
            params = self.config['POLICY_2']
        table_names = self.config['TABLES']
        decision_bbb = table_names['decision_2']
        invalid_length = table_names['invalid_length']
        invalid_asn = table_names['invalid_asn']
        ctime = table_names['first_seen']
        time_current = int(time.time())

        # Create decision_2 column if not exists
        if not decision_2 in df.columns:
            df[decision_2] = None

        # Init boundary parameters
        length_1 = time_current - time_parser_epoch(params['length_1'])
        length_2 = time_current - time_parser_epoch(params['length_2'])
        length_3 = time_current - time_parser_epoch(params['length_3'])
        asn_1 = time_current - time_parser_epoch(params['asn_1'])
        asn_2 = time_current - time_parser_epoch(params['asn_2'])
        asn_3 = time_current - time_parser_epoch(params['asn_3'])
        both_1 = time_current - time_parser_epoch(params['both_1'])
        both_2 = time_current - time_parser_epoch(params['both_2'])
        both_3 = time_current - time_parser_epoch(params['both_3'])

        #######################################################################
        # 1. For invalid_length
        # 1.1Enforce if age is smaller than length_1
        df.at[
            (df[invalid_length] == True) &
            (df[ctime] > length_1),
            decision_2] = 0

        # 1.2 Deprefer if age is greater than or equal to length_1 but smaller than length_2
        df.at[
            (df[invalid_length] == True) &
            (df[ctime] <= length_1) &
            (df[ctime] > length_2),
            decision_2] = 1

        # 1.3 Enforce if age is greater than or equal to length_2 but smaller than length_3
        df.at[
            (df[invalid_length] == True) &
            (df[ctime] <= length_2) &
            (df[ctime] > length_3),
            decision_2] = 2

        # 1.4 Whitelist if age is greater than or equal to length_3
        df.at[
            (df[invalid_length] == True) &
            (df[invalid_asn] == False) &
            (df[ctime] <= length_3),
            decision_2] = 3

        #######################################################################
        # 2. For invalid_asn
        # 2.1 Enforce if age is smaller than asn_1
        df.at[
          (df[invalid_asn] == True) &
          (df[ctime] > asn_1),
          decision_2] = 0

        # 2.2 Deprefer if age is greater than or equal to asn_1 but smaller than asn_2
        df.at[
          (df[invalid_asn] == True) &
          (df[ctime] <= asn_1) &
          (df[ctime] > asn_2),
          decision_2] = 1

        # 2.3 Enforce if age is greater than or equal to asn_2 but smaller than asn_3
        df.at[
          (df[invalid_asn] == True) &
          (df[ctime] <= asn_2) &
          (df[ctime] > asn_3),
          decision_2] = 2

        # 2.4 Whitelist if age is greater than or equal to asn_3
        df.at[
          (df[invalid_asn] == True) &
          (df[ctime] <= asn_3),
          decision_2] = 3

        #######################################################################
        # 3. For invalid_both
        # 3.1 Enforce if age is smaller than both_1
        df.at[
          (df[invalid_length] == True) &
          (df[invalid_asn] == True) &
          (df[ctime] > both_1),
          decision_2] = 0

        # 3.2 Deprefer if age is greater than or equal to both_1 but smaller than both_2
        df.at[
          (df[invalid_length] == True) &
          (df[invalid_asn] == True) &
          (df[ctime] <= both_1) &
          (df[ctime] > both_2),
          decision_2] = 1

        # 3.3 Enforce if age is greater than or equal to both_2 but smaller than both_3
        df.at[
          (df[invalid_length] == True) &
          (df[invalid_asn] == True) &
          (df[ctime] <= both_2) &
          (df[ctime] > both_3),
          decision_2] = 2

        # 3.4 Whitelist if age is greater than or equal to both_3
        df.at[
          (df[invalid_length] == True) &
          (df[invalid_asn] == True) &
          (df[ctime] <= both_3),
          decision_2] = 3

        return df


    def run_policy_3(self,df):
        # Init column names
        table_names = self.config['TABLES']
        invalid_asn = table_names['invalid_asn']
        decision_aaa = table_names['decision_aaa']

        # create decision_aaa column if not exists
        if not decision_aaa in df.columns:
            df[decision_aaa] = None

        df.at[df[invalid_asn] == True, decision_aaa] = 0
        df.at[df[invalid_asn] == False, decision_aaa] = 2

        return df

    def run_policy_2(self,df):
        # Init column names
        if params == None:
            params = self.config['POLICY_1']
        table_names = self.config['TABLES']

        decision_2 = table_names['decision_2']
        invalid_length = table_names['invalid_length']
        invalid_asn = table_names['invalid_asn']
        ctime = table_names['time']
        best_alternative = table_name['best_alternative']



    def run_policy_2_old(self,
                    df,
                    asn = None,
                    neighbor_threshold = 0,
                    mp_prefix_origin = True,
                    mp_exist_alternative = False,
                    exists_alternative_method = 0):

        # Set parameters
        self.mp_exist_alternative = mp_exist_alternative
        self.exists_alternative_method = exists_alternative_method

        # Init column names
        table_names = self.config['TABLES']
        invalid_asn = table_names['invalid_asn']
        decision_bbb = table_names['decision_bbb']

        # create decision_bbb column if not exists
        if not decision_bbb in df.columns:
            df[decision_bbb] = None
        decision_index = df.columns.get_loc(decision_bbb)

        # get extrapolation results of neighbors
        # if asn
        neighbors_pool = self.get_neighbors_pool(asn)
        if len(neighbors_pool) < neighbor_threshold:
            self.df_neighbors = self.get_neighbors_extrapolation_results(neighbors_pool)
        else:
            self.df_neighbors = None


        if mp_prefix_origin:
            pool = pathos.multiprocessing.ProcessingPool().map
            result = pool(
                        self.exists_alternative,
                        df[['asn','prefix','origin','received_from_asn']].itertuples(index=False,name=False))
        else:
            result = []
            for i in range(df.shape[0]):
                if self.debug:
                    print("current:", i)
                if self.exists_alternative(df.iloc[i][['asn','prefix','origin','received_from_asn']],df_neighbors,neighbors_pool,mp_exist_alternative,exists_alternative_method=exists_alternative_method):
                    result.append(True)
                    # print(True)
                else:
                    result.append(False)
            if self.debug:
                print(result)

        # Deprefer if exists alternative announcement
        df.loc[result,decision_bbb] = 1
        # Pass otherwise
        df.loc[df[decision_bbb].isnull(),'decision_bbb'] = 2
        return df

    def exists_alternative(self,row):
        # Init Database
        # Mode 0: Matrix matrix_operation
        # Mode 1: multiprocessing
        # Mode 2: for loop

        # Get asn, prefix, origin
        [asn,prefix,origin,received_from_asn] = row

        # Get table names
        extrapolation_results = self.config['TABLES']['extrapolation_results']

        # Initiate Database
        connection = init_db(self.config['DATABASE']['path_confidential'])
        cursor = connection.cursor()

        # If extrapolation_results of neighbors is not None, use
        if self.df_neighbors is not None:
            if self.df_neighbors.loc[(self.df_neighbors['prefix'] == prefix) &
                                (self.df_neighbors['prefix'] == origin) &
                                (self.df_neighbors['asn'] != asn) &
                                (self.df_neighbors['asn'] != received_from_asn)].shape[0] != 0:
                # print("False, spend", round(time.time()-start_time))
                return False
            else:
                # print("True, spend", round(time.time()-start_time))
                return True
        elif self.mp_exist_alternative:
        #     # Multiprocessing version
        #     pool = pathos.multiprocessing.ProcessingPool().imap
        #     result = pool(self.check_prefix_origin_match, iter(neighbors_pool), [prefix]*len(neighbors_pool), [origin]*len(neighbors_pool))
        #     if sum(result) == 0:
        #         return False
        #     else:
                return True
        #
        else:
            neighbors_pool = self.get_neighbors_pool(asn,received_from_asn)
            if self.exists_alternative_method == 0:
                for neighbor in neighbors_pool:
                    df_neighbors = self.get_neighbors_extrapolation_results(neighbor,connection=connection,prefix_origin='-'.join([prefix,str(origin)]))
                    if df_neighbors.shape[0] != 0:
                        return True

            elif self.exists_alternative_method == 1:
            # Single process version
                start_time = time.time()
                for neighbor in neighbors_pool:
                    # print("search for asn=", neighbor)

                    sql = "SELECT asn,prefix_origin FROM " + extrapolation_results + " WHERE asn=" + str(neighbor) + ";"
                    cursor.execute(sql)
                    for result in  cursor.fetchall():
                        po_prefix,po_origin = result['prefix_origin'].split("-")
                        po_origin = int(po_origin)
                        po_asn = int(result['asn'])

                        if po_prefix == prefix and po_origin == origin:
                            cursor.close()
                            connection.close()
                            # print("True, spend", round(time.time()-start_time))
                            return True
            cursor.close()
            connection.close()
            return False

    def check_prefix_origin_match(self,neighbor,prefix,origin,received_from_asn):
        # Init Database
        db_confid = self.config['DATABASE']['path_confidential']
        conn = db(db_confid)
        conn.connect()
        cursor = conn.get_cursor()

        # Init Table Names
        extrapolation_results = self.config['TABLES']['extrapolation_results']

        sql = "SELECT prefix_origin FROM " + extrapolation_results + " WHERE asn=" + str(neighbor) + ";"
        cursor.execute(sql)
        neighbor_prefix_origin = cursor.fetchall()

        for prefix_origin in neighbor_prefix_origin:
            asn_prefix,asn_origin = prefix_origin['prefix_origin'].split("-")
            if asn_prefix == prefix and int(asn_origin) == origin:
                # Close database connection
                cursor.close()
                conn.close()

                return True

        cursor.close()
        conn.close()

        return False

    def get_neighbors_pool(self,asn,received_from_asn=None):
        # Initiate Database
        connection = init_db(self.config['DATABASE']['path_confidential'])
        cursor = connection.cursor()

        # Init Table Names
        peer_peers = self.config['DATABASE']['peer_peers']
        customer_providers = self.config['DATABASE']['customer_providers']
        extrapolation_results = self.config['TABLES']['extrapolation_results']

        # Init the list of neighbor ASes
        neighbors_pool = []

        # Search peers
        sql = "SELECT peer_as_1 FROM " + peer_peers + " WHERE peer_as_2=" + str(asn) + ";"
        cursor.execute(sql)
        neighbors_pool = neighbors_pool + [item['peer_as_1'] for item in cursor.fetchall()]

        sql = "SELECT peer_as_2 FROM " + peer_peers + " WHERE peer_as_1=" + str(asn) + ";"
        cursor.execute(sql)
        neighbors_pool = neighbors_pool + [item['peer_as_2'] for item in cursor.fetchall()]

        # Search providers
        sql = "SELECT provider_as FROM " + customer_providers + " WHERE customer_as=" + str(asn) + ";"
        cursor.execute(sql)
        neighbors_pool = neighbors_pool + [item['provider_as'] for item in cursor.fetchall()]

        # Search customers
        sql = "SELECT customer_as FROM " + customer_providers + " WHERE provider_as=" + str(asn) + ";"
        cursor.execute(sql)
        neighbors_pool = neighbors_pool + [item['customer_as'] for item in cursor.fetchall()]

        if received_from_asn == None:
            neighbors_pool = list(set(neighbors_pool) - set([asn]))
        else:
            neighbors_pool = list(set(neighbors_pool) - set([asn,received_from_asn]))
        if self.debug:
            count = 0
            print("Pool size:", len(neighbors_pool))
        return neighbors_pool


    def get_neighbors_extrapolation_results(self,neighbors_pool,connection=None,prefix_origin=None):
        # Initiate Database
        use_inner_connection = False
        if connection == None:
            use_inner_connection = True
            connection = init_db(self.config['DATABASE']['path_confidential'])

        # Init Table Names
        extrapolation_results = self.config['TABLES']['extrapolation_results']

        start_time = time.time()
        # print("get_neighbors_extrapolation_results start")

        if type(neighbors_pool) == list:
            neighbors_str = ", ".join([str(a) for a in neighbors_pool])
        else:
            neighbors_str = str(neighbors_pool)

        if prefix_origin == None:
            sql = "SELECT asn,prefix_origin, received_from_asn FROM " + extrapolation_results + " WHERE asn IN (" + neighbors_str + ");"
        else:
            sql = "SELECT asn,df_neighbors = pd.read_sql_query(sql, con=connection)prefix_origin, received_from_asn FROM " + extrapolation_results + " WHERE asn IN (" + neighbors_str + ") AND prefix_origin='" + prefix_origin + "';"
        df_neighbors = pd.read_sql_query(sql, con=connection)
        # print("query time:",round(time.time()-start_time))

        # Split prefix_orign into prefix, origion
        if prefix_origin == None:
            if 'prefix_origin' in df_neighbors.columns and 'prefix' not in df_neighbors.columns:
                df_neighbors['prefix'] = df_neighbors['prefix_origin'].apply(lambda x: x.split("-")[0])
                df_neighbors['origin'] = df_neighbors['prefix_origin'].apply(lambda x: int(x.split("-")[1]))
                df_neighbors.drop(columns=['prefix_origin'],inplace=True)
            df_neighbors = df_neighbors[['asn','prefix','origin','received_from_asn']]

        if use_inner_connection:
            connection.close()
        return df_neighbors

    def get_extrapolator_results(self,offset,size):
        # Database Initialization
        db_confid = self.config['DATABASE']['path_confidential']
        conn = db(db_confid)
        conn.connect(use_dict=False)
        database = conn.get_connection()

        extrapolation_results = self.config['TABLES']['extrapolation_results']

        sql = "SELECT asn,prefix_origin,received_from_asn FROM " + extrapolation_results + " LIMIT " + str(size) + " OFFSET " + str(offset) + ";"
        df = pd.read_sql_query(sql,con=database)
        df['prefix'] = df['prefix_origin'].apply(lambda x: x.split("-")[0])
        df['origin'] = df['prefix_origin'].apply(lambda x: int(x.split("-")[1]))
        database.close()
        return df

    def get_asn_list(self):
        # Took 325 seconds on 400+ million data

        extrapolation_results = self.config['TABLES']['extrapolation_results']
        # Database Initialization
        database = init_db(self.config['DATABASE']['path_confidential'],use_dict=False)

        sql = "SELECT DISTINCT asn FROM " + extrapolation_results + ";"
        asn_list = pd.read_sql_query(sql,con=database)
        return asn_list









    def get_extrapolator_results_by_asn(self,asn):
        # Database Initialization
        db_confid = self.config['DATABASE']['path_confidential']
        conn = db(db_confid)
        conn.connect(use_dict=False)
        database = conn.get_connection()

        extrapolation_results = self.config['TABLES']['extrapolation_results']

        sql = "SELECT asn,prefix_origin,received_from_asn FROM " + extrapolation_results + " WHERE asn=" + str(asn) + ";"
        df = pd.read_sql_query(sql,con=database)
        if 'prefix_origin' in df.columns and 'prefix' not in df.columns:
            df['prefix'] = df['prefix_origin'].apply(lambda x: x.split("-")[0])
            df['origin'] = df['prefix_origin'].apply(lambda x: int(x.split("-")[1]))
            df.drop(columns=['prefix_origin'],inplace=True)
        database.close()
        return df


    def get_extrapolation_results_from_file(self,table):
        command = "SELECT * FROM " + table + ";"
        self.database.execute(command)
        cursor = self.database.get_cursor()
        ASes = self.fetchall()
        self.ASes = ASes
        return

    def get_extrapolator_data_from_db(self):
        pass

    def what_if_simulation(self):
        for AS in ASes:
            temp_list = []
            for a in AS.anns_from_customers:
                prefix = a.prefix
                origin = a.origin
                if not(prefix == self.a['prefix'] and origin == self.a['origin']):
                    temp_list.append(a)
            AS.anns_from_customers = temp_list
            temp_list = []

            for a in AS.anns_from_peer_proiders:
                prefix = a.prefix
                origin = a.origin
                if not(prefix == self.a['prefix'] and origin == self.a['origin']):
                    temp_list.append(a)
            AS.anns_from_peer_proiders = temp_list
        return

    def store_new_ASes(self):
        self.database.execute2("INSERT INTO analyzed_ASes (ana_prefix) VALUES (%s, %s, %s)", (prefix, asn, validity))
        # Wasn't sure how the data is stored in database. left it blank for now.


    # def get_asn_list(self):
    #     sql = "SELECT * FROM " + str['table_whatif_status'] + ";"
    #     # self.cursor.execute
    #     stime = time.time()
    #     self.whatif_status = pd.read_sql_query(sql, self.conn)
    #     etime = time.time() - stime
    #     print("Get asn status" + str(etime))
    #     # print(self.whatif_status)
    #     self.whatif_status.at[self.whatif_status['completed'] == False]['asn']

    # def store_df_to_database(self,df):
    #         # sql = '''
    #         #     CREATE TABLE roas (
    #         #         roa_id serial PRIMARY KEY,
    #         #         roa_asn bigint,
    #         #         roa_prefix cidr,
    #         #         roa_max_length integer
    #         #     );'''
    #         # self.cursor.execute(sql)
    #     db_confid = self.config['DATABASE']['path_confidential']
    #     conn = db(db_confid)
    #     conn.connect(use_dict=False)
    #     database = conn.get_connection()
    #     cursor = database.cursor()
    #
    #     df.to_sql('')
    #
    #     sql = 'INSERT INTO ' + roa_table_name + '''(roa_asn, roa_prefix, roa_max_length)
    #                 VALUES
    #                 ( %(asn)s, %(prefix)s, %(length)s)'''
    #     # print(sql)
    #     cursor.executemany(sql,self.file)
    #     print('Database Storation Completed.')
    #     database.commit()
    #     database.close()
    #     # self.database.close()
    #     return



    def what_if_report_generator(self,asn,policyid):
        if policyid == 2:
            pass
        else:
            sql = "SELECT * FROM "

if __name__ == "__main__":
    from main import lib_rpki_forecast_modules
    config_source = lib_rpki_forecast_modules()
    config = config_source.get_config()
    # print(config['POLICY_1']['Length_1'])
    # test = copy.deepcopy(config)
    # test['POLICY_1']['Length_1'] = '10s'
    # print(config['POLICY_1']['length_1'])
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
    # # print(df[['invalid_asn','invalid_length','decision_2','decision_bbb','decision_aaa']])
    # print(df)
    #
    #
    # #
    # # start = time.time()
    # # df = Instance.run_policy_2(df,df['asn'][0],mp_prefix_origin=True,mp_exist_alternative=False)
    # # print(round(time.time() - start))
    # #
    # # # df = Instance.run_policy_3(df)
    # # # print(df[['invalid_asn','invalid_length','decision_2','decision_bbb','decision_aaa']])
    # # print(df)
    # # # print(df[df[decision_2]==2][df.columns[4:]])
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
