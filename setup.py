'''
setup.py - a setup script
Author: Xinyu Wang
'''

try:
    from setuptools import setup
except ImportError:
	from distutils.core import setup

import os
import sys
import BGP_Forecast_Modules

try:
	setup(
		name=BGP_Forecast_Modules.__name__,
		version=BGP_Forecast_Modules.__version__,
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
		packages=['BGP_Forecast_Modules'],
		package_data = {
			'BGP_Forecast_Modules': ['config.ini']
		},
		# install_requirement=[
		# 	'requests',
		# 	'psycopg2',
		# 	'pathos'
		# ],
		)
finally:
	pass
