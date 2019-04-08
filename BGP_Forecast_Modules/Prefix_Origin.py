#! /usr/bin/env python3

import os
import sys
import json
import time
import requests
import numpy as np
import pandas as pd
import multiprocessing as mp
from urllib.parse import quote
import gzip

from .Database import *
from .Utilities import *


class Prefix_Origin:

    def __init__(self, config):
        self.f = None
        self.config = config
        self.tablename = self.config['DATABASE']


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

    def add_decision_columns(self,table):
        sql = "ALTER TABLE " + table + " "

        for i in range(len(self.config['POLICIES'])):
            sql = sql + '''
            ADD COLUMN IF NOT EXISTS decision_''' + str(i+1) + " smallint default 5,"
        sql = sql[:-1] + ";"
        self.sql_operation(sql)
        return

    def update_wroa(self,table):
        # Check whether prefix-origin pair has roaupdate_invalid_length
        sql = '''UPDATE ''' + table + '''
            SET    wroa = true
            FROM   ''' + self.config['TABLES']['roas'] + '''
            WHERE  ''' + table + '''.prefix <<=''' + self.config['TABLES']['roas'] + '''.prefix;'''
        self.sql_operation(sql)
        return

    def update_prefix_origin_validity(self,table):
        sql = '''UPDATE ''' + table + '''
            SET    invalid_length = true
            FROM   ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''
            WHERE  ''' + table + '''.prefix = ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''.prefix
            AND    ''' + table + '''.origin = ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''.origin
            AND    ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''.validity=-1;'''
        # print_time('[update_prefix_origin_validity]\n',sql,'\n')

        self.sql_operation(sql)
        sql = '''UPDATE ''' + table + '''
            SET    invalid_asn = true
            FROM   ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''
            WHERE  ''' + table + '''.prefix = ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''.prefix
            AND    ''' + table + '''.origin = ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''.origin
            AND    ''' + self.config['TABLES']['unique_prefix_origin_validity'] + '''.validity=-2;'''
        self.sql_operation(sql)
        return


    def update_invalid_length(self, table):
        # Verify if prefix-origin pair has a conflict in length
        sql = '''UPDATE ''' + table + '''
            SET    invalid_length = false
            FROM   ''' + self.config['TABLES']['roas'] + '''
            WHERE  ''' + table + '''.prefix <<= ''' + self.config['TABLES']['roas'] + '''.prefix
            AND    masklen(''' + table + '''.prefix) <= ''' + self.config['TABLES']['roas'] + '''.max_length;'''
        self.sql_operation(sql)
        return

    def update_invalid_asn(self,table):
        # Verify if prefix-origin pair has a conflict in asn
        sql = '''UPDATE ''' + table + '''
            SET    invalid_asn = false
            FROM   ''' + self.config['TABLES']['roas'] + '''
            WHERE  ''' + table + '''.prefix <<= ''' + self.config['TABLES']['roas'] + '''.prefix
            AND    ''' + table + '''.origin = ''' + self.config['TABLES']['roas'] + '''.origin;'''
        self.sql_operation(sql)
        return

    def update_hijack(self,table):
        # Verify if prefix-origin pair has a corresponding hijack record
        sql = '''UPDATE ''' + table + '''
            SET    hijack = true
            FROM   ''' + self.config['TABLES']['hijack'] + '''
            WHERE  ''' + table + '''.prefix <<= ''' + self.config['TABLES']['hijack'] + '''.prefix
            AND    ''' + table + '''.origin = ''' + self.config['TABLES']['hijack'] + '''.origin;'''
        self.sql_operation(sql)
        return
    def get_hijack(self):
        connection = init_db(self.config['DATABASE']['path_confidential'])
        hijack = self.config['TABLES']['hijack']

        sql = '''SELECT * FROM ''' + hijack + ''' WHERE origin is not null;'''
        df = pd.read_sql_query(sql,con=connection)
        connection.close()
        return df

    def get_unique_prefix_origin_history(self):
        connection = init_db(self.config['DATABASE']['path_confidential'])
        unique_prefix_origin_history = self.config['TABLES']['unique_prefix_origin_history']

        sql = '''SELECT * FROM ''' + unique_prefix_origin_history + ''';'''
        df = pd.read_sql_query(sql,con=connection)
        connection.close()
        return df

    def update_time(self,table,prefixorigin=True):
        # Verify if prefix-origin pair has a corresponding hijack record
        sql = '''UPDATE ''' + table + '''
            SET    first_seen=''' + self.config['TABLES']['prefix_origin_history'] + '''.first_seen
            FROM   ''' + self.config['TABLES']['prefix_origin_history'] + '''
            WHERE  ''' + table + '''.prefix_origin = ''' + self.config['TABLES']['prefix_origin_history'] + '''.prefix_origin;'''
        self.sql_operation(sql)
        return


    def get_prefix_origin(self,table):
        connection = init_db(self.config['DATABASE']['path_confidential'])
        sql = "SELECT * FROM " + table + ";"
        df = pd.read_sql_query(sql,con=connection)
        connection.close()
        return df

    def collect_from_conflicted_announcements(self):
        # Droping exist tables
        sql = "DROP INDEX IF EXISTS " + self.tablename['po_analysis_distinct'] + self.tablename['po_analysis_distinct_index'] + ''';
        DROP TABLE IF EXISTS ''' + self.tablename['po_analysis'] + ''';
        DROP TABLE IF EXISTS ''' + self.tablename['po_analysis_distinct'] + ";"
        self.cursor.execute(sql)
        self.conn.commit()
        # cursor = self.cursor

        # Create tables
        sql = "CREATE TABLE " + self.tablename['po_analysis_distinct'] + " AS SELECT DISTINCT ON (prefix_origin) prefix_origin, ann_id FROM " + self.tablename['table_extrapolation'] + ''' ORDER BY prefix_origin, ann_id;
        CREATE TABLE ''' + self.tablename['po_analysis'] + " AS SELECT ann_id, asn, prefix_origin, received_from_asn FROM " + self.tablename['table_extrapolation'] + ";"
        self.cursor.execute(sql)
        self.conn.commit()

        # Add new columns on poa_distinct
        sql = "ALTER TABLE " + self.tablename['po_analysis_distinct'] + '''
            ADD COLUMN invalid_length boolean default false,
            ADD COLUMN invalid_asn boolean default false,
            ADD COLUMN hijack boolean default false,
            DROP COLUMN IF EXISTS priority,
            DROP COLUMN IF EXISTS asn,
            ADD COLUMN prefix cidr,
            ADD COLUMN origin bigint,
            ADD COLUMN decision smallint ARRAY,
            ADD COLUMN time integer,
            ADD COLUMN wroa boolean default false;'''
        self.cursor.execute(sql)
        self.conn.commit()

        # Generate prefix and origin on poa_distinct
        sql = "UPDATE " + self.tablename['po_analysis_distinct'] + '''
            SET       prefix = split_part(''' + self.tablename['po_analysis_distinct'] + '''.prefix_origin, '-', 1)::cidr,
                   origin = split_part(''' + self.tablename['po_analysis_distinct'] + '''.prefix_origin, '-', 2)::bigint;'''
        self.cursor.execute(sql)
        self.conn.commit()


        # Add new columns to poa
        sql = "ALTER TABLE " + self.tablename['po_analysis'] + '''
            ADD COLUMN prefix cidr,
            ADD COLUMN origin bigint;'''
        self.cursor.execute(sql)
        self.conn.commit()

        # Generate prefix and origin to poa
        sql = "UPDATE " + self.tablename['po_analysis'] + '''
            SET       prefix = split_part(''' + self.tablename['po_analysis'] + '''.prefix_origin, '-', 1)::cidr,
                   origin = split_part(''' + self.tablename['po_analysis'] + '''.prefix_origin, '-', 2)::bigint;'''
        self.cursor.execute(sql)
        self.conn.commit()

        # # Drop prefix_origin to save space (not necessary)
        # sql = "ALTER TABLE " + self.tablename['po_analysis'] + '''
     #         DROP COLUMN IF EXISTS prefix_origin;'''
        # self.cursor.execute(sql)
        # self.conn.commit()

        # sql = "DELETE FROM " + self.tablename['po_analysis_distinct'] + ''' WHERE NOT EXISTS
        # ( SELECT 1 FROM roas where roas.roa_prefix >>= prefix);'''

        # # Check whether prefix-origin pair has roa
        # sql = "UPDATE " + self.tablename['po_analysis_distinct'] + '''
        #     SET    wroa = true
        #     FROM   roas
        #     WHERE  prefix <<=roas.roa_prefix;'''
        # self.cursor.execute(sql)
        # self.conn.commit()

        # Verify if prefix-origin pair has a conflict in length
        sql = "UPDATE " + self.tablename['po_analysis_distinct'] + '''
            SET    invalid_length = true
            FROM   roas
            WHERE  prefix <<= roas.roa_prefix
            AND    masklen(prefix) > roas.roa_max_length;'''
        self.cursor.execute(sql)
        self.conn.commit()

        # Verify if prefix-origin pair has a conflict in asn
        sql = "UPDATE " + self.tablename['po_analysis_distinct'] + '''
            SET    invalid_asn = true
            FROM   roas
            WHERE  prefix <<= roas.roa_prefix
            AND    origin != roas.roa_asn;'''
        self.cursor.execute(sql)
        self.conn.commit()

        # Verify if prefix-origin pair has a corresponding hijack record
        sql = "UPDATE " + self.tablename['po_analysis_distinct'] + '''
            SET    hijack = true
            FROM   hijack
            WHERE  prefix <<= hijack.expected_prefix
            AND    origin = hijack.detected_origin_number;'''
        self.cursor.execute(sql)
        self.conn.commit()

        # Create an index to search faster
        sql = "CREATE INDEX " + self.tablename['po_analysis_distinct'] + self.tablename['po_analysis_distinct_index'] + '''
            ON ''' + self.tablename['po_analysis_distinct'] + " (prefix);"
        self.cursor.execute(sql)
        self.conn.commit()

        # load it to pandas.DataFrame
        conn = self.conn.get_connection()
        self.f = pd.read_sql_query("SELECT * FROM " + self.tablename['po_analysis_distinct'] + ";",conn)

        # Mirring mrt takes 805s = 13m
        self.conn.close()


        # announcements = cursor.fetchall()
        # for announcement in announcements:
        #     prefix, asn = announcement[1:3]
        #     self.prefix_origin_pairs.append((prefix, asn))
        # return
    def get_f(self):
        return self.f
    def collect_from_hijacks(self):
        self.database.execute("SELECT * FROM hijack")
        cursor = self.cursor
        announcements = cursor.fetchall()

        for announcement in announcements:
            prefix, asn = announcement[12:14]
            self.hijacks.append((prefix, asn))
        return

    def mark_suspect_attacks(self,a):
        for a in self.hijacks:
            if a['prefix'] == announcement['prefix'] and a['origin'] == announcement['origin']:
                self.prefix_origin_pairs['attack'] = 1
            else:
                self.prefix_origin_pairs['attack'] = 0
        return



if __name__ == "__main__":
    from main import lib_rpki_forecast_modules
    config_source = lib_rpki_forecast_modules()
    config = config_source.get_config()
    Instance = Prefix_Origin(config)
    # Instance.collect_from_conflicted_announcements()
    # Instance.collect_from_hijacks()
    # print(len(Instance.prefix_origin_pairs))
    # ini = Instance
    # print(ini.f.shape)
    # init_po_analysis_distinct
