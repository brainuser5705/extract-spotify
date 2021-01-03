from bokeh.plotting import figure, output_file, show
import pandas as pd
import numpy as np
from bokeh.io import show, curdoc
from bokeh.models import CustomJS, Select, ColumnDataSource, FileInput, Title
from bokeh.layouts import column, row

import json
from base64 import b64encode, b64decode

# initial empty display
file_input = FileInput(accept='.json')

p = figure(title='Artist X Stream Time', plot_width=1500)
select_widget =  Select(title='Select an Artist', value="", options=[])
p2 = figure(title='Track X Stream Time', plot_width=1500)
track_select = Select(title='Select a Track', value="", options=[])

# initial layout
layout = column(row(file_input), row(select_widget), row(p), row(track_select), row(p2))



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

    data['msPlayed'] = data['msPlayed']/60000
    data = data.rename(columns={'msPlayed' : 'minPlayed'})

    data['endTime'] = np.array(data['endTime'], dtype=np.datetime64)
    data['endTime'] = data['endTime'].astype('M8[D]')
    
    #artist X stream time
    df= data.groupby(['endTime', 'artistName'], as_index=False)['minPlayed'].sum()

    artist_list = list(pd.unique(df['artistName'])) # generates list of unique artist in df
    select_widget =  Select(title='Select an Artist', value="", options=artist_list) # select widget options are updated

    artistData = df[df['artistName'] == artist_list[0]]
    source = ColumnDataSource(data=artistData)
    p = figure(title='Artist X Stream Time', toolbar_location='above', x_axis_type='datetime', plot_width=1500)
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Minutes Played'

    p.vbar(x='endTime', top='minPlayed', source=source, width=0.5)

    #track X stream time
    df2 = data.groupby(['endTime', 'trackName', 'artistName'], as_index=False)['minPlayed'].sum() #weird bug: have to include artistName to show up in table
    temp= df2[df2['artistName'] == artist_list[0]] # linked to artist graph

    track_list = list(pd.unique(temp['trackName']))

    track_select = Select(title="Select a Track", value='', options=track_list)

    trackData = temp[temp['trackName'] == track_list[0]]
    trackSource = ColumnDataSource(data=trackData)
    p2 = figure(title='Track X Stream Time', toolbar_location="above", x_axis_type='datetime', plot_width=1500)
    p2.xaxis.axis_label = 'Time'
    p2.yaxis.axis_label = 'Minutes Played'

    p2.vbar(x='endTime', top='minPlayed', source=trackSource, width=0.5)

    
    def update_track_plot(attrname, old, new):
        temp= df2[df2['artistName'] == select_widget.value] # linked to artist graph
        track_list = list(pd.unique(temp['trackName']))
        track_select.options = track_list # update options for track_select with new artist
        trackData = temp[temp['trackName'] == track_select.value]
        trackSource.data = trackData
    track_select.on_change('value', update_track_plot)

    def update_plot(attrname, old, new):
        artistData = df[df['artistName'] == select_widget.value]
        source.data = artistData # updates glyph source
    select_widget.on_change('value', update_plot)
    select_widget.on_change('value', update_track_plot)


    new_layout = column(row(file_input), row(select_widget), row(p), row(track_select), row(p2)) #creates a new layout with updated values
    layout.children = new_layout.children
