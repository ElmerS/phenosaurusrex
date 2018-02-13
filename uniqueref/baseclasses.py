import models

class ValidatedQuerySet(object):
	"""

	"""
	def __init__(self, user_details, *args, **kwargs):
		self.uid = user_details['uid']
		self.authorized_screens = user_details['authorized_screens']
		self.gids = user_details['gids']
		if not 'ref' in user_details.keys():
			refname = self.get_setting("default_reference")
			self.ref = self.get_refid_from_name(refname)
		else:
			self.ref = user_details['ref']
		self.qs_screen = models.Screen.objects.filter(id__in=self.authorized_screens)

	def get_setting(self, var):
		'''
		Get name of default reference from Settings table in database database, lookup and return its identifier
		:param var:
		:return:
		'''
		return models.Settings.objects.get(variable_name=var).value

	def get_refgenomes(self):
		return models.ReferenceGenome.objects.all()

	def get_refname_from_id(self):
		return models.ReferenceGenome.objects.get(id=self.ref).shortname

	def get_refid_from_name(self, refname):
		return models.ReferenceGenome.objects.get(shortname=refname).id