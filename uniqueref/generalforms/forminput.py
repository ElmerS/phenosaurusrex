'''
A baseclass to process the received forminput. Only to be subclassed.
'''

from abc import ABCMeta, abstractmethod

class FormInput(object):
	'''
	Process the forminput
	'''
	__metaclass__ = ABCMeta

	def __init__(self, user_details, formdata, *args, **kwargs):
		self.formdata = formdata
		self.user_details = user_details