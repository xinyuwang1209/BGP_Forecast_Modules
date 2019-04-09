#!/usr/bin/env python3
import os
import configparser
# from argparser import ArgumentParser

from .ROAs_Collector                import ROAs_Collector
from .What_If_Analysis_Evaluator    import What_If_Analysis_Evaluator
from .PyBGP_Extrapolator            import PyBGP_Extrapolator
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
        self.ROAs_Collector             = ROAs_Collector(self.config)
        self.What_If_Analysis_Evaluator = What_If_Analysis_Evaluator(self.config)
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

    def init_unique_prefix_origin_history_daemon(self):
        pass

    def run_PyBGP_Extrapolator(self):
        pass

    def run_What_If_Analysis_Evaluator(self,db=True):
        print_time('[run_What_If_Analysis_Evaluator] Starts.')
        start_time = time.time()
        self.What_If_Analysis_Evaluator.What_If_Analysis.init_what_if_analysis_db()
        if db:
            self.What_If_Analysis_Evaluator.analyze_all_asn_db()
        else:
            self.What_If_Analysis_Evaluator.analyze_all_asn_memory()
        print_time('[run_What_If_Analysis_Evaluator] Completed, elapsed time:',str(datetime.timedelta(seconds=time.time()-start_time))[:-6])
        return
