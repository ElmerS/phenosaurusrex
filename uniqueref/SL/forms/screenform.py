# Import Django related libraries and functions
from django import forms

# General Phenosaurus imports
from uniqueref.SL.sharedvars import formvars as fv  # form variables
from uniqueref.generalforms.forminput import FormInput

# Specific Synthetic Lethal imports
from uniqueref.SL.baseclasses import ValidatedSLIQuerySet

import logging
logger = logging.getLogger(__name__)

class ScreenForm(forms.Form):
	def __init__(self, user_details, *args, **kwargs):
		"""
		Return a dropdown form with a list of synthetic lethal screens a user is allowed to see
		:param user_details:
		:param args:
		:param kwargs:
		"""
		authorized_screens = user_details['authorized_screens']
		super(ScreenForm, self).__init__(*args, **kwargs)
		self.fields['screenid'] = forms.ModelChoiceField(
			queryset=ValidatedSLIQuerySet(user_details).queryset_sli_screens().order_by('name'),
			label=fv.screen_choice_label,
			widget=forms.Select(attrs={'class': 'form-control'}))


class ScreenFormInput(FormInput):

	def check(self):
		'''
		Check if screenid is valid
		:return: boolean
		'''
		isint = False
		valid = False
		try:
			int(self.formdata['screenid'][0])
			isint = True
		except Exception:
			pass
		if isint:
			if ValidatedSLIQuerySet(self.user_details).queryset_sli_screens().filter(id=self.formdata['screenid'][0]):
				valid = True
		return valid