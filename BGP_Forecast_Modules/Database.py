#!/usr/bin/env python3

import os
import sys
import psycopg2
import pandas as pd
import configparser
from sqlalchemy import create_engine
from psycopg2.extras import RealDictCursor

class Database():
    """Interact with the database to populate them"""

    def __init__(self,path_confidential,message=False):
        self.message = message
        self.connection = None
        self.cursor = None
        self.file_path = path_confidential
        self.config = configparser.ConfigParser()
        self.config.read(path_confidential)

    def get_config(self,file_path):
        username = self.config['bgp']['user']
        password = self.config['bgp']['password']
        database = self.config['bgp']['database']
        # print(username,password,database)
        return(username,password,database)

    def connect(self,use_dict=True):
        # Start connecting PostgreSQL
        if self.message:
            print('----Start connecting PostgreSQL....')
        username, password, database = self.get_config(self.file_path)
        try:
            if use_dict:
                self.connection = psycopg2.connect(user=username,
                                                    password=password,
                                                    host="localhost",
                                                    database=database,
                                                    cursor_factory=RealDictCursor)
            else:
                self.connection = psycopg2.connect(user=username,
                                                    password=password,
                                                    host="localhost",
                                                    database=database)

            if self.message:
                print('Database connected.')
            return
        except Exception as e:
            raise ('Postgres connection failure: {0}'.format(e))

    def get_cursor(self,server=None):
        self.cursor = self.connection.cursor()
        return self.cursor

    def commit(self):
        self.connection.commit()
        return

    def get_connection(self):
        return self.connection

    def close(self):
        self.connection.close();
        self.cursor.close();
        if self.message:
            print('Database closed.')
        return

    def generate_engine(self):
        username, password, database = self.get_config(self.file_path)
        engine = create_engine("postgresql://" + username + ":" + password + "@localhost/" + database)
        return engine

    # def run_cmd_db(self,str):
def init_db(db_confid,use_dict=True,cursor=False):
    # Database Initialization
    conn = Database(db_confid)
    conn.connect(use_dict=use_dict)
    database = conn.get_connection()
    if cursor:
        return database, database.cursor()
    else:
        return database


def sql_operation(sql,db_confid,connection=None,use_dict=True,result=False):
    internal_cursor = True
    if connection is None:
        internal_cursor = False
        connection = init_db(db_confid,use_dict)
    if result:
        df = pd.read_sql_query(sql,con=connection)
    else:
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()

    if internal_cursor:
        connection.close()

    if result:
        return df
    else:
        return
