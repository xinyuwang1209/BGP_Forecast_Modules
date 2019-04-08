#!/usr/bin/env python3
import os
import configparser
# from argparser import ArgumentParser

from .ROAs_Collector import ROAs_Collector
from .Utilities import *
from .Database import *
__author__ = "Xinyu Wang"

# from .What_If_Analysis_Evaluator    import What_If_Analysis_Evaluator

class BGP_Forecast_Modules():
    def __init__(self,config=None):
        if config is None:
            self.reset_config_default()
        else:
            self.config = config
        self.ROAs_Collector = ROAs_Collector(self.config)
        return

    def reset_config_default(self):
        self.config = configparser.ConfigParser()
        config_file = os.path.abspath(os.path.dirname(__file__)) + '/config.ini'
        self.config.read(config_file)
        return

    def get_config(self):
        return self.config

    def set_config(self,config):
        self.config = config
        return

        # Download and Store ROAs
    def run_ROAs_Collector(self):
        self.ROAs_Collector.init_roas_table()
        self.ROAs_Collector.store_ROAs(self.ROAs_Collector.download_ROAs())
        self.ROAs_Collector.create_index()

    def run_PyBGPExtrapolator(self):
        pass

    def run_What_If_Analysis_Evaluator(self):
        Instance = What_If_Analysis_Evaluator(self.config)
        Instance.analyze_all_asn_db()

# if __name__ == "__main__":
#     Instance = main()
#     Instance.run_What_If_Analysis_Evaluator()
