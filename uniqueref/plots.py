from bokeh.plotting import figure
from bokeh.models.widgets import Select
from bokeh.models import HoverTool, TapTool, OpenURL, Circle, Text, CustomJS, FixedTicker, ColumnDataSource, Legend
from bokeh.models.widgets import TableColumn, DataTable
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.layouts import column, row, layout, Row, Spacer, gridplot
import pandas as pd
import numpy as np
from django.contrib.auth.decorators import login_required
import operator
from math import pi
from globalvars import *
import math
from .models import Gene, IPSDatapoint, PSSDatapoint, Screen, Location
import sys
import custom_functions

import globalvars as gv

TOOLS = "resize,hover,save,pan,wheel_zoom,box_zoom,reset,tap"

##########################################################
# 1. Fishtail plots                                       #
##########################################################

def pfishtailplot(title, df, sag, oca, textsize, authorized_screens, legend=pd.DataFrame(), df_arrow=pd.DataFrame(),
                  setwidth=1000, setheight=700, legend_location="top_right", toolbar_location="below",
                  customtools='full_set'):

    if(customtools=='limited_set'):
        TOOLS = "resize,pan,wheel_zoom,box_zoom,tap,reset"
    else:
        TOOLS = "resize,hover,save,pan,wheel_zoom,box_zoom,reset,tap"

    absmin = np.absolute(df.min()['logmi'])
    absmax = np.absolute(df.max()['logmi'])
    if (absmin >= absmax):
        min = -absmin-(0.1*absmin)
        max = absmin+(0.1*absmin)
    else:
        min = -absmax-(0.1*absmax)
        max = absmax+(0.1*absmax)
    max_x = np.absolute(df.max()['loginsertions'])*1.05
    
    p = figure(
        width=setwidth,
        height=setheight,
        y_range=(min, max),
        x_range=(0, max_x),
        tools=[TOOLS],
        title=title,
        output_backend="webgl",
        x_axis_label = "Insertions [10log]",
        y_axis_label = "Mutational index [2log]"
    )

    # This is the place for some styling of the graph
    p.toolbar_location = toolbar_location
    p.outline_line_width = 3
    p.outline_line_alpha = 1
    p.outline_line_color = "black"
    p.line([0, 120],[0, 0], line_width=2, line_color="black")   # This actually is part of the data but it as it merely functions a accent if the x-axis, it is under the styling tab    
    
    # The hover guy
    hover = p.select(type=HoverTool)
    hover.tooltips = [
        ('P-Value', '@fcpv'),
        ('Gene', '@relgene'),
        ('Custom info', '@adddescription')
    ]            

    # Create a ColumnDataSource from the merged dataframa
    source = ColumnDataSource(df)          
    # Create a new dataframe and source that only holds the names and the positions of datapoints, used for labeling genes
    textsource = ColumnDataSource(data=dict(loginsertions=[], logmi=[], relgene=[]))
    # Define the layout of the circle (a Bokeh Glyph) if nothing has been selected, ie. the inital view
    initial_view = Circle(x='loginsertions', y='logmi', fill_color='color', fill_alpha=1, line_color='linecolor', size=5, line_width=1) # This is the initial view, if there's no labeling if genes, this is the only plot

    if sag == "on":
        p.text('loginsertions', 'logmi', text='signame', text_color='black', text_font_size=textsize, source=source)
    if oca == "hah": # If the 'on click action' is highlight and label
    # Start with creating an empty overlaying plot for the textlabels
        p.text('loginsertions', 'logmi', text='relgene', text_color='black', text_font_size=textsize, source=textsource) # This initally is an empty p because the textsource is empty as long as no hits have been selected
        # Define how the bokeh glyphs should look if selected
        selected_circle = Circle(fill_color='black', line_color='black', fill_alpha=1, line_alpha=1, size=5, line_width=1)
        # Define how the bokeh glyphs should look if not selected
        nonselected_circle = Circle(fill_color='color', line_color='linecolor', fill_alpha=transp_nsel_f, line_alpha=transp_nsel_l, size=5, line_width=1)
        
        source.callback = CustomJS(args=dict(textsource=textsource), code="""
            var inds = cb_obj.get('selected')['1d'].indices;
            var d1 = cb_obj.get('data');
            var d2 = textsource.get('data');
            d2['loginsertions'] = []
            d2['logmi'] = []
            d2['relgene'] = []
            for (i = 0; i < inds.length; i++) {
                d2['loginsertions'].push(d1['loginsertions'][inds[i]])
                d2['logmi'].push(d1['logmi'][inds[i]])
                d2['relgene'].push(d1['relgene'][inds[i]])
            }
            textsource.trigger('change');
        """)

    elif oca == "gc": # If linking out to genecards
        selected_circle = initial_view
        nonselected_circle = initial_view
            
        url = "http://www.genecards.org/cgi-bin/carddisp.pl?gene=@relgene"
        taptool = p.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

    # If linking out to geplots
    elif oca == "gp":
        selected_circle = initial_view
        nonselected_circle = initial_view

        url = custom_functions.create_gene_plot_url("@relgene", authorized_screens)
        taptool = p.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

    # Plot the final graph  
    p.add_glyph(
        source,
        initial_view,
        selection_glyph=selected_circle,
        nonselection_glyph=nonselected_circle
    )
    # When coloring the dots by track, create legend that tells which color is which track  
    if (not legend.empty):
        legend = Legend(items=[(r[1], [p.circle(x=0, y=0, color=r[2])]) for r in legend.itertuples()],location=legend_location)
        if (legend_location!='top_right'):
            p.add_layout(legend, 'right')
        else:
            p.add_layout(legend)

    if (not df_arrow.empty):
        linesource = ColumnDataSource(df_arrow)
        for r in df_arrow.itertuples():
            p.line([r[3], r[4]], [r[1], r[2]], color=r[7], line_width=4)
        p.text(x='loginsertions_x', y='logmi_x', text='relgene_x', color='black', text_font_size=textsize, source=linesource)

    r = row(children=[p], responsive=True)

    return r

