from uniqueref.baseclasses import ValidatedQuerySet
from uniqueref import models

class ValidatedSLIQuerySet(ValidatedQuerySet):
	'''
	Extends ValidatedQuerySet with specific queries for synthetic lethal screens
	'''

	def __init__(self, user_details):
		super(ValidatedSLIQuerySet, self).__init__(user_details)
		self.qs_datapoint = models.SLSDatapoint.objects.filter(
			relscreen__id__in=self.authorized_screens).filter(
			relgene__relref=self.ref)

	def queryset_sli_screens(self):
		'''
		Looks up the screens that have been designated as control (ie. wildtype) screens for synthetic lethal screens
		and remove them from the list of available synthetic lethal screens. To query the screens that the users is
		allowed to see and from those subset the ones that have been analyzed with the currently selected reference
		annotation (self. ref)
		:return: queryset of Screen model (type: Queryset object)
		'''
		controlscreens = [int(i) for i in self.get_setting('synthetic_lethal_controls').split(",")]
		return self.qs_screen.exclude(id__in=controlscreens).filter(
			screentype='SL').filter(relrefs=self.ref)


	def queryset_single_screen(self, screen_id):
		'''
		To query the screen Model for a given (screen_id) synthetic lethal screen
		:param screen_id:
		:return: queryset of a single Synthetic Lethal screen
		'''
		return self.qs_screen.filter(id=screen_id).filter(screentype='SL')


	def get_control_screen_id(self, screen_id):
		'''
		Queries the value of the associated control screen for a requested screen and returns the ID of the control
		:param screen_id:
		:return: id of associated control screen (type: int)
		'''
		control_screen_id = int(self.queryset_single_screen(screen_id).values_list('controlscreen')[0][0])
		return control_screen_id

	def get_qs_replicate(self, screen_id, replicate):
		'''
		Queries all the datapoints for a selected screen and replicate
		:param screen_id: pk of screen
		:param replicate: number of the replicate
		:return: Queryset
		'''
		data = self.qs_datapoint.filter(relscreen__id=screen_id).filter(replicate=replicate)
		return data
	