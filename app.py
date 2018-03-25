from __future__ import (absolute_import, division, print_function)

import numpy as np
import pandas as pd
import requests

from bokeh.plotting import figure
# from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, LinearAxis, Range1d, DatetimeTickFormatter, HoverTool
from bokeh.models.widgets import Select, TextInput
from bokeh.embed import components
from flask import Flask, render_template, request, redirect
# from bokeh.io import output_notebook
# from bokeh.resources import INLINE
# from bokeh.plotting import show
# These were for notebook plotting. I am including them
# just in case I'm incorrect.


app = Flask(__name__)

ticker_frame = pd.DataFrame()

y_axis_map = {'Opening Price': 'open',
              'High': 'high',
              'Low': 'high',
              'Closing Price': 'close',
              'Volume': 'volume',
              'Ex-Dividend': 'ex-dividend',
              'Split Ratio': 'split_ratio',
              'Adjusted Opening Price': 'adj_open',
              'Adjusted High': 'adj_high',
              'Adjusted Low': 'adj_low',
              'Adjusted Closing Price': 'adj_close',
              'Adjusted Volume': 'adj_volume'
              }

y_map_reverse = {val: key for
                 (key, val) in y_axis_map.items()}

color_map = {"Black": "black",
             "Gray": "gray",
             "Brown": "brown",
             "Maroon": "maroon",
             "Crimson": "crimson",
             "Red": "red",
             "Deep Pink": "deeppink",
             "Orchid": "orchid",
             "Coral": "coral",
             "Orange": "orange",
             "Gold": "gold",
             "Yellow": "yellow",
             "Green": "green",
             "Lime Green": "limegreen",
             "Dark Blue": "darkblue",
             "Navy": "navy",
             "Cadet Blue": "cadetblue",
             "Blue": "blue",
             "Aqua": "aqua",
             "Purple": "purple"
             }

color_map_reverse = {val: key for
                     (key, val) in color_map.items()}


@app.route('/', methods=['GET', 'POST'])
def index():
    tic_1 = request.args.get("ticker_1")
    y_1 = request.args.get("y_axis_1")
    c_1 = request.args.get("color_1")
    tic_2 = request.args.get("ticker_2")
    y_2 = request.args.get("y_axis_2")
    c_2 = request.args.get("color_2")
    d_s = request.args.get("date_start")
    d_e = request.args.get("date_end")

    if tic_1 is None:
        tic_1 = "GOOG"
    if tic_2 is None:
        tic_2 = "FB"
    if y_1 is None:
        y_1 = "Closing Price"
    if y_2 is None:
        y_2 = "Closing Price"
    if c_1 is None:
        c_1 = "Blue"
    if c_2 is None:
        c_2 = "Crimson"
    if d_s is None:
        d_s = "1984-09-07"
    if d_e is None:
        d_e = "2018-03-21"

    # Now update values:
    update_parameters(tic_1, y_1, c_1, tic_2, y_2, c_2, d_s, d_e)
    # With values updated, we need to re-draw the plot:
    plot = create_figure()

    script, div = components(plot)

    return render_template("index.html", script=script, div=div,
                           # options for axes and colors
                           axis_opts=sorted(y_axis_map.keys()),
                           color_opts=color_map.keys(),
                           ticker_1_cur=ticker_1.value,
                           y_axis_1_cur=y_axis_1.value,
                           color_1_cur=color_1.value,
                           ticker_2_cur=ticker_2.value,
                           y_axis_2_cur=y_axis_2.value,
                           color_2_cur=color_2.value,
                           date_start_cur=date_start.value,
                           date_end_cur=date_end.value
                           )


# @app.route('/about')  # means that the URL '.../about' should trigger this function
# def about():
#     return render_template('about.html')


# Blind code copy

# We are going to have some trouble using these selectors with our HTML tools
date_start = TextInput(title="Date Range (yyyy-mm-dd)",
                       value='1984-09-07',
                       placeholder='1984-09-07')
date_end = TextInput(value='2018-03-21',
                     placeholder='2018-03-21')
# A date picker widget exists, but I...kind of hate those.
ticker_1 = TextInput(title="Stock Ticker Symbol 1", value='GOOG')
y_axis_1 = Select(title="Y Axis", options=sorted(y_axis_map.keys()),
                  value='Closing Price')
