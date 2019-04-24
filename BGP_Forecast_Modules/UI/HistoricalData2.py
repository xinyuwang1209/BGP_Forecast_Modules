#! /usr/bin/env python3

import copy

import datetime

import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html

# import dash_daq as daq
import json
import plotly.graph_objs as go
import pandas as pd
import plotly.figure_factory as ff
import numpy as np
import random
import requests
import time

app = dash.Dash(__name__)
server = app.server
# asns = pd.read_csv('/var/www/html/vi/asns.csv')


policies = ['deprefer', 'rov', 'simpleTimeHeuristic']
policies_checklist = [{'label': policy, 'value': policy} for policy in policies]
asns = pd.read_csv('extrapolation_asns.csv').values
asns_dropdown =    [{'label': asn, 'value': asn} for asn in asns]
results = ['hijackedAndBlocked', 'hijackedButNotBlocked', 'neitherBlockedNorHijacked', 'notHijackedButBlocked']


# api utilities

def gen_url(url_prefix,asn,length):
    return '/'.join([url_prefix,str(asn),str(length)]) + '/'

# fake utilities
fake = True
time_range = 45
today = datetime.datetime.now().date()
begin = datetime.datetime.now().date() - datetime.timedelta(days=time_range)
data_time = []
for i in range(time_range):
    data_time.append(begin + datetime.timedelta(days=i))


def fake_poly_generator(data_range=100,upper_bound = 20000):
    # random.seed(int(time.time()))
    mode = random.randint(0,2)
    lst = []
    a = random.randint(-data_range, data_range)
    b = random.randint(-data_range, data_range)
    c = random.randint(-time_range*2, time_range)
    print(a,b,c)
    for i in range(time_range):
        if mode == 0:
            lst.append(int(0))
        elif mode == 1:
            lst.append(int(0 + b * (c+i)))
        else:
            lst.append(int(0 + b * (c+i) + a * ((c+i) ** 2)))
    minimal = min(lst)
    maximum = max(lst)
    avg = sum(lst) // len(lst)
    rand_avg = random.randint(0,upper_bound)
    lst = [a - avg + rand_avg for a in lst]
    rand = random.randint(0,min(rand_avg,upper_bound-rand_avg))
    if upper_bound//2 < rand_avg:
        rate = (maximum - rand_avg) // rand
    else:
        rate = (rand_avg) // rand
    lst = [a//rate for a in lst]
    noise_range = (max(lst) - min(lst)) // 10 + 100
    # print(random.randint(-noise_range, noise_range))
    for i in range(time_range):
        lst[i] += random.randint(-noise_range, noise_range)
    minimal = min(lst)
    if minimal < 0:
        lst = [a - minimal for a in lst]
    return lst

def fake_data_generator():
    data = {}
    for policy in policies:
        current = {}
        for result in results:
            current[result] = fake_poly_generator()
        data[policy] = current
    return data



# def get_data(asn):



if fake:
    data = fake_data_generator()
    # print(data)
# #
# url = "http://bgpforecast.uconn.edu:5000/asn_history/1111/all/20/"
# params = {'accept': 'application/json'}
# rhtml = requests.get(url,params=params)
# data = rhtml.json()['1111']['history']
# # with open('save.txt') as json_file:
# #     data = json.load(json_file)
#
# # time = data['1111']['timestamps']


#

# print(time)
df_dict = {}
for result in results:
    df_dict[result] = []
    for policy in policies:
        df_dict[result].append(
            {'x': data_time,
             'y': data[policy][result],
             'type': 'Scatter',
             'mode': 'lines+markers',
             'name': policy
             # 'line': {'shape': 'spline', 'smoothing': 2}
             }
        )


hijackedAndBlocked =        dcc.Graph(
                                id=policies[0],
                                figure = {'data': df_dict[results[0]],
                                           'layout': {'title': results[0]}}
                            )

hijackedButNotBlocked =     dcc.Graph(
                                id=policies[1],
                                figure = {'data': df_dict[results[1]],
                                           'layout': {'title': results[1]}}
                            )

neitherBlockedNorHijacked = dcc.Graph(
                                id=results[2],
                                figure = {'data': df_dict[results[2]],
                                           'layout': {'title': results[2]}}
                            )

notHijackedButBlocked =     dcc.Graph(
                                id=results[3],
                                figure = {'data': df_dict[results[3]],
                                           'layout': {'title': results[3]}}
                            )

app.layout = html.Div([
            dcc.Dropdown(options=asns_dropdown,value=1111),
            dcc.Checklist(
                options=policies_checklist,values=policies,
                labelStyle={'display': 'inline-block'}
            ),
            dcc.RangeSlider(
                marks={i: 'Label {}'.format(i) for i in range(-5, 7)},
                min=0,
                max=6,
                value=[-3, 4]
            ),
            hijackedAndBlocked,
            hijackedButNotBlocked,
            neitherBlockedNorHijacked,
            notHijackedButBlocked,
            ],style={'width':'100%'})


# def


@app.callback(Output(policies[0], 'figure'),
              [Input('dropdown', 'value')])
#
# @app.callback(Output(policies[0], 'figure'),
#               [Input('interval-component', 'n_intervals')])
# def update_graph_live(n):
#     satellite = Orbital('TERRA')
#     data = {
#         'time': [],
#         'Latitude': [],
#         'Longitude': [],
#         'Altitude': []
#     }
#
#     # Collect some data
#     for i in range(180):
#         time = datetime.datetime.now() - datetime.timedelta(seconds=i*20)
#         lon, lat, alt = satellite.get_lonlatalt(
#             time
#         )
#         data['Longitude'].append(lon)
#         data['Latitude'].append(lat)
#         data['Altitude'].append(alt)
#         data['time'].append(time)
#
#     # Create the graph with subplots
#     fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
#     fig['layout']['margin'] = {
#         'l': 30, 'r': 10, 'b': 30, 't': 10
#     }
#     fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
#
#     fig.append_trace({
#         'x': data['time'],
#         'y': data['Altitude'],
#         'name': 'Altitude',
#         'mode': 'lines+markers',
#         'type': 'scatter'
#     }, 1, 1)
#     fig.append_trace({
#         'x': data['Longitude'],
#         'y': data['Latitude'],
#         'text': data['time'],
#         'name': 'Longitude vs Latitude',
#         'mode': 'lines+markers',
#         'type': 'scatter'
#     }, 2, 1)
#
#     return fig
#



external_css = ["https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "//fonts.googleapis.com/css?family=Raleway:400,300,600",
                "//fonts.googleapis.com/css?family=Dosis:Medium",
                "https://cdn.rawgit.com/plotly/dash-app-stylesheets/0e463810ed36927caf20372b6411690692f94819/dash-drug-discovery-demo-stylesheet.css"]


for css in external_css:
    app.css.append_css({"external_url": css})






# app.css.append_css({
#     'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
# })

if __name__ == '__main__':
        app.run_server()
