from bokeh.plotting import figure
from bokeh.models import Span, LabelSet
from bokeh.models import HoverTool, TapTool, OpenURL, Circle, Text, CustomJS, ColumnDataSource, Legend
from bokeh.layouts import row
import numpy as np


# Dev imports
import logging
logger = logging.getLogger(__name__)

class Fishtail(object):
	def __init__(self, attr):
		self.attr = attr


	def create_plot_object(self):
		# Define the available tools for the plot
		TOOLS = "save,wheel_zoom,box_zoom,reset,hover"

		p = figure(
			width = self.attr['dim']['width'],
			height = self.attr['dim']['height'],
			y_range = (self.attr['dim']['min_y'], self.attr['dim']['max_y']),
			x_range=(self.attr['dim']['min_x'], np.log10(self.attr['dim']['max_x'])),
			tools = [TOOLS],
			title = self.attr['title'],
			x_axis_label = self.attr['x_label'],
			y_axis_label = self.attr['y_label']
		)

		# Adjust output backend if required
		if self.attr['rendering_mode'] == 'svg':
			p.output_backend = "svg"
		elif self.attr['rendering_mode'] == 'opengl':
			p.output_backend = "webgl"


		# This is the place for some styling of the graph
		#p.toolbar_location = self.attr['toolbar_location']
		p.outline_line_width = 3
		p.outline_line_alpha = 1
		p.outline_line_color = "black"

		'''
		#A horizontal line to indicate the zero-bar
		'''
		horizontal_line = Span(location=self.attr['span_location'],
									  dimension='width', line_color='black',
									  line_dash='dashed', line_width=3)
		p.add_layout(horizontal_line)

		# The hover guy
		hover = p.select(type=HoverTool)
		hover.tooltips = [
			('Gene', '@relgene')
		]


		# Add the datapoints to the plot
		self.attr['data']['loginsertions'] = np.log10(self.attr['data']['insertions'])
		self.attr['data'].drop('insertions', axis=1, inplace=True)
		source = ColumnDataSource(self.attr['data'])
		p.circle(x='loginsertions', y='senseratio', fill_color='color', fill_alpha=1, line_color='color',
							  size=5, line_width=1, source=source)

		# Add the text annotations to the plot
		self.attr['text_data']['loginsertions'] = np.log10(self.attr['text_data']['insertions'])
		self.attr['text_data'].drop('insertions', axis=1, inplace=True)
		textsource = ColumnDataSource(self.attr['text_data'])
		labels = LabelSet(x='loginsertions', y='senseratio', text='relgene', source=textsource)
		p.add_layout(labels)

		#textsource = ColumnDataSource(data=dict(insertions=[], senseratio=[], relgene=[]))
		# Define the layout of the circle (a Bokeh Glyph) if nothing has been selected, ie. the inital view
		#initial_view = Circle(x='insertions', y='senseratio', fill_color='color', fill_alpha=1, line_color='color',
							  #size=5, line_width=1)

		# Plot the final graph
		#p.add_glyph(
		#	source,
		#	initial_view,
		#	selection_glyph=initial_view,
		#	nonselection_glyph=initial_view
		#)
		'''
		if sag == "on":
			p.text('loginsertions', 'logmi', text='signame', text_color='black', text_font_size=textsize, source=source)
			
		if oca == "hah":  # If the 'on click action' is highlight and label
			# Start with creating an empty overlaying plot for the textlabels
			p.text('loginsertions', 'logmi', text='relgene', text_color='black', text_font_size=textsize,
				   source=textsource)  # This initally is an empty p because the textsource is empty as long as no hits have been selected
			# Define how the bokeh glyphs should look if selected
			selected_circle = Circle(fill_color='black', line_color='black', fill_alpha=1, line_alpha=1, size=5,
									 line_width=1)
			# Define how the bokeh glyphs should look if not selected
			nonselected_circle = Circle(fill_color='color', line_color='linecolor', fill_alpha=transp_nsel_f,
										line_alpha=transp_nsel_l, size=5, line_width=1)

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

		elif oca == "gc":  # If linking out to genecards
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

		# When coloring the dots by track, create legend that tells which color is which track
		if (not legend.empty):
			legend = Legend(items=[(r[1], [p.circle(x=0, y=0, color=r[2])]) for r in legend.itertuples()],
							location=legend_location)
			if (legend_location != 'top_right'):
				p.add_layout(legend, 'right')
			else:
				p.add_layout(legend)

		'''

		return p
