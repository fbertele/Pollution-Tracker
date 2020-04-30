import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from sql import *


# external_stylesheets = ['static/style.css']
# external_stylesheets = [dbc.themes.BOOTSTRAP]
external_stylesheets = ['assets/lux.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def data2plot(poll_name, data):
    keys = ['x', 'y', 'name', 'connectgaps']
    poll_limits = {'SO2': 125, 'PM10': 50, 'PM2': 25, 'NO2': 200, 'CO': 10, 'O3': 180, 'C6H6': 5}
    start, end = data['Dates'][0], data['Dates'][-1]
    limit = poll_limits[poll_name]
    plot_data = {'data': [dict(zip(keys, [data['Dates'], data[station], station, True]))
                          for station in data.keys()][1:]}
    plot_data['data'].append({'x': (start, end), 'y': (limit, limit),
                              'connectgaps': True, 'showlegend': False})
    plot_data['layout'] = {'title': poll_name,
                           'xaxis': {'rangeslider': {'visible': True}},
                           'plot_bgcolor': '#000',
                           'paper_bgcolor': '#fff'}
    return plot_data


def load():

    poll_name = 'PM10'
    data = select_last_month(poll_name)
    data = data2plot(poll_name, data)

    title = html.Div(html.H1('Pollution in Milan', style={
                     'backgroundColor': '#000', 'color': '#fff'}))

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
                            updatemode='bothdates'))

    form = dbc.Container([
        dbc.Row(
            [dbc.Col(html.Div('Select pollutant'), align='start'),
             dbc.Col(html.Div('Select dates'), align='start')],
        ),
        dbc.Row(
            [dbc.Col(dropdown),
             dbc.Col(date_picker)],
        )
    ])

    graph = dcc.Graph(figure=data,
                      id='graph',
                      config={'displayModeBar': False})

    app.layout = html.Div([
        title,
        dbc.Form(children=form, inline=True),
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
    data = select_interval(selected_poll, start_date, end_date)
    return data2plot(selected_poll, data)


def main():
    load()


if __name__ == '__main__':
    main()
    app.run_server(port=5000, debug=True)
