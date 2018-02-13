import pandas as pd

# Dev imports
import logging
logger = logging.getLogger(__name__)

class SampleData(object):
	'''
	To hold the data from a single replicate of a Synthetic Lethal Screen. In the __init__ a dataframe is created with
	the minimum information to draw a plot.
	'''
	def __init__(self, vqs, screen_id, replicate):
		self.qs = vqs.get_qs_replicate(screen_id, replicate)

	def get_df_for_experiment(self, control_replicates, fdr):
		'''
		To make a dataframe for experimental dataset. Requires relgene, senseratio, insertions, binom_fdr and depending
		of the choice of the user the fdr-corrected on non-fdr-corrected p-values are queried for the selected screen.
		Because fdr-and non-fdr p-values have a different columnname, the name is the columns is changed after selection
		to make subsequent analysis easier.

		:param control_replicates:
		:param fdr:
		:return:
		'''
		cols = ['relgene', 'senseratio', 'insertions', 'binom_fdr'] # These columns are always required

		'''
		Instead of directly appending the names of the requested p-value columns to the cols list, a dict is created
		first where the keys represent the names of columns that need to be included in the queryset. By doing so the
		values can be used to represent the new 'common name' for the fisher exact p-value column, which can be parsed
		to the rename function of the pd.dataframe object.
		'''
		control_cols = {}
		control_col_base = 'fcpv' if fdr else 'pv'

		for r in control_replicates:
				control_cols['_'.join([control_col_base, 'control', str(r)])] = '_'.join(['fe_control', str(r)])
		cols = cols + control_cols.keys()
		df = self.qs.to_dataframe(fieldnames=cols)
		df.rename(columns=control_cols, inplace=True)
		return df


	def get_df_for_control(self):
		'''
		To make a dataframe for controlpopulation.
		For the controls, only the genename, senseration, p-value from the binomial (per definition FDR corrected),
		number of insertions columns are required
		:return: dataframe
		'''
		df = self.qs.to_dataframe(fieldnames=['relgene', 'senseratio', 'insertions', 'binom_fdr'])
		return df