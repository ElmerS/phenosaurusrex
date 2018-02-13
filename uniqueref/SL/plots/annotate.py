import numpy as np

# Synthetic Lethal Specific imports
from uniqueref.SL.sharedvars import colors
import pandas as pd

# Dev imports
import logging
logger = logging.getLogger(__name__)

class LabeledSampleData:
	'''
	:param data: Pandas DataFrame
	:param genes: list of significant genes
	'''
	def __init__(self, data, params):
		self.data = data
		self.text_data = pd.DataFrame(columns=['senseratio', 'insertions', 'relgene'])
		self.text_data['insertions'] = self.text_data['insertions'].astype(np.int32)
		self.text_data['insertions'] = self.text_data['senseratio'].astype(np.float32)
		self.params = params
		self.sig_genes = params['sig_genes']

	def color_data(self):
		'''
		Colors the datapoints of a plot according to given parameters
		:return: return updated version of data (PD DF)
		'''
		self.data['color'] = np.where(self.data['relgene'].isin(self.sig_genes), colors.sig_gene, colors.non_sig_gene)
		return self.data

	def annotate_sig_genes(self):
		text_data = self.data[self.data['relgene'].isin(self.sig_genes)]
		text_data = text_data[['senseratio', 'insertions', 'relgene']]
		return text_data

	def get_annotations(self):
		if self.params['aas']:
			self.text_data = self.text_data.append(self.annotate_sig_genes())
		self.text_data.drop_duplicates(inplace=True) # Get rid of potential duplicates

		return self.text_data