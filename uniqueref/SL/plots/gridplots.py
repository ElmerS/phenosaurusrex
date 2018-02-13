from bokeh.layouts import layout, widgetbox, row
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.models.widgets import Div

class ComparativePlot(object):
	def __init__(self, name):
		self.control_plots = {}
		self.experiment_plots = {}
		self.gridplot = None
		self.experiment_row = [] # To keep track of the plots in the row with experiment plots
		self.control_row = [] # To keep track of the plots in the row with control population plots
		self.name = name

	def add_control_plot(self, bpo):
		self.control_row.append(bpo)


	def add_experiment_plot(self, bpo):
		self.experiment_row.append(bpo)


	def make_gridplot(self):
		# Append the experiment and control rows
		expdiv = Div(text=" ".join(["""<font size=4>""", "Experiment:", self.name, """</>"""]))
		wtdiv = Div(text="""<font size=4>Wildtype controls</>""")
		rows = []
		rows.append([widgetbox(expdiv)])
		rows.append(self.experiment_row)
		rows.append([widgetbox(wtdiv)])
		rows.append(self.control_row)

		# And put them in a gridplot
		self.gridplot = layout(
			children=rows,
			sizing_mode='scale_width',
			responsive=True
		)
		pass

	def get_html(self):
		script, div = components(self.gridplot, CDN, "bokeh-gl")
		return script, div