##########################################################
# 2. Bubble plots for positive selection screens         #
##########################################################

def pbubbleplot(title, df, scaling, oca, sag, textsize, authorized_screens):
    # In the positive selection bubbleplot the following is plotted along the axis
    # x = seq
    # y = logfcpv

    # Adjust plot attributes according to desired y-scaling
    if scaling=='log':
        ymin = .008
        ymax = 11
        yat="log"
#       df = df[(df['yval'] >= 0.01) & (df['yval'] <= 10)]
    else:
        ymin = -15
        ymax = 375
        hw=True
        yat='linear'

    p = figure(
        width=bubbleplotwidth,
        height=bubbleplotheight,
        y_range=(ymin,ymax),
        x_range=(0-0.05*len(df.index), 1.05*len(df.index)),
        tools=[TOOLS],
        title=title,
        output_backend="webgl",
        x_axis_label = "Genes",
        y_axis_label = '-log(p)',
        y_axis_type = yat,
        toolbar_location = 'above',
    )

    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.xaxis[0].ticker=FixedTicker(ticks=[])

    # The hover guy
    hover = p.select(type=HoverTool)
    hover.tooltips = [
        ('P-Value', '@fcpv'),
        ('Gene', '@relgene'),
        ('Insertions','@nm')
    ]

    # Create a new dataframe and source that only holds the names and the positions of datapoints, used for labeling genes
    textsource = ColumnDataSource(data=dict(txval=[], tyval=[], relgene=[]))
    # Build a ColumnDataSource from the Pandas dataframe required for Bokeh
    source = ColumnDataSource(df)
    # Define the layout of the circle (a Bokeh Glyph) if nothing has been selected, ie. the inital view
    initial_view = Circle(x='xval', y='yval', fill_color='color', line_color='black', fill_alpha=0.9, line_alpha=0.9, size='dotsize') # This is the initial view, if there's no labeling if genes, this is the only plot
    
    # In case all significant hits needs to be labled
    if sag == "on":
        p.text('txval', 'tyval', text='signame', text_color='black', text_font_size=textsize, source=source)

    if oca == "hah": # If the 'on click action' is highlight and label (hah)
        # Define how the bokeh glyphs should look if selected
        selected_circle = Circle(fill_alpha=0.9, size='dotsize', line_color='#000000', fill_color='color')
        # Define how the bokeh glyphs should look if not selected
        nonselected_circle = Circle(fill_alpha=0.5, size='dotsize', line_color='#000000', fill_color='color', line_alpha=0.5)
        # Start with creating an empty overlaying plot for the textlabels
        p.text('txval', 'tyval', text='relgene', text_color='black', text_font_size=textsize, source=textsource) # This initally is an empty p because the textsource is empty as long as no hits have been selected
        
        source.callback = CustomJS(args=dict(textsource=textsource), code="""
            var inds = cb_obj.get('selected')['1d'].indices;
            var d1 = cb_obj.get('data');
            var d2 = textsource.get('data');
            d2['txval'] = []
            d2['tyval'] = []
            d2['relgene'] = []
            for (i = 0; i < inds.length; i++) {
                d2['txval'].push(d1['txval'][inds[i]])
                d2['tyval'].push(d1['tyval'][inds[i]])
                d2['relgene'].push(d1['relgene'][inds[i]])
            }
            textsource.trigger('change');
        """)

        # If linking out to genecards
    elif oca == "gc": 
        selected_circle = initial_view
        nonselected_circle = initial_view

        url = "http://www.genecards.org/cgi-bin/carddisp.pl?gene=@relgene"
        taptool = p.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

        # If linking out to geplots
    elif oca == "gp":
        selected_circle = initial_view
        nonselected_circle = initial_view

        url = custom_functions.create_gene_plot_url("@relgene", authorized_screens)
        taptool = p.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

    # Plot the final graph
    p.add_glyph(
        source,
        initial_view,
        selection_glyph=selected_circle,
        nonselection_glyph=nonselected_circle
    )

    r = row(children=[p], responsive=True)
    return r

