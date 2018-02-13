import pandas as pd

# Dev imports
import logging
logger = logging.getLogger(__name__)

class SLIResults(object):
	'''
	This class is designed to calculate and hold the results of an experiment vs control analysis. The subsequent
	object can be used to label dots in the plots and to create a table.
	The object is initialized with the following data:
	- experiment_data
	- control_data
	- a parameters dict with:
		- effect_size
		- binom_cutoff
		- pv_cutoff
		- directionality
	'''

	def __init__(self, experiment_data, control_data, parameters):
		self.experiment_data = experiment_data
		self.control_data = control_data
		self.parameters = parameters
		self.results = pd.DataFrame()

	def get_significant_genes(self):
		pass_pv_cutoff = self.get_pv_genes()
		pass_effect_size_cutoff = self.get_effectsize_genes(pass_pv_cutoff)
		pass_directionality_cutoff = self.get_directionality_genes(pass_effect_size_cutoff)
		return pass_directionality_cutoff

	def get_pv_genes(self):
		'''
		The first step is to identify which genes match the required p-value cutoff (both binomial as well as fisher-
		exact). This is done by individually evaluating the p-value of the binomial test of each replicate and then
		assessing of all the p-values of the Fisher exact test against the selected controls match the cutoff. When
		this is done for all replicates, the results are inner merged to see which genes meet the criteria over all the
		replicates. The result is a dataframe called pv_filtered with a single column with the genenames that meet the
		requirements
		:param: none
		:return pv_filtered: list of genes matching only the genes that match the p-value criteria
		'''
		i = 0
		pv_filtered = None # Dataframe of genes that match the pv-value cutoff (bimon + fisher exact)
		for r in self.experiment_data.replicates.keys():
			filter = " & ".join(
				["".join(["(df.fe_control_", str(c),
						  "<=",str(self.parameters['pv_cutoff']),
						  ")"]) for c in self.control_data.replicates.keys()]) + " & " + "".join(
				["(df.binom_fdr<=",str(self.parameters['binom_cutoff']),")"])
			''' 
			The following is a bit of a complex statement: self.experiment_data.replicates is a dict where each key
			represents a replicate and the value is a dataframe with all the datapoints of for that replicate. The eval
			statement applies the filter as built above.
			'''
			df = self.experiment_data.replicates[r]
			df = self.experiment_data.replicates[r][eval(filter)][['relgene']]
			if i==0:
				pv_filtered = df
			else:
				# Inner merge because all replicates should meet the p-value requirements
				pv_filtered = pd.merge(pv_filtered, df, on='relgene', how='inner')
			i+=1

		genes = [str(g) for g in pv_filtered['relgene'].tolist()]
		return genes

	def get_effectsize_genes(self, genes):
		'''
		The second step is to find the genes that also match the effect size cutoff and similar directionality
		requirement. To limit the comparison, only the genes that met the first (p-value) requirements are considered.
		First a single dataframe is created for the controls that solely holds the senseratios.
		:genes param: list holding the genes to include in this analysis
		:return es_filtered:  list that is a further selection (meeting the effectsize and directionality
		requirement) of genes
		'''
		# Initialize list of genes with those that match the pv cutoff
		es_filtered = genes
		for r in self.experiment_data.replicates.keys():
			exp_data = self.experiment_data.replicates[r][['relgene', 'senseratio']]
			exp_data = exp_data[exp_data.relgene.isin(es_filtered)] # Filter rows based on pv analysis results
			'''
			Loop over the selected controls and test whether the senseratio of the replicate is at least the required
			effectsize smaller or larger than the control.
			'''
			for c in self.control_data.replicates.keys():
				control_data = self.control_data.replicates[c][['relgene', 'senseratio']]
				control_data = control_data[control_data.relgene.isin(es_filtered)]
				control_column_name = "_".join(['senseratio_control', str(c)])
				control_data.rename(columns={'senseratio': control_column_name}, inplace=True)
				merged = pd.merge(exp_data, control_data, on='relgene', how='inner')
				'''
				Currently, the following filter only identfies genes whose senseration in the control at least
				the given effectsize smaller than in the experimental condition. This mean that genes that lost
				essentiality will not be highlighted nor genes that give a fitness benefit upon knockout. Ie.
				really focussed on identifying genes that have become essential in a KO background. 
				'''
				es_filtered = [str(g) for g in merged[
					(merged[control_column_name]-merged['senseratio'])>=
					self.parameters['effect_size']]['relgene'].tolist()]
				'''
				Create a dataframe of the senseratio columns of all replicates that individually meet the effectsize
				against the 
				'''

		return es_filtered

	def get_directionality_genes(self, genes):
		'''
		From finally also make sure that all the selected genes behave the same in all the replicates (ie. should
		not yield a fitness advantage in one replicate and give a fitness defect in another one). Currently this
		function is implemented in its most simple way: all replicates should give a fitness defect, ie. senseratio
		below 0.5
		:param self:
		:param genes: list of genes that passed the pv- and effectsize cutoff
		:return dir_filtered: list of genes that also pass the directionality cutoff
		'''
		# Initialize list of genes with those that match the pv- and effectsize cutoff
		dir_filtered = genes
		for r in self.experiment_data.replicates.keys():
			df = self.experiment_data.replicates[r][['relgene', 'senseratio']]
			df = df[df.relgene.isin(dir_filtered)]
			dir_filtered = [str(g) for g in df[df['senseratio']<0.5]['relgene'].tolist()]

		return dir_filtered


	def get_table(self):
		pass