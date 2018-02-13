import numpy as np

from uniqueref.SL.plots.baseplots import Fishtail

from ...sharedvars import plotvars as cpv #cpv = common plot vars
from ..sharedvars import plotvars as pv # plots vars specific for synthetic lethals

# Dev imports
import logging
logger = logging.getLogger(__name__)

class SenseAntisenseFishtail(Fishtail):

	def calculate_plot_shape(self):
		dim = {}
		dim['height'] = cpv.fishtail_height
		dim['width'] = cpv.fishtail_width
		dim['max_x'] = self.attr['data'].max()['insertions'] * 1.05
		dim['min_x'] = 0
		dim['max_y'] = 1
		dim['min_y'] = 0
		self.attr['dim'] = dim
		pass


	def annotation_attributes(self):
		self.attr['title'] = ' '.join(['Replicate', str(self.attr['replicate'])])
		self.attr['x_label'] = cpv.x_axis_insertions_label
		self.attr['y_label'] = pv.y_axis_label
		pass


	def set_attributes(self):
		'''
		Calculates the non-given plotting attributes and stores them in keys of the self.attr dict.
		:return: None
		'''

		# Set the attributes for the shape of the plot
		self.calculate_plot_shape()

		# Set the attributes for the annotation
		self.annotation_attributes()

		# And some other attributes
		self.attr['toolbar_location'] = "below"
		self.attr['span_location'] = 0.5 # The Y-value (in the graph) where the horizontal line should be.
		pass


	def get_bokeh_plot_object(self):
		self.set_attributes()
		bpo = super(SenseAntisenseFishtail, self).create_plot_object()
		return bpo
