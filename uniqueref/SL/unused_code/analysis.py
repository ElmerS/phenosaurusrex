from abc import ABCMeta, abstractmethod
from uniqueref import custom_functions as cf
from uniqueref import globalvars as gv
from uniqueref import models as db
import uniqueref.SL.UserMessages

from bokeh.plotting import figure
from bokeh.models import HoverTool, TapTool, OpenURL, Circle, Text, CustomJS, ColumnDataSource, Legend

import pandas as pd
import numpy as np


class SyntheticLethalAnalysis:

	__metaclass__ = ABCMeta

	def __init__(self, forminput): # replicates must be dict of one or more SLIScreenReplicate Objects, same holds for controls
		self.replicates = replicates
		self.controls = controls
		self.replicatedata = {i:self.replicates[i].qs.objects.all().to_dataframe() for i in self.replicates} # Dict comprehensions, requires Python 2.7+
		self.controldata = {i:self.controls[i].qs.only('relgene', 'senseratio', 'insertions', 'binom_fdr').to_dataframe() for i in self.controls}
		self.gene = db.Gene.objects.all().to_dataframe() # Fetch data from tables with genes to annotate datapoints
		for replicate in self.replicatedata:
			self.replicatedata[replicate] = pd.merge(self.gene, self.replicatedata[replicate], left_on='name', right_on='relgene')
		for control in self.controldata:
			self.controldata[control] = pd.merge(self.gene, self.controldata[control], left_on='name', right_on='relgene')




	def DrawSenseRatioGraph(self, SampleDF, authorized_screens, GraphTitle="Unnamed sample", sag='', oca='gc', textsize='11px', DFLegend=pd.DataFrame()):
		"""
		This function creates a Bokeh Plot Object to display the sense/antisense insertion-ratio for a screen
		:param SampleDF: Pandas DataFrame for a single sample (either replicate or control, with the columns relgene/senseratio/insertions/fcpv
		:param authorized_screens: list if ScreenIDs current user is allowed to see (for calling GenePlots of all screens upon click)
		:param sag: Boolean option whether all significant genes should be labeled
		:param oca: Option what should happen upon click (see forms)
		:param textsize: Textsize of labels
		:DFLegend: Pandas Dataframe consisting of color and name categorical nametag 
		:return: 
		"""
		GM = uniqueref.SL.UserMessages.SenseRatioGraphMessages()
		xlim = SampleDF['loginsertions'].max() * 1.05
		p = figure(
			width = gv.binomplot_width,
			height = gv.binomplot_height,
			y_range = (0, 1),
			x_range = (0, xlim),
			tools = [gv.full_toolset],
			title = GraphTitle,
			webgl = True,
			x_axis_label = GM.x_axis_label,
			y_axis_label = GM.y_axis_label
		)

		# The hover guy
		hover = p.select(type=HoverTool)
		hover.tooltips = [
			(GM.hover_tooltip_p_values, '@fcpv'),
			(GM.hover_tooltip_gene, '@relgene'),
			(GM.hover_tooltip_custom, '@adddescription')]

		# This is the place for some styling of the graph
		p.toolbar_location = "below"
		p.outline_line_width = 3
		p.outline_line_alpha = 1

		# Create a ColumnDataSource from the merged dataframa
		source = ColumnDataSource(SampleDF)
		# Create a new dataframe and source that only holds the names and the positions of datapoints, used for labeling genes
		textsource = ColumnDataSource(data=dict(loginsertions=[], senseratio=[], relgene=[]))
		# Define the layout of the circle (a Bokeh Glyph) if nothing has been selected, ie. the inital view
		initial_view = Circle(x='loginsertions', y='senseratio', fill_color='color', line_color='color', fill_alpha=1, size=5, line_width=1)

		############################################################################
		###### The functions between these lines are all conditional functions #####
		############################################################################
		# 'Label all significant genes is required'
		if sag == "on":
			p.text('loginsertions', 'senseratio', text='signame', text_color='black', text_font_size=textsize, source=source)

		# If the 'OnClickAction' is highlight and label
		if oca == "hah":
			# Start with creating an empty overlaying plot for the textlabels
			p.text('loginsertions', 'senseratio', text='relgene', text_color='black', text_font_size=textsize,
			# Define how the bokeh glyphs should look if selected
			source = textsource)  # This initally is an empty p because the textsource is empty as long as no hits have been selected
			# Define how the bokeh glyphs should look if selected
			selected_circle = Circle(fill_color='black', line_color='black', fill_alpha=1, line_alpha=1, size=5, line_width=1)
			# Define how the bokeh glyphs should look if not selected
			nonselected_circle = Circle(fill_color='color', line_color='color', fill_alpha=gv.transp_nsel_f, line_alpha = gv.transp_nsel_l, size = 5, line_width = 1)
			source.callback = CustomJS(args=dict(textsource=textsource), code="""
       			var inds = cb_obj.get('selected')['1d'].indices;
    			var d1 = cb_obj.get('data');
    			var d2 = textsource.get('data');
	        	d2['loginsertions'] = []
	        	d2['senseratio'] = []
	        	d2['relgene'] = []
	        	for (i = 0; i < inds.length; i++) {
	        	    d2['loginsertions'].push(d1['loginsertions'][inds[i]])
	        	    d2['senseratio'].push(d1['senseratio'][inds[i]])
	        	    d2['relgene'].push(d1['relgene'][inds[i]])
	        	}
	        	textsource.trigger('change');
	    	""")

		# If the 'OnClickAction' is open link in GeneCards
		elif oca == "gc":
			selected_circle = initial_view
			nonselected_circle = initial_view
			url = "http://www.genecards.org/cgi-bin/carddisp.pl?gene=@relgene"
			taptool = p.select(type=TapTool)
			taptool.callback = OpenURL(url=url)

		# If the 'OnClickAction' should open link to gene in GenePlot view
		elif oca == "gp":
			selected_circle = initial_view
			nonselected_circle = initial_view
			url = cf.create_gene_plot_url("@relgene", authorized_screens)
			taptool = p.select(type=TapTool)
			taptool.callback = OpenURL(url=url)

		# When coloring the dots by track, create legend that tells which color is which track
		if (not DFLegend.empty):
			legend = Legend(items=[(r[1], [p.circle(x=0, y=0, color=r[2])]) for r in DFLegend.itertuples()], location='top_right')
			p.add_layout(DFLegend)
		############################################################################

		# Plot the final graph
		p.add_glyph(source, initial_view, selection_glyph=selected_circle, nonselection_glyph=nonselected_circle)
		return p