# Specific Synthetic Lethal imports

from uniqueref.SL.baseclasses import ValidatedSLIQuerySet
from uniqueref.SL.plots.annotate import LabeledSampleData
from uniqueref.SL.plots.fishtails import SenseAntisenseFishtail
from uniqueref.SL.plots.gridplots import ComparativePlot
from uniqueref.SL.results import SLIResults
from uniqueref.SL.sample import SampleData
from uniqueref.SL.screen import ScreenInfo, ScreenData

import numpy as np

# Dev imports
import logging
logger = logging.getLogger(__name__)


class ComparativeAnalysis:
	'''
	Initialize ComparativeAnalysis object with formdata, a name (based on forminput)
	'''
	def __init__(self, user_details, formdata, *args, **kwargs):
		self.user_details = user_details
		self.vqs = ValidatedSLIQuerySet(self.user_details) # Use this object to make queries to the DB
		self.unpack_formdata(formdata) # New self variables assigned in unpack_formdata!
		self.control_info = ScreenInfo(self.vqs, self.control_screen_id)
		self.experiment_info = ScreenInfo(self.vqs, self.screen_id)
		self.name = self.get_name() # The name of the comparison
		self.annotation_parameters = {'effect_size':self.effect_size,
					  'binom_cutoff':self.binom_cutoff,
					  'pv_cutoff': self.pv_cutoff,
					  'directionality':self.directionality}
		self.annotated_genes = []

	def unpack_formdata(self, formdata):
		self.screen_id = int(formdata['screenid'][0])	# int
		self.control_screen_id = int(self.vqs.get_control_screen_id(self.screen_id))
		self.experiment_replicates = [int(s) for s in formdata['replicates']]
		self.control_replicates = [int(s) for s in formdata['controls']]
		self.pv_cutoff = float(formdata['fisher_p_value'][0])
		self.binom_cutoff = float(formdata['binom_p_value'][0])
		self.effect_size = float(formdata['effect_size'][0])
		self.oca = str(formdata['oca'])
		# These parameters' existence needs to be checked first:
		self.customgenelistids = [int(id) for id in formdata['customgenelist']] if 'customgenelist' in formdata else False
		self.customgenes = [str(gene) for gene in formdata['genes']] if 'genes' in formdata else False
		self.aggregate_controls = True if 'aggregate' in formdata else False
		self.directionality = True if 'directionality' in formdata else False
		self.aas = True if 'aas' in formdata else False
		self.fdr = True if 'fdr' in formdata else False


		return


	def get_name(self):
		name = ' '.join(['Comparison of replicate',
						 ' '.join([str(r) for r in self.experiment_replicates]),
						 'of', self.experiment_info.name, 'against replicate',
						 ' '.join([str(r) for r in self.control_replicates]),
					     'of', self.control_info.name])
		return name


	def build_dataframes(self):
		'''
		Method to create ScreenData objects for all the replicates of the screen and control populations
		:return experimentdata: ScreenData instance filled with data of replicates of screen/experiment
		:return controldata: ScreenData instance filled with data of replicates of controls
		'''
		experiment_data = ScreenData(self.experiment_info)
		control_data = ScreenData(self.control_info)
		for r in self.experiment_replicates:
			qs = SampleData(self.vqs, self.screen_id, r)
			df = qs.get_df_for_experiment(self.control_replicates, self.fdr)
			experiment_data.add_replicate(r, df)
		for r in self.control_replicates:
			qs = SampleData(self.vqs, self.control_screen_id, r)
			df = qs.get_df_for_control()
			control_data.add_replicate(r, df)

		return experiment_data, control_data

	def process(self):
		# Get the data
		experiment_data, control_data = self.build_dataframes()

		# Create results object that can be to identify significant genes
		results = SLIResults(experiment_data, control_data, self.annotation_parameters)
		sig_genes = results.get_significant_genes()

		# Initialize an instance of ComparativePlot to hold the plots of the experiment and control populations
		comparativeplot = ComparativePlot(self.experiment_info.name)
		labelparams = {'aas': self.aas, 'sig_genes': sig_genes}

		# Loop over replicates of experiment (ie. screen),
		for r in experiment_data.replicates.keys():
			attr = {} # A dict to store the attributes for building the plot
			'''
			Create a LabeledSampleData (labeled as in: genes are assigned color) and apply the required functions. By
			default, genes that score significant are always assigned the significant color and other coloring schemes
			come on top of that (such as tracks etc.)
			'''
			d = LabeledSampleData(experiment_data.replicates[r], labelparams)
			attr['data'] = d.color_data()
			attr['text_data'] = d.get_annotations()
			attr['oca'] = self.oca
			attr['replicate'] = r
			s = SenseAntisenseFishtail(attr) # Create an instance of SenseAntisenseFishtail to draw a plot
			bpo = s.get_bokeh_plot_object() # Call the method to actually make a Bokeh plot
			comparativeplot.add_experiment_plot(bpo) # Parse the Bokeh plot to the comparative overview


		'''
		Call aggregate_controls method of ScreenData if aggregate of controls should be plotted instead of creating
		separate plots, otherwise loop of over the replicates of the control screen
		'''
		if self.aggregate_controls:
			attr = {} # A dict to store the attributes for building the plot
			# Create a aggregate of the control populations
			aggdata = control_data.aggregate_controls()
			# Give color attributes to genes according to previously calculated significance
			d = LabeledSampleData(aggdata, labelparams)
			attr['data'] = d.color_data()
			attr['text_data'] = d.get_annotations()
			attr['oca'] = self.oca
			attr['replicate'] = " ".join([", ".join((str(s) for s in self.control_replicates)), "(aggregated)"])
			s = SenseAntisenseFishtail(attr) # Create an instance of SenseAntisenseFishtail to draw a plot
			bpo = s.get_bokeh_plot_object() # Call the method to actually make a Bokeh plot
			comparativeplot.add_control_plot(bpo) # Parse the Bokeh plot to the comparative overview

		else:
			for c in control_data.replicates.keys():
				attr = {}  # A dict to store the attributes for building the plot
				'''
				Create a LabeledSampleData (labeled as in: genes are assigned color) and apply the required functions. By
				default, genes that score significant are always assigned the significant color and other coloring schemes
				come on top of that (such as tracks etc.)
				'''
				d = LabeledSampleData(control_data.replicates[c], labelparams)
				attr['data'] = d.color_data()
				attr['text_data'] = d.get_annotations()
				attr['oca'] = self.oca
				attr['replicate'] = c
				s = SenseAntisenseFishtail(attr)  # Create an instance of SenseAntisenseFishtail to draw a plot
				bpo = s.get_bokeh_plot_object()  # Call the method to actually make a Bokeh plot
				comparativeplot.add_control_plot(bpo)  # Parse the Bokeh plot to the comparative overview

		comparativeplot.make_gridplot()
		exp_script, control_script, exp_div, control_div = comparativeplot.get_html()
		context = {'exp_script':exp_script, 'control_script':control_script, 'exp_div':exp_div, 'control_div':control_div}
		return context