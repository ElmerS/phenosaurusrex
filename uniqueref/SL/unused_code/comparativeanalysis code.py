# ComparativeAnalysis code

'''

class SyntheticLethalComparativeAnalysis(SyntheticLethalAnalysis):
	def BuildView(self, binom_cutoff=gv.pvdc, authorized_screens=None, fdr_correction=fv.default_fdr, fisher_cutoff=gv.pvdc):
		self.PrepareDataForPlot(binom_cutoff, fdr_correction, fisher_cutoff)
		GraphObjects = []
		for r in sorted(self.replicatedata.keys()): # By sorting on the keys, the replicates are plotted in logical order
			Graph = self.DrawSenseRatioGraph(self.replicatedata[r], authorized_screens, GraphTitle=" ".join([self.replicates[r].name, 'replicate', r]))
			GraphObjects.append(Graph)
		script, div = components(column(GraphObjects, responsive=True), CDN)
		return script, div

	def PrepareDataForPlot(self, binom_cutoff, fdr_correction, fisher_cutoff, effectsize_cutoff, directionality):
		for r in self.replicatedata:
			self.replicatedata[r]['color'] = np.where(self.replicatedata[r]['binom_fdr'] <= binom_cutoff, gv.color_sl_s,
													  gv.color_sl_ns)
			self.replicatedata[r]['loginsertions'] = np.log10(self.replicatedata[r]['insertions'])
			self.replicatedata[r]['signame'] = np.where(self.replicatedata[r]['binom_fdr'] <= binom_cutoff,
														self.replicatedata[r]['relgene'], "")
			self.replicatedata[r].rename(columns={'binom_fdr': 'fcpv'}, inplace=True)
'''

# BinomialAnalysis code

'''

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
'''

# Screen code

'''
from abc import ABCMeta, abstractmethod
from .. import custom_functions as cf
from .. import globalvars as gv
from .. import models as db
import logging

class Screen(object):
	"""An abstract class for all type of screens
		
	Attributes:
		relscreen: the database ID of the screen the used wants to make an object from
		authorized_screens: a list of all database IDs that the user is allowed to access
	
	"""
	__metaclass__ = ABCMeta

	def __init__ (self, screen_id):
		self.info = db.Screen.objects.filter(id=screen_id).values()[0] # A dict holding all values for screen x
		self.id = self.info['id']
		self.name = self.info['name']
		self.description = self.info['description']
		self.longdescription = self.info['longdescription']
		self.sequenceids = self.info['sequenceids']
		self.directory = self.info['directory']
		self.induced = self.info['induced']
		self.knockout = self.info['knockout']
		self.scientist = self.info['scientist_id']
		self.screen_date = self.info['screen_date']
		self.screentype = self.info['screentype']

class SLIScreenReplicate(Screen):
	"""
	A screen replicate can be both a replicate of the wildtype screen or a replicate of a screen in a genetic
	background
	"""
	def __init__(self, screen_id, replicate_id):
		super(SLIScreenReplicate, self).__init__(screen_id)
		self.qs = db.SLSDatapoint.objects.filter(relscreen_id=screen_id).filter(replicate=replicate_id)

	def __repr__ (self):
		return force_bytes('%s replicate %s' % (self.name, self.replicate))


'''
# Some stuff from views
'''
		'''
		self.formdata = parameterform.ParameterFormInput(self.user_details, self.formdata)
		if not self.formdata.error:  # If form error don't try to make a plot at all
			self.context = {'error': self.formdata.error}

		elif self.formdata['analysis'][0] == "compare":
			context = ComparativeAnalysis(self.formdata)

		else:
			context = SyntheticLethalBionomialAnalysis(self.formdata)
		'''

'''