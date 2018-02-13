'''
Everything that is related to the creation of tables from the menu 'Data Sources' such as a list of all genes etc.
should be put here. Some of these functions still reside in custom_functions.py and should be moved at some point.
'''

from ..baseclasses import ValidatedQuerySet
from .. import models
import pandas as pd

class annotation_table(object):

	def __init__(self, user_details):
		self.table = self.make_list(user_details)

	def make_list(self, user_details):
		qs = ValidatedQuerySet(user_details).get_refgenomes()
		with pd.option_context('display.max_colwidth', -1):
			table = qs.to_dataframe()[['shortname', 'longname', 'description']].to_html(
				index=False, classes=["table-bordered", "table-striped", "table-hover"])
		return table