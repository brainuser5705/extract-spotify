"""
Ashley Liew
Extract Spotify main.py script
"""

from bokeh.plotting import figure
import pandas as pd
import numpy as np
from bokeh.io import curdoc
from bokeh.models import Select, ColumnDataSource, FileInput, HoverTool, DataTable, TableColumn, DateFormatter
from bokeh.layouts import column, row
import json
from base64 import b64decode
from datetime import time
from zipfile import ZipFile
import os

# These are the intital empty widgets when the server first loads
file_input = FileInput(accept='.json, .zip')
artist_plot = figure(title='Artist X Stream Time', plot_width=1500)
select_artist =  Select(title='Select an Artist', value="", options=[])
track_plot = figure(title='Track X Stream Time', plot_width=1500)
select_track = Select(title='Select a Track', value="", options=[])

# Adds the empty widgets to the document
layout = column(row(file_input), row(select_artist), row(artist_plot), row(select_track), row(track_plot))
curdoc().add_root(layout)


def read_file(attrname, old, new):
    """
    Takes the file from file input and converts into a JSON string
    """

    try:
        os.remove('temp.zip')
    except:
        pass

    bs64_str = file_input.value
    if file_input.filename.endswith('.json'):
        json_file = json.dumps(json.loads(b64decode(bs64_str)))
        generate_plots(json_file)
    elif file_input.filename.endswith('.zip'):
        zip_b64 = b64decode(bs64_str)
        temp = ZipFile('temp.zip', 'x')
        temp.writestr('file.zip', zip_b64)
        with ZipFile('temp.zip') as temp_file:
            directory = temp_file.infolist()
            for file in directory:
                if 'StreamingHistory0.json' in file.filename:
                    json_file = temp_file.open(file.filename)
        # decodes base64 string, loads into list, convert into string
                    generate_plots(json_file)
file_input.on_change('value', read_file)


def generate_plots(file):
    """
    Generates the plots and widgets
    """
    data = pd.read_json(file)

    # Reconfigures data 
    data['msPlayed'] = data['msPlayed']/60000
    data = data.rename(columns={'msPlayed' : 'minPlayed'})
    data['endTime'] = np.array(data['endTime'], dtype=np.datetime64) # convert to datetime object
    data['endTime'] = data['endTime'].astype('M8[D]')
    
    # This is the hover tool for all stream time plots:
    STREAMTIME_HOVER = HoverTool(
        tooltips = [
            ('Date', '@endTime{%F}'),
            ('Minutes Played', '@minPlayed'),
        ],

        formatters = {
            '@endTime' : 'datetime',
        },

        mode='mouse'
    )
    

    """Artist and Stream Time Plot"""

    artist_df= data.groupby(['endTime', 'artistName'], as_index=False)['minPlayed'].sum()

    artist_list = list(pd.unique(artist_df['artistName']))

    select_artist =  Select(title='Select an Artist', value=artist_list[0], options=artist_list)

    selected_artist = artist_df[artist_df['artistName'] == artist_list[0]] # setting initial plot shown
    artist_source = ColumnDataSource(data=selected_artist)

    artist_plot = figure(title='Artist X Stream Time', toolbar_location='above', x_axis_type='datetime', plot_width=1500)
    artist_plot.tools.append(STREAMTIME_HOVER)
    artist_plot.xaxis.axis_label = 'Time'
    artist_plot.yaxis.axis_label = 'Minutes Played'
    artist_plot.vbar(x='endTime', top='minPlayed', source=artist_source, width=time(16,0,0))
    

    """Track and Stream Time Plot"""

    track_df= data.groupby(['endTime', 'artistName', 'trackName'], as_index=False)['minPlayed'].sum()
    artist_track_df = track_df[track_df['artistName'] == artist_list[0]] # tracks must be from selected artist, intially set to the first artist

    track_list = list(pd.unique(artist_track_df['trackName']))

    select_track = Select(title="Select a Track", value=track_list[0], options=track_list)

    selected_track = artist_track_df[artist_track_df['trackName'] == track_list[0]]
    track_source = ColumnDataSource(data=selected_track)

    track_plot = figure(title='Track X Stream Time', toolbar_location="above", x_axis_type='datetime', plot_width=1500)
    track_plot.tools.append(STREAMTIME_HOVER)
    track_plot.xaxis.axis_label = 'Time'
    track_plot.yaxis.axis_label = 'Minutes Played'
    track_plot.vbar(x='endTime', top='minPlayed', source=track_source, width=time(16,0,0))


    """When select widgets are updated"""

    def update_track_select(attrname, old, new):
        artist_track_df = track_df[track_df['artistName'] == select_artist.value] # linked to artist graph
        track_list = list(pd.unique(artist_track_df['trackName']))
        select_track.options = track_list # update options for select_track widget with new selected artist
        select_track.value = track_list[0]

    def update_track_plot(attrname, old, new):
        artist_track_df = track_df[track_df['artistName'] == select_artist.value]
        selected_track = artist_track_df[artist_track_df['trackName'] == select_track.value]
        track_source.data = selected_track
    select_track.on_change('value', update_track_plot)

    def update_artist_plot(attrname, old, new):
        selected_artist = artist_df[artist_df['artistName'] == select_artist.value]
        artist_source.data = selected_artist # updates glyph artist_source
    select_artist.on_change('value', update_artist_plot)
    select_artist.on_change('value', update_track_select)


    # Creates a new layout with updated plots and widgets
    new_layout = column(row(file_input), row(select_artist), row(artist_plot), row(select_track), row(track_plot)) 
    layout.children = new_layout.children