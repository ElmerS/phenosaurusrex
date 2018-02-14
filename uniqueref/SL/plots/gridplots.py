from bokeh.layouts import layout, widgetbox, row
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.models.widgets import Div
import numpy as np

class ComparativePlot(object):
	def __init__(self, name):
		self.control_plots = {}
		self.experiment_plots = {}
		self.exp_gridplot = None
		self.control_gridplot = None
		self.experiment_row = [] # To keep track of the plots in the row with experiment plots
		self.control_row = [] # To keep track of the plots in the row with control population plots
		self.name = name

	def add_control_plot(self, bpo):
		self.control_row.append(bpo)


	def add_experiment_plot(self, bpo):
		self.experiment_row.append(bpo)


	def make_gridplot(self):
		# Create a title and layoutDOMs for experiment and control plots
		expdiv = Div(text=" ".join(["""<font size=4>""", "Experiment:", self.name, """</>"""]))
		exp_rows = []
		exp_rows.append([widgetbox(expdiv)])
		exp_rows.append(self.experiment_row)
		self.exp_gridplot = layout(
			children=exp_rows,
			responsive=True
		)

		wtdiv = Div(text="""<font size=4>Wildtype controls</>""")
		control_rows = []
		control_rows.append([widgetbox(wtdiv)])
		# Make sure no more than 3 control plots are plotted in a single row, otherwise Bokeh crashes
		if len(self.control_row)>=4:
			for part in np.array_split(self.control_row,2):
				control_rows.append(part.tolist())
		else:
			control_rows.append(self.control_row)
		self.control_gridplot = layout(
			children=control_rows,
			responsive=True
		)
		pass

	def get_html(self):
		exp_script, exp_div = components(self.exp_gridplot, CDN, "bokeh-gl")
		control_script, control_div = components(self.control_gridplot, CDN, "bokeh-gl")
		return exp_script, control_script, exp_div, control_div