##########################################################
# 3. Single gene plots (genefinder histogram things)     #
##########################################################


def single_gene_plots(genes_df, screenids_array, pvcutoff, authorized_screens, plot_width, legend=False):
    # A limited set of tools
    TOOLS = "resize,save,pan,wheel_zoom,box_zoom,reset"
    # The labels for the x-axis
    x_range = [str(x[0]) for x in custom_functions.authorized_qs_screen(authorized_screens).filter(id__in=screenids_array).order_by('name').values_list('name')]
    # Now we create a dictionary that uses the genenames to create variables. An sich this is a nice approach but because dictionaries are intrinsically unsorted, the plots will have an unsorted order in which they appear under each other
    figures = {name: 0 for name in genes_df['relgene']}
    # Now we create another empty array, which will hold the actual plotobjects instead of the variables
    # The reason for restructing like this is that bokeh gridplot can only handle an array of plot objects, and certainly not a dict of variables
    full_df = custom_functions.df_multiple_geneplot(genes_df['relgene'].values.tolist(), screenids_array, pvcutoff, authorized_screens)
    calculated_plot_width = custom_functions.calc_geneplot_width(plot_width, len(x_range))
    plot_dict = {}
    for y in figures:
        df = full_df[full_df['relgene']==y]
        title=y+(genes_df[genes_df['relgene']==y]['adddescription'].values[0])
        source = ColumnDataSource(df)
        # This gives optimal separation of the datapoints but 0 is not always in the middle (or present at all!)... would that be desirable?
        absmin = np.absolute(df['logmi'].min())
        absmax = np.absolute(df['logmi'].max())
        if (absmin >= absmax):
            min = -absmin-(0.1*absmin)
            max = absmin+(0.1*absmin)
        else:
            min = -absmax-(0.1*absmax)
            max = absmax+(0.1*absmax)
        figures[y] = figure(
            width=calculated_plot_width,
            height=400,
            y_range=(min, max),
            x_range=x_range,
            tools=[TOOLS],
            title=title,
            min_border_left=65,
            min_border_top=45,
            toolbar_location='above',
            sizing_mode = 'scale_both'
        )
        figures[y].circle('relscreen', 'logmi', color='color', alpha=1, source=source, size=10)
        figures[y].xaxis.major_label_orientation = pi/4
        # The hover guy
        hover = figures[y].select(type=HoverTool)
        hover.tooltips = [
            ('P-Value', '@fcpv'),
            ('log(MI)', '@logmi'),
            ('Screen', '@relscreen'),
        ]

        if legend:
            legend = Legend(items=[
                ('Pos. reg', [figures[y].circle(x=0, y=0, color=gv.color_sb)]),
                ('Neg. reg', [figures[y].circle(x=0, y=0, color=gv.color_st)]),
                ('Not sign', [figures[y].circle(x=0, y=0, color=gv.color_ns)])],
                location='top_right',
                orientation = 'horizontal',
                background_fill_alpha = 0.1,
                background_fill_color = gv.legend_background,
                border_line_width = 1,
                border_line_color = "black",
                border_line_alpha = 0.3
            )
            figures[y].add_layout(legend)

        plot_dict[y]=figures[y]
    return(plot_dict.values())

