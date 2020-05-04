import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from sql import *


external_stylesheets = [dbc.themes.LUX]
#external_stylesheets = ['static/lux.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def data2plot(poll_name, data):
    keys = ['x', 'y', 'name', 'connectgaps']
    poll_limits = {'SO2': 125, 'PM10': 50, 'PM2': 25, 'NO2': 200, 'CO': 10, 'O3': 180, 'C6H6': 5}
    start, end = data['Dates'][0], data['Dates'][-1]
    limit = poll_limits[poll_name]
    title = f'Concentration [{"mg" if poll_name == "CO" else "µg"}/m<sup>3</sup>]'
    plot_data = {'data': [dict(zip(keys, [data['Dates'], data[station], station, True]))
                          for station in data.keys()][1:]}
    plot_data['data'].append({'x': (start, end), 'y': (limit, limit),
                              'connectgaps': True, 'showlegend': False})
    plot_data['layout'] = {'title': poll_name,
                           'font': {'size': 15},
                           'xaxis': {'rangeslider': {'visible': True}},
                           'yaxis': {'title': title},
                           'plot_bgcolor': '#000',
                           'paper_bgcolor': '#fff',
                           'autosize': 'false'}
    return plot_data


poll_name = 'PM10'
data = select_last_month(poll_name)
data = data2plot(poll_name, data)
title = html.H1('Pollution in Milan', style={'backgroundColor': '#000', 'color': '#fff'})

dropdown = dbc.FormGroup(
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'Biossido di zolfo - SO2', 'value': 'SO2'},
            {'label': 'Polveri < 10 μm - PM10', 'value': 'PM10'},
            {'label': 'Polveri < 2 μm - PM2', 'value': 'PM2'},
            {'label': 'Biossido di azoto - NO2', 'value': 'NO2'},
            {'label': 'Monossido di carbonio - CO', 'value': 'CO'},
            {'label': 'Ozono - O3', 'value': 'O3'},
            {'label': 'Benzene - C6H6', 'value': 'C6H6'}],
        value=poll_name,
        searchable=False,
        clearable=False,
        style={'width': '300px'})
)

date_picker = dbc.FormGroup(
    dcc.DatePickerRange(id='date-picker',
                        display_format='DD-MM-YYYY',
                        start_date=datetime.today().date() - timedelta(days=32),
                        end_date=datetime.today().date() - timedelta(days=1),
                        max_date_allowed=datetime.today(),
                        updatemode='bothdates'),
    style={'font': {'size': 30}})


form = dbc.Form([
    dbc.Container([
        dbc.Row(
            [dbc.Col(html.Div('Select pollutant'), width={'size': 3, 'offset': 2}),
             dbc.Col(html.Div('Select dates'), width={'size': 3, 'offset': 2})],
        ),
        dbc.Row(
            [dbc.Col(html.Div(dropdown), width={'size': 3, 'offset': 2}),
             dbc.Col(html.Div(date_picker), width={'size': 3, 'offset': 2})]
        )
    ], fluid=True)
], inline=True)

graph = dbc.Container(
    dcc.Graph(figure=data,
              id='graph',
              config={'displayModeBar': False},
              style={'width': '180vh', 'height': '90vh'}),
    fluid=True)

app.layout = html.Div([
    title,
    form,
    dcc.Loading(children=graph,
                type='default')
], style={'backgroundColor': '#fff'})


@app.callback(
    Output('graph', 'figure'),
    [Input('dropdown', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')])
def update_poll(selected_poll, start_date, end_date):
    # Prevent the function to update onload
    if all(t['value'] is None for t in dash.callback_context.triggered):
        raise dash.exceptions.PreventUpdate
    if not start_date and not end_date:
        data = select_last_month(selected_poll)
        return data2plot(selected_poll, data)
    else:
        data = select_interval(selected_poll, start_date, end_date)
        return data2plot(selected_poll, data)


if __name__ == '__main__':
    app.run_server(port=5000, debug=True)
