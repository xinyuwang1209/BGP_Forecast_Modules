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

updated = False

policies = ['deprefer', 'rov', 'simpleTimeHeuristic']
policies_checklist = [{'label': policy, 'value': policy} for policy in policies]
asns = pd.read_csv('extrapolation_asns.csv').values
asns_dropdown =    [{'label': asn, 'value': asn} for asn in asns]
results = ['hijackedAndBlocked', 'hijackedButNotBlocked', 'neitherBlockedNorHijacked', 'notHijackedButBlocked']
results_name = ['Hijacked And Blocked', 'Hijacked But Not Blocked', 'Neither Blocked Nor Hijacked', 'Not Hijacked But Blocked']


# api utilities

def gen_url(url_prefix,asn,length):
    return '/'.join([url_prefix,str(asn),str(length)]) + '/'


asn = 13335
# fake utilities
fake = True
time_range = 45
time_start = 0
time_end = time_range


def fake_poly_generator(time_start,time_end,data_range=100,upper_bound = 40000):
    # random.seed(int(time.time()))
    mode = random.randint(2,2)
    lst = []
    a = random.randint(-data_range, data_range)
    b = random.randint(-data_range, data_range)
    c = random.randint(-time_range*2, time_range)
    for i in range(time_end-time_start):
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
        rate = (rand_avg) // max(rand,1)
    lst = [a//max(rate,1) for a in lst]
    noise_range = (max(lst) - min(lst)) // 10 + 10
    # print(random.randint(-noise_range, noise_range))
    for i in range(time_end-time_start):
        lst[i] += random.randint(-noise_range, noise_range)
    minimal = min(lst)
    if minimal < 0:
        lst = [a - minimal for a in lst]
    return lst

def fake_data_generator(time_start,time_end):
    data = {}
    for policy in policies:
        current = {}
        for result in results:
            current[result] = fake_poly_generator(time_start,time_end)
        data[policy] = current
    return data

def data_time_generator(time_start,time_end):
    data_time = []
    begin = datetime.datetime.now().date() - datetime.timedelta(days=time_range+time_start)
    for i in range(time_end-time_start):
        data_time.append(begin + datetime.timedelta(days=i))
    return data_time

if fake:
    data = fake_data_generator(time_start,time_end)
    data_time = data_time_generator(time_start,time_end)
    data_time_part = data_time
    data_part = data

# def get_data(asn):
range_mark = {}
for i in range(time_range):
    if i % (time_range // 6) == 0:
        range_mark[i] = data_time[i]
    else:
        range_mark[i] = ''
# range_mark[time_range-1] = data_time[time_range-1]


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
def gen_df(d,dt):
    df_dict = {}
    for result in results:
        df_dict[result] = []
        for policy in policies:
            df_dict[result].append(
                {'x': dt,
                 'y': d[policy][result],
                 'type': 'Scatter',
                 'mode': 'lines+markers',
                 'name': policy,
                 'line': {'shape': 'spline', 'smoothing': 2}
                 }
            )
    return df_dict
df_dict = gen_df(data,data_time)


def update_data(time_start,time_end,d):
    new_d = {}
    for policy in policies:
        current = {}
        for result in results:
            current[result] = d[policy][result][time_start:time_end]
            new_d[policy] = current
    return new_d


hijackedAndBlocked =        dcc.Graph(
                                id=results[0],
                                figure = {'data': df_dict[results[0]],
                                           'layout': {'title': results_name[0],
                                           'font': dict(family='Courier New, monospace', size=12, color='#7f7f7f'),
                                                      'xaxis': {'autorange': True},
                                                      'yaxis': {'autorange': True},
                                                      'legend':dict(orientation="h")}},
                                animate=True
                            )

hijackedButNotBlocked =     dcc.Graph(
                                id=results[1],
                                figure = {'data': df_dict[results[1]],
                                           'layout': {'title': results_name[1],
                                           'font': dict(family='Courier New, monospace', size=12, color='#7f7f7f'),
                                                      'xaxis': {'autorange': True},
                                                      'yaxis': {'autorange': True},
                                                      'legend':dict(orientation="h")}},
                                animate=True
                            )

neitherBlockedNorHijacked = dcc.Graph(
                                id=results[2],
                                figure = {'data': df_dict[results[2]],
                                           'layout': {'title': results_name[2],
                                           'font': dict(family='Courier New, monospace', size=12, color='#7f7f7f'),
                                                      'xaxis': {'autorange': True},
                                                      'yaxis': {'autorange': True},
                                                      'legend':dict(orientation="h")}},
                                animate=True
                            )

notHijackedButBlocked =     dcc.Graph(
                                id=results[3],
                                figure = {'data': df_dict[results[3]],
                                           'layout': {'title': results_name[3],
                                           'font': dict(family='Courier New, monospace', size=12, color='#7f7f7f'),
                                                      'xaxis': {'autorange': True},
                                                      'yaxis': {'autorange': True},
                                                      'legend':dict(orientation="h")}},
                                animate=True
                            )

app.layout = html.Div([
            dcc.Dropdown(id='dropdown',
                         options=asns_dropdown,
                         multi=True,
                         value=[13335,1],
                         placeholder='Select an ASN'),
            html.Br(),
            html.Div([dcc.RangeSlider(
                id='rangeslider',
                min=0,
                max=time_range-1,
                # marks={i: data_time[i] for i in range(time_range)},
                marks=range_mark,
                value=[0, time_range-1]
            ),],style={'height':'50px','width':'90%','display': 'block','margin-right': 'auto','margin-left': 'auto'}),
            html.Br(),
            html.Div([hijackedAndBlocked,
                      hijackedButNotBlocked
                      ],style={'width': '49%', 'display': 'inline-block'}),
            html.Div([neitherBlockedNorHijacked,
                      notHijackedButBlocked,
                      ],style={'width': '49%', 'display': 'inline-block'}),
            ],style={'width':'100%', 'height':'100%'})


@app.callback(Output(results[0], 'figure'),
              [Input('dropdown', 'value'),Input('rangeslider', 'value')])
def ddupdate0(value1,value2):
    global updated
    updated = False
    global time_start
    global time_end
    print('values:',value2)
    a , b = value2
    time_start = a
    time_end = b+1
    print('values:',a)
    print('values:',b)
    global data
    global data_part
    global data_time
    global data_time_part
    # data_time = data_time_generator(time_end,time_end)

    global asn
    if asn == value1:
        data_time_part = data_time[time_start:time_end]
        data_part = update_data(time_start,time_end,data)
        print(len(data[policies[0]][results[0]]))
        print(len(data_part[policies[0]][results[0]]))
    else:
        data = fake_data_generator(0,time_range)
        data_part = update_data(time_start,time_end,data)
        asn = value1

    global df_dict
    df_dict = gen_df(data_part,data_time_part)
    updated = True
    return {'data': df_dict[results[0]],
               'layout': {'title': results_name[0],
                          'xaxis': {'autorange': True},
                          'yaxis': {'autorange': True}}}


@app.callback(Output(results[1], 'figure'),
              [Input(results[0], 'figure')])
def ddupdate1(value1):
    return {'data': df_dict[results[1]],
               'layout': {'title': results_name[1]}}

@app.callback(Output(results[2], 'figure'),
              [Input(results[1], 'figure')])
def ddupdate1(value1):
    return {'data': df_dict[results[2]],
               'layout': {'title': results_name[2]}}

@app.callback(Output(results[3], 'figure'),
              [Input(results[2], 'figure')])
def ddupdate1(value1):
    return {'data': df_dict[results[3]],
               'layout': {'title': results_name[3]}}

#



# @app.callback(Output('dropdown', 'value'), [Input('dropdown', 'options')])
# def callback(value):
#     return ""
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
