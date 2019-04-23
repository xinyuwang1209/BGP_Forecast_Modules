#! /usr/bin/env python3

import dash
# import dash_daq as daq
from dash.dependencies import Output, Event
import json
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import plotly.figure_factory as ff
# import numpy as np
import copy
import requests
# from scipy.cluster.hierarchy import dendrogram, linkage

app = dash.Dash(__name__)
server = app.server

# asns = pd.read_csv('/var/www/html/vi/asns.csv')



fake = True
def gen_url(url_prefix,asn,length):
    return '/'.join([url_prefix,str(asn),str(length)]) + '/'


# def get_data(asn):


policies = ['deprefer', 'rov', 'simpleTimeHeuristic']
policies_checklist = [{'label': policy, 'value': policy} for policy in policies]
asns = [1111,2222]
asns_dropdown =    [{'label': asn, 'value': asn} for asn in asns]
results = ['hijackedAndBlocked', 'hijackedButNotBlocked', 'neitherBlockedNorHijacked', 'notHijackedButBlocked']

#
url = "http://inndrugcs.uconn.edu:5000/asn_history/1111/all/20/"
params = {'accept': 'application/json'}
rhtml = requests.get(url,params=params)
data = rhtml.json()
# with open('save.txt') as json_file:
#     data = json.load(json_file)

time = data['1111']['timestamps']


#

# print(time)
df_dict = {}
for policy in policies:
    df_dict[policy] = []
    current = data['1111']['history'][policy]
    for result in results:
        if fake:
            df_dict[policy].append(
                {'x': time,
                 'y': current[result],
                 'type': 'Scatter',
                 'mode': 'lines+markers',
                 'name': result
                 }
            )
        else:
            df_dict[policy].append(
                {'x': time,
                 'y': current[result],
                 'type': 'Scatter',
                 'mode': 'lines+markers',
                 'name': result
                 }
            )


app.layout = html.Div([
            dcc.Dropdown(options=asns_dropdown,value=1111),
            dcc.Checklist(
                options=policies_checklist,values=policies,
                labelStyle={'display': 'inline-block'}
            ),
            dcc.RangeSlider(
                marks={i: 'Label {}'.format(i) for i in range(-5, 7)},
                min=-5,
                max=6,
                value=[-3, 4]
            ),
            dcc.Graph(
                id=policies[0],
                figure = {'data': df_dict[policies[0]],
                           'layout': {'title': policies[0]}}
            ),
            dcc.Graph(
                id=policies[1],
                figure = {'data': df_dict[policies[0]],
                           'layout': {'title': policies[1]}}
            ),
            dcc.Graph(
                id=policies[2],
                figure = {'data': df_dict[policies[0]],
                           'layout': {'title': policies[2]}}
            ),
            ],style={'width':'100%'})



def




@app.callback(Output(policies[0], 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    satellite = Orbital('TERRA')
    data = {
        'time': [],
        'Latitude': [],
        'Longitude': [],
        'Altitude': []
    }

    # Collect some data
    for i in range(180):
        time = datetime.datetime.now() - datetime.timedelta(seconds=i*20)
        lon, lat, alt = satellite.get_lonlatalt(
            time
        )
        data['Longitude'].append(lon)
        data['Latitude'].append(lat)
        data['Altitude'].append(alt)
        data['time'].append(time)

    # Create the graph with subplots
    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}

    fig.append_trace({
        'x': data['time'],
        'y': data['Altitude'],
        'name': 'Altitude',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 1, 1)
    fig.append_trace({
        'x': data['Longitude'],
        'y': data['Latitude'],
        'text': data['time'],
        'name': 'Longitude vs Latitude',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 2, 1)

    return fig




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