color_1 = Select(title="Line Color", options=color_map.keys(),
                  value='Blue')

ticker_2 = TextInput(title="Stock Ticker Symbol 2", value='GOOGL')
y_axis_2 = Select(title="Y Axis", options=sorted(y_axis_map.keys()),
                  value='Closing Price')
color_2 = Select(title="Line Color", options=color_map.keys(),
                  value='Crimson')

source_1 = ColumnDataSource(data=dict(x=[], y=[],  # lcolor='blue', this doesn't go here
                                      ticker_name=[],
                                      op_price=[],
                                      hi=[],
                                      lo=[],
                                      cl_price=[],
                                      date=[]))
source_2 = ColumnDataSource(data=dict(x=[], y=[],  # lcolor='crimson',
                                      ticker_name=[],
                                      op_price=[],
                                      hi=[],
                                      lo=[],
                                      cl_price=[],
                                      date=[]))


def update_parameters(tic_1, y_1, col_1, tic_2, y_2, col_2, sta, stp):
    # global ticker_1, y_axis_1, color_1, ticker_2, y_axis_2, color_2, date_start, date_end
    # Given how I used source_1 in update(), I don't need to
    # declare these globals.

    ticker_1.value = tic_1
    y_axis_1.value = y_1
    color_1.value = col_1
    ticker_2.value = tic_2
    y_axis_2.value = y_2
    color_2.value = col_2
    date_start.value = sta
    date_end.value = stp


def select_data():  # Refer to notebook for comments
    # I think we can keep our TextInputs and Selects, but we have
    # to modify their values in non-standard ways.
    # It's not clean, but we really don't want to change this code
    # in case we decide later to just use a Bokeh server.
    # The new function will be written above.
    date_start_val = date_start.value
    date_end_val = date_end.value
    ticker_1_val = ticker_1.value
    ticker_2_val = ticker_2.value

    if (np.array(date_end_val, dtype="datetime64[D]")
            - np.array(date_start_val, dtype="datetime64[D]")
        ).astype("float") < 0:
        date_end_val = date_start_val

    try:
        np.arange(date_start_val, date_end_val, dtype="datetime64[D]")
    except (ValueError, MemoryError):
        date_start_val = date_start.placeholder
        date_end_val = date_end.placeholder

    if not (ticker_1_val in ticker_frame.ticker.values):
        ticker_1_val = "GOOG"
    selected_1 = ticker_frame[  # Boolean selections go here
        (ticker_frame.ticker == ticker_1_val)
    ]
    # Limit the data range
    selected_1 = selected_1[selected_1.date.isin(
        np.arange(date_start_val, date_end_val, dtype="datetime64[D]"))]

    if not (ticker_2_val in ticker_frame.ticker.values):
        ticker_2_val = "FB"
    selected_2 = ticker_frame[
        (ticker_frame.ticker == ticker_2_val)
    ]
    selected_2 = selected_2[selected_2.date.isin(
        np.arange(date_start_val, date_end_val, dtype="datetime64[D]"))]

    return selected_1, selected_2


def update(p):
    df1, df2 = select_data()

    x_name_1 = "date"
    y_name_1 = y_axis_map[y_axis_1.value]
    line_color_1 = color_map[color_1.value]

    x_name_2 = "date"
    y_name_2 = y_axis_map[y_axis_2.value]
    line_color_2 = color_map[color_2.value]

    # I can't figure out how to access the second plot's y-axis
    # It looks like there is no way, but the docs just don't tell you.
    # So we may only be able to set it once. This is ridiculous, of course.

    p.xaxis.axis_label = "Date"
    p.yaxis[0].axis_label = y_axis_1.value
    p.yaxis[0].axis_label_text_color = line_color_1
    p.yaxis[1].axis_label = y_axis_2.value
    p.yaxis[1].axis_label_text_color = line_color_2
    p.title.text = "{}: {}, and {}: {}".format(
        ticker_1.value,
        y_axis_1.value,
        ticker_2.value,
        y_axis_2.value
    )

    source_1.data = dict(
        x=df1[x_name_1],
        y=df1[y_name_1],
        ticker_name=df1['ticker'],
        op_price=df1['open'],
        hi=df1['high'],
        lo=df1['low'],
        cl_price=df1['close'],
        date=df1['date'],
        date_str=df1['date_str']
    )

    source_2.data = dict(
        x=df2[x_name_2],
        y=df2[y_name_2],
        ticker_name=df2['ticker'],
        op_price=df2['open'],
        hi=df2['high'],
        lo=df2['low'],
        cl_price=df2['close'],
        date=df2['date'],
        date_str=df2['date_str']
    )


