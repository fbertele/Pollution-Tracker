import plotly.graph_objects as go
import numpy as np
from sql import *

data = select_interval('PM10', '1-3-2020', '8-3-2020')
print(data)
print()


fig = go.Figure(data=go.Scatter(x=['a', 'b', 'c', 'd'],
                                y=[1, 2, None, 4], connectgaps=True))

keys = ['x', 'y', 'name', 'connectgaps']
data = [{k: v for k, v in zip(keys, [data['Dates'], data[station], station, True])}
        for station in data][1:]
print(data)
