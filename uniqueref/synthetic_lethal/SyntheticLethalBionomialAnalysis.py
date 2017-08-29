from .. import custom_functions as cf
from .. import globalvars as gv
from SyntheticLethalAnalysis import SyntheticLethalAnalysis

from bokeh.layouts import column
from bokeh.resources import CDN
from bokeh.embed import components

import pandas as pd
import numpy as np

class SyntheticLethalBionomialAnalysis(SyntheticLethalAnalysis):
	def BuildView(self, binomcutoff, authorized_screens):
		self.PrepareDataForPlot(binomcutoff)
		GraphObjects = []
		for r in sorted(self.replicatedata.keys()): # By sorting on the keys, the replicates are plotted in logical order
			Graph = self.DrawSenseRatioGraph(self.replicatedata[r], authorized_screens, GraphTitle=" ".join([self.replicates[r].name, 'replicate', r]))
			GraphObjects.append(Graph)
		script, div = components(column(GraphObjects, responsive=True), CDN)
		return script, div

	def PrepareDataForPlot(self, binomcutoff):
		for r in self.replicatedata:
			self.replicatedata[r]['color'] = np.where(self.replicatedata[r]['binom_fdr'] <= binomcutoff, gv.color_sl_s,
													  gv.color_sl_ns)
			self.replicatedata[r]['loginsertions'] = np.log10(self.replicatedata[r]['insertions'])
			self.replicatedata[r]['signame'] = np.where(self.replicatedata[r]['binom_fdr'] <= binomcutoff,
														self.replicatedata[r]['relgene'], "")
			self.replicatedata[r].rename(columns={'binom_fdr': 'fcpv'}, inplace=True)