##########################################################
# 4. Veritical layout of geneplots          #
##########################################################
def vertial_geneplots_layout(list_of_geneplot_objects):
    return(column(list_of_geneplot_objects, responsive=True))
##########################################################
# 4. Plot a table
##########################################################
def create_table_plot(table_data):
    table_data_dict = ColumnDataSource(dict(seq=table_data.keys(),count=table_data.values()))
    columns = [
        TableColumn(field="seq", title="Sequenceread"),
        TableColumn(field="count", title="Count", width=80, default_sort='descending'),
    ]
    tableplot = DataTable(source=table_data_dict, columns=columns, width=700, height=280)
    return tableplot

##########################################################
# 6. A general scatter plot with screens on X-axis and   #
# values a Y-axis                                        #
# This is a more general form of the single geneplot...  #
# these could be merged one day                          #
##########################################################
def cross_screen_scatter(dataframe, title, plot_width, x_range, legend=pd.DataFrame()):
    calculated_plot_width = custom_functions.calc_geneplot_width(plot_width, len(x_range))
    p = figure(
        width=calculated_plot_width,
        height=400,
        y_range=(0.01*min(dataframe['yval'].values), 1.1*max(dataframe['yval'].values)),
        x_range=x_range,
        tools=[TOOLS],
        title=title,
        min_border_left=100,
    )
    p.xaxis.major_label_orientation = pi / 4
    source = ColumnDataSource(dataframe)
    print(dataframe)
    p.circle('relscreen', 'yval', color='color', source=source)
    legend = Legend(items=[(row[1], [p.circle(x=0, y=0, color=row[2])]) for row in legend.itertuples()],location='top_right')
    p.add_layout(legend)
    return p


'''
##########################################################
# 7. A general barplot
##########################################################
def barplot(dataframe):
    p = Bar(dataframe, label='relscreen', values='yval', group='statistic',
        title="Median MPG by YR, grouped by ORIGIN", legend='top_right')
    return p

'''
##########################################################
# 8. Grid Layout of Fixed Screen Summary                 #
##########################################################

def create_plot_screen_summary(fishtail, uniquefinder, list_custom_plots, geneplots):
    # The following can be enable for linked panning, very cool but it makes things a bit slow...
    #uniquefinder.x_range=fishtail.x_range
    #uniquefinder.y_range=fishtail.y_range
    rows = []
    rows.append([fishtail,uniquefinder])
    rows.append(list_custom_plots)
    rows = rows + [[plot] for plot in geneplots]
   # print(rows)
    summaryplot = layout(
        children=rows,
        sizing_mode='scale_width',
        responsive=True
    )

    return summaryplot

##########################################################
# 9. Grid Layout of Fixed Screen Sequence Summary        #
##########################################################

def create_plot_screen_seq_summary(totalreadsplot, uniquereadsplots, ratioplot):
    rows = []
    rows.append([totalreadsplot])
    rows.append([uniquereadsplots])
    rows.append([ratioplot])
#    rows.append(list_custom_plots)
#    rows = rows + [[plot] for plot in geneplots]
   # print(rows)
    seqsummaryplot = layout(
        children=rows,
        sizing_mode='scale_width',
    )

    return seqsummaryplot
