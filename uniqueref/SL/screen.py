import pandas as pd

# Dev imports
import logging
logger = logging.getLogger(__name__)

class ScreenInfo(object):
	'''
	To hold all the information about a single experiment (ie. a simplified object of the uniqueref.models.screen)
	'''
	def __init__(self, vqs, id):
		self.qs = vqs.queryset_single_screen(id)
		self.name = self.qs.values_list('name', flat=True).get() # No arguments needed for get because only one row
		self.description = self.qs.values_list('description', flat=True).get()


class ScreenData(object):
	'''
	To hold the information about a single screen and all the datapoints of the selected replicates used for the
	requested analysis. Name of replicate is stored in the key and the dataframe is stored in the value of the
	self.replicates dictionary.
	'''
	def __init__(self, ScreenInfo):
		'''
		Requires an object on Screeninfo and creates a dict to store the dataframes of the requested replicates
		:param ScreenInfo:
		'''
		self.info = ScreenInfo
		self.replicates = {}

	def add_replicate(self, r, SampleData):
		'''
		Stores the parsed number of the associated replicate as a key and the DataFrame as a value and appends it to
		the self.replicates dict.
		:param r: int of replicate
		:param SampleData: Pandas DataFrame
		:return:
		'''
		self.replicates[r] = SampleData

	def aggregate_controls(self):
		'''
		To create a single dataframe that represents the aggregate of all selected controls. The following things are
		taken into consideration:
		- not all genes are hit in all replicates. If no insertions were identified in a replicate, the number of
		insertions and fdr-value are set to 2 and sense/total ratio is set to 0.5.
		- The largest p-value (binom-fdr) is selected.
		- Columns with lower and upper limit of sense/total ratio is created for later optionally plotting errorbars at
		some point.
		:return: merged_controls (pandas DataFrame
		'''
		i = 0
		senseratio_cols = []
		insertions_cols = []
		binom_fdr_cols = []
		replicates = {} # Local copy of self.replicates to hold modified data
		for r in self.replicates.keys():
			'''
			Rename the columns of the dataframes prior to merge and then merge dataframes of replicates on genename		
			'''
			newnames = {'senseratio': '_'.join(['senseratio', str(r)]),
						'insertions': '_'.join(['insertions', str(r)]),
					    'binom_fdr': '_'.join(['binom_fdr', str(r)])
			}
			replicates[r] = self.replicates[r].rename(columns=newnames)
			'''
			And actually merge the dataframes into a new frame called merged_controls
			'''
			if i == 0:
				merged_controls = replicates[r]
			else:
				merged_controls = pd.merge(merged_controls, replicates[r], on='relgene')
			i+=1
			'''
			Store the new names of each of the replicate columns in a list that can later be used to merge the values
			and calculate boundries
			'''
			senseratio_cols.append(newnames['senseratio'])
			insertions_cols.append(newnames['insertions'])
			binom_fdr_cols.append(newnames['binom_fdr'])


		'''
		Calculate the overage senseratio over the replicates as well as the average of the insertions. For the
		binom_fdr, take the least sign. value. Default behaviour for values that do not exist is skipna=True, one could
		argue to fill the empty insertions and binom_fdr cells with 1 and the senseratio with 0.5.
		'''

		merged_controls['senseratio'] = merged_controls[senseratio_cols].mean(axis=1)
		merged_controls['insertions'] = merged_controls[insertions_cols].mean(axis=1)
		merged_controls['binom_fdr'] = merged_controls[binom_fdr_cols].max(axis=1)

		'''
		Return aggregate values to original self.replicates dataframe
		'''
		return merged_controls[['relgene', 'senseratio', 'insertions', 'binom_fdr']]



