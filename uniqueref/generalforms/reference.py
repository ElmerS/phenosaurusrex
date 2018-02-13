# Django stuff
from django import forms

# Own classes
from .. import models
from uniqueref.baseclasses import ValidatedQuerySet
from uniqueref.generalforms.forminput import FormInput


class SwitchReference(forms.Form):
	ref = forms.ModelChoiceField(queryset=models.ReferenceGenome.objects.all(), label="Choose reference",
								   widget=forms.Select(attrs={'class': 'form-control'}))

class ReferenceFormInput(FormInput):

	def check(self):
		'''
		# Check whether a ref. is was received from the form, has the right format(int) and is present in DB

		:param user_details:
		:return result:
		'''
		result = False
		try:
			self.formdata['ref']
			int(self.formdata['ref'][0])
			int(self.formdata['ref'][0]) in list(ValidatedQuerySet(
						self.user_details).get_refgenomes().values_list('id', flat=True).distinct())
			result = True
		except Exception:
			pass
		return result