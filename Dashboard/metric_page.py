import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State
from server import app, redisUtil
import pandas as pd
import logging
logger = logging.getLogger(__name__)

from dash import dcc
import plotly.express as px
import plotly.graph_objs as go

 
from metric_page_details import get_metric_page_details
from metric_page_graph import get_metric_page_graph

def get_metric_page():
    
    res = html.Div([
    dcc.Tabs(
        id="tabs-with-classes",
        value='details',
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            dcc.Tab(
                label='Metric Details',
                value='details',
                className='custom-tab',
                selected_className='custom-tab--selected'
            ),
            dcc.Tab(
                label='Metric Plots',
                value='plots',
                className='custom-tab',
                selected_className='custom-tab--selected'
            ) 
        ]),
        html.Div(id='tabs-content-classes')
    ])
    return res

@app.callback(Output('tabs-content-classes', 'children'),
              Input('tabs-with-classes', 'value'))
def render_content(tab):
     
    if tab == 'details':
        return get_metric_page_details()
    elif tab == 'plots':
        return get_metric_page_graph()