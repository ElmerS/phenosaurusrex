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
		self.info = db.Screen.objects.filter(id=screen_id).values()[0] # A dict with holding all values for screen x
		self.id = self.info['id']
		self.name = self.info['name']
		self.description = self.info['description']
		self.longdescription = self.info['longdescription']
		self.sequenceids = self.info['sequenceids']
		self.directory = self.info['directory']
		self.induced = self.info['induced']
		self.knockout = self.info['knockout']
		self.scientisy = self.info['scientist_id']
		self.screen_date = self.info['screen_date']
		self.screentype = self.info['screentype']

class SLIScreenReplicate(Screen):

	def __init__(self, screen_id, replicate_id):
		super(SLIScreenReplicate, self).__init__(screen_id)
		self.qs = db.SLSDatapoint.objects.filter(relscreen_id=screen_id).filter(replicate=replicate_id)

	def __repr__ (self):
		return force_bytes('%s replicate %s' % (self.name, self.replicate))

