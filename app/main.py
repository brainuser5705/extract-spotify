from bokeh.plotting import figure, output_file, show
import pandas as pd
import numpy as np
from bokeh.io import show, curdoc
from bokeh.models import CustomJS, Select, ColumnDataSource, FileInput
from bokeh.layouts import column, row

import json
from base64 import b64encode, b64decode

# initial empty display
file_input = FileInput(accept='.json')
p = figure(title='spotify data')
seelct_widget =  Select(title="Artist", value="", options=[])

# initial layout
layout = column(row(file_input), row(seelct_widget), row(p))
curdoc().add_root(layout)


def read_file(attrname, old, new):
    # decodes file into JSON string
    bs64_str = file_input.value
    json_file = json.dumps(json.loads(b64decode(bs64_str)))
    # decodes base64 string, loads into list, convert into string
    generate_data(json_file)
file_input.on_change('value', read_file)


def generate_data(file):
    #generates plot and updates document
    data = pd.read_json(file)

    df = data
    df['msPlayed'] = df['msPlayed']/60000
    df = df.rename(columns={'msPlayed' : 'minPlayed'})

    df['endTime'] = np.array(df['endTime'], dtype=np.datetime64).astype('M8[D]')
    df= df.groupby(['endTime', 'artistName'], as_index=False)['minPlayed'].sum()

    artist_list = list(pd.unique(df['artistName'])) # generates list of unique artist in df
    seelct_widget =  Select(title="Artist", value="", options=artist_list) # select widget options are updated

    artistData = df[df['artistName'] == artist_list[0]]
    source = ColumnDataSource(data=artistData)
    p = figure(title='Spotify Data', x_axis_type='datetime')
    p.circle(x='endTime', y="minPlayed", source=source, width=0.2)

    new_layout = column(row(file_input), row(seelct_widget), row(p)) #creates a new layout with updated values
    layout.children = new_layout.children

    def update_plot(attrname, old, new):
        artistData = df[df['artistName'] == seelct_widget.value]
        source.data = artistData # updates glyph source
    seelct_widget.on_change('value', update_plot)