def reload_ticker_data(p):
    global ticker_frame
    url_1 = (r"https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?ticker="
             + ticker_1.value + "&api_key=Ag7zcnbbYyMz-cTAFdR2"
             )
    url_2 = (r"https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?ticker="
             + ticker_2.value + "&api_key=Ag7zcnbbYyMz-cTAFdR2"
             )
    resp_1 = requests.get(url_1)
    resp_2 = requests.get(url_2)
    data_1 = resp_1.json()
    data_2 = resp_2.json()
    col_names = [r['name'] for r in data_1['datatable']['columns']]
    column_data = data_1['datatable']['data']  # data['datatable']['data']
    column_data.extend(data_2['datatable']['data'])

    ticker_frame = pd.DataFrame(column_data, columns=col_names)
    ticker_frame['date_str'] = ticker_frame.date.copy()
    ticker_frame.date = ticker_frame.date.astype('datetime64[D]')

    # Can add functionality for initial load too, if desired.
    update(p)


# This is entirely useless as all of our controls need to be
# drawn in HTML
# controls = [ticker_1, y_axis_1, color_1,
#             ticker_2, y_axis_2, color_2,
#             date_start, date_end]
#
# for control in controls:
#     control.on_change('value', lambda attr, old, new: update())


def ticker_update(p):
    reload_ticker_data(p)


# controls[0].on_change('value', lambda attr, old, new: ticker_update())
# controls[3].on_change('value', lambda attr, old, new: ticker_update())

# HERE is everything we do to draw the plot
def create_figure(*args):
    line_width = 2
    hover = create_hover_tool()
    p = figure(plot_height=600, plot_width=700, title="",
               toolbar_location=None, tools=[hover,])
    # Remove the hover tool, I think.

    p.xaxis.formatter = DatetimeTickFormatter(
            hours=["%d %B %Y"],
            days=["%d %B %Y"],
            months=["%d %B %Y"],
            years=["%d %B %Y"],
        )
    p.extra_y_ranges = {"data_set_2": Range1d(start=0, end=200)}
    p.add_layout(LinearAxis(y_range_name="data_set_2"), 'right')

    line_1 = p.line(x="x", y="y", source=source_1, line_width=line_width,
                    line_color=color_1.value, name="data_set_1")
    line_2 = p.line(x="x", y="y", source=source_2, line_width=line_width,
                    line_color=color_2.value, name="data_set_2")

    ticker_update(p)

    return p


def create_hover_tool():
    hover_html = """
        <div>
            <span class="hover-tooltip">IDX: @ticker_name</span>
            <br>
            <span class="hover-tooltip">Year, Y-axis: @date_str, $y</span>
            <br>
            <span class="hover-tooltip">Opening Price: @op_price</span>
            <br>
            <span class="hover-tooltip">High: @hi</span>
            <br>
            <span class="hover-tooltip">Low: @lo</span>
            <br>
            <span class="hover-tooltip">Closing Price: @cl_price</span>
        </div>     
    """
    return HoverTool(tooltips=hover_html)


# This hover tool has to be changed entirely and rendered in html
# hover = HoverTool(tooltips=[
#     ("IDX", "@ticker_name"),
#     ("Year, Y-axis", "@date, $y"),
#     ("Opening Price", "@op_price"),
#     ("High", "@hi"),
#     ("Low", "@lo"),
#     ("Closing Price", "@cl_price")
# ])

# sizing_mode = 'fixed'
# inputs = widgetbox(*controls, sizing_mode=sizing_mode)
# l = layout([
#     [inputs, p]
# ], sizing_mode=sizing_mode)


if __name__ == '__main__':
    app.run(port=33507)
