#! /usr/bin/env python3

import os
import sys
import json
import time
import requests
from .Utilities import *
from .Database import *


class ROAs_Collector:
    def __init__(self, config):
        self.config = config
        self.port = int(self.config['RPKI']['rpki_port'])
        self.rpki_addr = self.config['RPKI']['rpki_addr']
        self.url = self.rpki_addr + ':' + str(self.port) + '/api/roas?pageSize=2'
        self.url_full = None
        self.request = None
        self.header = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        return

    # def run_RPKI_Validator(self):
    #     # print_time('--------Start running rpki-validator-3.0-306--------')
    #     # status = os.system('sh rpki-validator-3.0-306/rpki-validator-3.sh')
    #
    #     # Check every 2 minutes until ROAs is ready in Rpki Validator
    #     print_time('--------Check if ROAs is ready to download, repeat every 2 minutes if not----')
    #
    #     counter = 0
    #     while True:
    #         self.html = requests.head(self.url, headers=self.header)
    #         status = self.html.status_code
    #
    #         if (status in [200, 201]):
    #             print_time('Json file is ready. (code:',status,')\n')
    #             break
    #         print_time('Counter:', counter,'ROAs is not ready. (code:',status,')')
    #         time.sleep(120)


    def download_ROAs(self):
        # Reading ROAs from json format
        print_time('[Get ROAs size] Starts.')
        html = requests.get(self.url, headers=self.header)
        rows = html.json()['metadata']['totalCount']
        print_time('[Get ROAs size] Size:',str(rows),'\n')

        # Reset url with correct row size
        self.url_full = self.url[:-1] + str(rows)
        print_time('[Download ROAs] Starts.')
        html = requests.get(self.url_full, headers=self.header)
        file = html.json()['data']
        print_time('[Download ROAs] Completed.\n')
        return file

    def get_ROAs(self):
        database = init_db(self.config['DATABASE']['path_confidential'],use_dict=False)
        sql = "SELECT * FROM " + self.config['TABLES']['roas'] + ";"
        roas = pd.read_sql_query(sql,con=database)
        database.close()
        return roas

    def init_roas_table(self):
        print_time('[Init ROAs table] Starts')
        roa_table_name = self.config['TABLES']['roas']
        sql = '''
            DROP TABLE IF EXISTS ''' + roa_table_name + ''';
            CREATE TABLE ''' + roa_table_name + ''' (
                roa_id serial PRIMARY KEY,
                prefix cidr,
                asn bigint,
                max_length integer
            );'''
        print_time('[Init ROAs table]\n', sql,'\n')
        sql_operation(sql,self.config['DATABASE']['path_confidential'])
        print_time('[Init ROAs table] Completed.\n')
        return


    def store_ROAs(self,roas):
        # Store the ROAs into roas table in bgp database
        roa_table_name = self.config['TABLES']['roas']

        database, cursor = init_db(self.config['DATABASE']['path_confidential'],
                                   use_dict=True,
                                   cursor=True)
        for roa in roas:
            if type(roa['asn']) is str:
                roa['asn'] = int(roa['asn'][2:])

        print_time('[Store ROAs] Starts.')
        sql = 'INSERT INTO ' + roa_table_name + '''(prefix, asn, max_length)
                    VALUES
                    ( %(prefix)s, %(asn)s, %(length)s)'''
        cursor.executemany(sql,roas)
        database.commit()
        database.close()
        print_time('[Store ROAs] Completed.\n')
        return

    def create_index(self):
        print_time('[Create ROAs Index] Starts.')
        roa_table_name = self.config['TABLES']['roas']
        sql = '''
            CREATE INDEX ''' + roa_table_name + '''_index
            ON ''' + roa_table_name + '''
            USING gist(prefix inet_ops, asn);'''
        print_time('[Create ROAs Index]\n', sql, '\n')
        sql_operation(sql,self.config['DATABASE']['path_confidential'])
        print_time('[Create ROAs Index] Completed.\n')
        return
