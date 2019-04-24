#!/usr/bin/python3.6
import sys

# add your project directory to the sys.path

# need to pass the flask app as "application" for WSGI to work
# for a dash app, that is at app.server
# see https://plot.ly/dash/deployment
from template1 import app
#from test import app
app.config.requests_pathname_prefix = ''
server = app.server
# application = app
application = app.server
