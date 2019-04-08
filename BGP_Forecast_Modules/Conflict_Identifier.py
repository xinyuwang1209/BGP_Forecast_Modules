#! /usr/bin/env python3

import os
import sys
import ast
import json
import time
import requests
import numpy as np
import pandas as pd
import ipaddress as ip
import multiprocessing as mp
from urllib.parse import quote

# Database access module import
# dir_db = 'Database/'
# path = os.path.abspath(__file__)
# # print(path)
# path_db = path.split('/')[:-2]
# path_db.append(dir_db)
# path_db = '/'.join(path_db)
# # print(path_db)
# sys.path.insert(0, path_db)
from Database import Database as db
from Utilities import *

class Conflict_Identifier:
    def __init__(self,config):
        # self.url = 'http://localhost:8080/api/bgp/validity?'
        # # self.url = 'http://localhost:8080/api/v2/validity/AS12654/93.175.146.0/24'
        # self.announcements = None
        # self.anno_size = 0
        # self.nprocess = nprocess
        # self.partition_mult = partition_mult
        # self.file = None
        # self.html = None
        # self.prefix_origin_table_name = prefix_origin_table_name
        # self.announcement_table_name = announcement_table_name
        # request = None
        # self.partition = []
        # self.header = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
        #     "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        #     }
        self.config = config
        # Table name Initialization
        self.tablename = config['TABLES']
        # Database Initialization
        self.roas = None
        return

    def get_ROAs(self,mode=4):
        database = init_db(self.config['DATABASE']['path_confidential'],use_dict=False)
        sql = "SELECT * FROM " + self.config['TABLES']['roas'] + ";"
        roas = pd.read_sql_query(sql,con=database)
        database.close()
        roas['prefix'] = roas['prefix'].apply(ip.ip_network)
        if mode == 4:
            roas = roas.loc[roas['prefix'].apply(get_network_version) == 4]
        return roas

    def get_asn_list(self):
        connection = init_db(self.config['DATABASE']['path_confidential'])
        # sql = "SELECT DISTINCT asn FROM " + self.config['TABLES']['extrapolation_results'] + ";"
        # df = pd.read_sql_query(sql,con=database)


        cursor = connection.cursor()
        sql = "SELECT DISTINCT asn FROM " + self.config['TABLES']['extrapolation_asns'] + ";"
        cursor.execute(sql)
        df = cursor.fetchall()
        return [a['asn'] for a in df]

    def init_ROAs(self):
        self.roas = self.get_ROAs(mode=4)
        return

    def local_validation(self,row):
        # print("print row")
        # print(row)
        prefix,origin = row['prefix'],row['origin']
        wroa,invalid_length,invalid_asn = row['wroa'],row['invalid_length'],row['invalid_asn']
        current_roas = self.roas[self.roas['prefix'].apply(prefix.subnet_of)]
        if current_roas.shape[0] == 0:
            wroa            = False
            invalid_length  = False
            invalid_asn     = False
        else:
            wroa = True
            valid = False
            for index,roas_row in current_roas.iterrows():
                roas_prefix, roas_origin, max_length = roas_row['prefix'], roas_row['origin'], roas_row['max_length']
                # Check whether invalid by asn
                if roas_origin != origin:
                    invalid_asn = True
                else:
                    invalid_asn = False
                # Check whether invalid by max length
                if max_length < prefix.prefixlen:
                    invalid_length = True
                else:
                    invalid_legnth = False
                # Remember if both passed
                if invalid_length == False and invalid_length == False:
                    valid = True
            if valid:
                invalid_length == False and invalid_length == False
        # row['wroa'] = wroa
        # row['invalid_asn'] = invalid_asn
        # row['invalid_length'] = invalid_length
        return {'wroa': wroa, 'invalid_asn': invalid_asn, 'invalid_length': invalid_length}

    def get_prefix_origin_query(self,asn):
        query_asn = str(asn)
        connection = init_db(self.config['DATABASE']['path_confidential'])
        sql = "SELECT prefix_origin FROM " + self.config['TABLES']['extrapolation_results'] + " WHERE asn=" + query_asn + ";"
        df = pd.read_sql_query(sql,con=connection)
        df['prefix'] = df['prefix_origin'].apply(lambda x: x.split("-")[0])
        df['origin'] = df['prefix_origin'].apply(lambda x: int(x.split("-")[1]))
        connection.close()
        return df[['prefix','origin']]

    def get_prefix_origin_dump(self):
        url = "http://www.ris.ripe.net/dumps/riswhoisdump.IPv4.gz"
        df = pd.read_table(url,compression='gzip',sep='\t',header=15,names=['origin','prefix','seen-peer'])
        df = df[['prefix','origin']]

        if type(df.iloc[-1,0]) is not str:
            df = df.iloc[:-1,:]
        print("Size of prefix origin pairs is:", df.shape[0])

        special  = df[df['origin'].str.contains('{')]
        df = df[~df['origin'].str.contains('{')]
        lst = []

        for index, row in special.iterrows():
            prefix, origins = row['prefix'], ast.literal_eval(row['origin'])
            for origin in origins:
                # df2 = pd.concat([df2, pd.DataFrame([prefix,origin],columns=['prefix', 'origin'])])
                lst.append([prefix,origin])

        df = pd.concat([df, pd.DataFrame(lst,columns=['prefix','origin'])])

        return df[['prefix','origin']]

    def validation(self,wroa,invalid_length,invalid_asn):

        return

    def init_prefix_origin_table(self,asn,table,table_new):
        # Then add table
        sql = '''DROP TABLE IF EXISTS ''' + table_new + ''';
                CREATE TABLE IF NOT EXISTS ''' + table_new + '''
                AS SELECT * FROM ''' + table + '''
                WHERE asn=''' + str(asn) + ";"
        self.sql_operation(sql)
        return
    # def init_prefix_origin_table(self,asn=0):
    #     # Get table name
    #     # Default name is prefix_origin
    #     connection = init_db(self.config['DATABASE']['path_confidential'],use_dict=True)
    #     table_prefix_origin = self.config['TABLES']['prefix_origin_distinct']
    #     if asn != 0:
    #         table_prefix_origin = table_prefix_origin + '_' + str(asn)
    #     cursor = connection.cursor()
    #     # Drop current table if exists
    #     # Then add table
    #     sql = '''DROP TABLE IF EXISTS ''' + table_prefix_origin + ''';
    #             CREATE TABLE IF NOT EXISTS ''' + table_prefix_origin + ''' (
    #             ''' + table_prefix_origin + '''_id serial PRIMARY KEY,
    #             prefix cidr,
    #             origin bigint,
    #             wroa boolean DEFAULT false,
    #             invalid_length boolean DEFAULT false,
    #             inbalid_asn boolean DEFAULT false,
    #             hijack boolean);'''
    #     cursor.execute(sql)
    #     connection.commit()
    #     connection.close()
    #     return

    def store_prefix_origin(self,df):
        # connection = init_db(self.config['DATABASE']['path_confidential'],use_dict=True)
        table_prefix_origin = self.config['TABLES']['prefix_origin_distinct']
        engine = DB(self.config['DATABASE']['path_confidential']).generate_engine()
        df.to_sql(table_prefix_origin,con=engine,if_exists='replace')
        return
        # file = df.to_dict('records')



    def get_announcements_size(self):
        connection = init_db(self.config['DATABASE']['path_confidential'],use_dict=True)
        cursor = connection.cursor()
        table_prefix_origin = self.config['TABLES']['prefix_origin_distinct']
        cursor.execute("SELECT COUNT(1) FROM " + table_prefix_origin + ";")
        po_size = self.cursor.fetchall()[0]['count']
        print("The total size of the announcement are:", self.anno_size)
        connection.commit()
        connection.close()
        return po_size

    def alter_prefix_origin_columns(self,table,asn=0):
        date_format = self.config['IP']['date_format']
        if asn == 0:
            # Add new columns on poa_distinct
            # extract(epoch from now() at time zone 'utc')::integer
            sql = "ALTER TABLE " + table + '''
                ALTER COLUMN prefix TYPE cidr USING prefix::cidr,
                ALTER COLUMN origin TYPE bigint USING origin::bigint,
                ADD COLUMN IF NOT EXISTS invalid_length boolean default false,
                ADD COLUMN IF NOT EXISTS invalid_asn boolean default false,
                ADD COLUMN IF NOT EXISTS hijack boolean default false,
                ADD COLUMN IF NOT EXISTS first_seen ''' + date_format + ''' default current_date,
                DROP COLUMN IF EXISTS ann_id,
                DROP COLUMN IF EXISTS priority;'''
        else:
            sql = "ALTER TABLE " + table + '''
                ADD COLUMN IF NOT EXISTS prefix cidr,
                ADD COLUMN IF NOT EXISTS origin bigint,
                ADD COLUMN IF NOT EXISTS invalid_length boolean default false,
                ADD COLUMN IF NOT EXISTS invalid_asn boolean default false,
                ADD COLUMN IF NOT EXISTS hijack boolean default false,
                ADD COLUMN IF NOT EXISTS first_seen ''' + date_format + ''' default current_date,
                DROP COLUMN IF EXISTS ann_id,
                DROP COLUMN IF EXISTS priority;'''
        self.sql_operation(sql)
        return

    def create_index(self, table, asn=0,prefixorigin=False):
        if prefixorigin:
            sql = "DROP INDEX IF EXISTS " + table + '''_po_index;
            CREATE INDEX ''' + table + "_po_index ON " + table + " (prefix_origin);"
        else:
            sql = "DROP INDEX IF EXISTS " + table + '''_p_o_index;
            CREATE INDEX ''' + table + "_p_o_index ON " + table + " (prefix, origin);"
        self.sql_operation(sql)
        return

    def split_prefix_origin(self,asn,table):
        # UPDATE prefix;
        sql = '''
        UPDATE ''' + table + '''
        SET	   prefix = split_part(''' + table + '''.prefix_origin, '-', 1)::cidr,
        	   origin = split_part(''' + table + '''.prefix_origin, '-', 2)::bigint;'''
        self.sql_operation(sql)
        return

    def drop_prefix_origin(self,asn,table):
        # UPDATE prefix;
        sql = "ALTER TABLE " + table + " DROP COLUMN IF EXISTS prefix_origin;"
        self.sql_operation(sql)
        return


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

    def init_po_distinct(self):
        table_source = 'simplified_elements'
        sql = '''
            DROP TABLE IF EXISTS ''' + self.tablename['po_analysis_distinct'] + ''';
            CREATE TABLE ''' + self.tablename['po_analysis_distinct'] + '''
            AS SELECT element_id,prefix,as_path[1] FROM ''' + table_source + ";"
        self.cursor.execute(sql)
        self.conn.commit()

        sql = '''
            ALTER TABLE ''' + self.tablename['po_analysis_distinct'] + '''
            RENAME COLUMN as_path TO origin;'''
        self.cursor.execute(sql)
        self.conn.commit()

        sql = '''
            ALTER TABLE ''' + self.tablename['po_analysis_distinct'] + '''
            ADD COLUMN wroa boolean default false,
            ADD COLUMN invalid_length boolean default false,
            ADD COLUMN invalid_asn boolean default false,
            ADD COLUMN first_seen date;'''
        self.cursor.execute(sql)
        self.conn.commit()

        sql = '''
            CREATE INDEX ''' + self.tablename['po_analysis_distinct'] + self.tablename['po_analysis_distinct_index'] + '''
            ON ''' + self.tablename['po_analysis_distinct'] + " (prefix);"
        self.cursor.execute(sql)
        self.conn.commit()

        start_time = time.time()
        # Check whether prefix-origin pair has roa
        sql = "UPDATE " + self.tablename['po_analysis_distinct'] + '''
            SET    wroa = true
            FROM   roas
            WHERE  prefix <<=roas.roa_prefix;'''
        self.cursor.execute(sql)
        self.conn.commit()
        print("Checking if exists roas",time.time()-start_time)


    def validate_and_store(self,announcement):
        prefix = announcement['prefix']
        origin = announcement['origin']
        url = self.url + 'prefix=' + quote(prefix,safe="") + '&asn=' + str(origin)
        html = requests.get(url, headers=self.header)
        try:
            result = html.json()['data']
        except:
            print(html)
            print(prefix,origin)
            validity = 'UNKNOWN'
            return
        if result['validity'] == 'INVALID_ASN':
            validity = '00'
        elif result['validity'] == 'INVALID_LENGTH':
            validity = '01'
        elif result['validity'] == 'UNKNOWN':
            validity = '10'
        elif result['validity'] == 'VALID':
            validity = '11'
        else:
            print(prefix,origin,"NOT FOUND")
            return
        self.partition.append([prefix,origin,validity])
        return

    def validate_and_store_announcements(self):
        processes = []
        query_size = self.nprocess*self.partition_mult
        print('anno size:', self.anno_size)


        sql = "SELECT * FROM " + self.announcement_table_name + " OFFSET " + str(0) + " LIMIT " + str(query_size) + ";"
        self.cursor.execute(sql)
        annos = self.cursor.fetchall()
        # print(annos)

        start_time = time.time()

        for i in range(self.anno_size):
            p = mp.Process(target=self.validate_and_store, args=[annos[i % query_size]])
            processes.append(p)

            if i == self.anno_size - 1 or (i+1) % query_size == 0:
                self.store_partition_to_table()
                self.partition = []
                sql = "SELECT * FROM " + self.announcement_table_name + " OFFSET " + str(i+1) + " LIMIT " + str(query_size)
                self.cursor.execute(sql)
                annos = self.cursor.fetchall()
                print(i, '/', self.anno_size, 'completed.')
                print('Elapsed_time:', time.time() - start_time)
                start_time = time.time()

            if i == self.anno_size - 1 or (i+1) % self.nprocess == 0:
                for p in processes:
                    p.start()
                for p in processes:
                    p.join()
                processes = []
        return


    def store_partition_to_table(self):
        for prefix,origin,validity in self.partition:
            if validity == '00' or validity == '01':
                # next_AS = announcement['as_path'][1]
                self.cursor.execute('''INSERT INTO
                    prefix_origin (po_prefix, po_origin, po_validity)
                    VALUES(%s, %s, %s)''', (prefix, origin, validity))
        return

        #sql = "SELECT prefix,origin," + self.announcement_table_name + ";"
        #self.cursor.execute(sql)
        #self.announcements = self.cursor.fetchall()
        #print(len(self.announcements))
        #return self.announcements








if __name__ == "__main__":
    Instance = Conflict_Identifier()
    Instance.init_po_distinct()
    Instance.init_po_analysis_distinct()
    # Instance.get_announcements()
    # Instance.validate_and_storing_announcements()
    # Instance.download_Invalid_ROAs()
    # Instance.store_Invalid_ROAs()
    # print(announcements[0])
    # counter = 0
    #for anno in announcements:
    #    result = Instance.validate_announcement(anno)
    #    if result == 1:
    #        counter += 1
    # print(counter)
