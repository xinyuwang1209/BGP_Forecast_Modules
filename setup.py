'''
setup.py - a setup script
Author: Xinyu Wang
'''

from setuptools import setup, find_packages

import os
import sys
# import BGP_Forecast_Modules

try:
	setup(
		name='BGP_Forecast_Modules',
		version='BGP_Forecast_Modules',
		author='Xinyu Wang',
		author_email='xinyuwang1209@gmail.com',
		description = ("BGP Forecast Project."),
		url='https://github.com/xinyuwang1209/BGP_Forecast_Modules.git',
		platforms = 'any',
		classifiers=[
			'Environment :: Console',
			'Intended Audience :: Developers',
			'License :: OSI Approved :: MIT License',
			'Operating System :: OS Independent',
			'Programming Language :: Python',
			'Programming Language :: Python :: 3'
		],
		keywords=['Xinyu, xinyu, pypi, package, rpki'],
		packages=find_packages(include=['BGP_Forecast_Modules', 'BGP_Forecast_Modules.*']),
		package_data = {
			'BGP_Forecast_Modules': ['config.ini']
		},
		# install_requires=[
		# 	'ipaddress',
		# 	'numpy',
		# 	'pandas',
		# 	'pathos',
        #     'pause',
		# 	'psycopg2',
        #     'python-daemon',
		# 	'requests',
		# 	'sqlalchemy'
		# ],
		)
finally:
	pass
