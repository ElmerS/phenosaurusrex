# Import Django related libraries and functions
from django.forms import ModelForm
from django import forms
from django.db.models import Q

# Import other custom phenosaurus functions
from .. import globalvars as gv
from .. import models as db
from .. import custom_functions as cf
import UserMessages

# Other general libraries
import pandas as pd
import numpy as np

FM = UserMessages.FormMessages()

class ScreenForm(forms.Form):
	def __init__(self, *args, **kwargs):
		authorized_screens = kwargs.pop('authorized_screens')
		super(ScreenForm, self).__init__(*args, **kwargs)
		self.fields['screenid']  = forms.ModelChoiceField(queryset=db.Screen.objects.filter(id__in=authorized_screens).filter(screentype='SL').order_by('name'), label=FM.screen_choice_label, widget=forms.Select(attrs={'class': 'form-control'}))


class AnalysisForm(forms.Form):
	def __init__(self, *args, **kwargs):
		compound_input = kwargs.pop('compound_input')
		screenid = compound_input.split("|")[0]
		user = compound_input.split("|")[2]
		self.authorized_screens = map(int, compound_input.split("|")[1].strip("[]").split(','))
		super(AnalysisForm, self).__init__(*args, **kwargs)
		self.fields['replicates'] = forms.MultipleChoiceField(label='Select replicates', choices=[(r[0], str(r[0])) for r in list(db.SLSDatapoint.objects.filter(relscreen_id=screenid).values_list('replicate').distinct())], widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}))
		self.fields['screenid'] = forms.ChoiceField(label='Screen (px)', choices=[(screenid, screenid)], initial=screenid, widget=forms.HiddenInput())
		self.fields['controls'] = forms.MultipleChoiceField(label='Select controls', choices=self.LookUpControls(), widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}))
		self.fields['analysis'] = forms.ChoiceField(label=FM.analysis_choices, choices=self.AnalysesChoices(), initial='normal',
								 widget=forms.Select(attrs={'class': 'form-control'}))
		self.fields['customgenelist'] = forms.ModelMultipleChoiceField(queryset=db.CustomTracks.objects.filter(Q(user__username=gv.publicuser) | Q(user__username=user)).order_by('name'), widget=forms.Select(attrs={'class': 'form-control'}), label=FM.custom_list_label, required=False)

	def LookUpControls(self):
		control_id = int(db.Settings.objects.filter(variable_name='synthetic_lethal_controls').values()[0]['value'])
		choices = []
		if control_id in self.authorized_screens:
			choices = [(r[0], str(r[0])) for r in list(db.SLSDatapoint.objects.filter(relscreen_id=control_id).values_list('replicate').distinct())]
		else:
			self.nocontrols = FM.no_controls_available
		return choices

	def AnalysesChoices(self):
		binom = (('bimom',FM.binom_choice),)
		compare = (('compare', FM.compare_choice),)
		if self.nocontrols:
			return binom
		else:
			return binom + compare

	OnClickActionChoices = (
		('gc', FM.gc_choice),
		('hah', FM.hah_choice),
		('gp', FM.gp_choice)
	)

	oca = forms.ChoiceField(label='Select action on click', choices=OnClickActionChoices, initial='gc',
							widget=forms.Select(attrs={'class': 'form-control'}))

	binom_p_value = forms.DecimalField(required=False, label=FM.binom_p_value_label, initial=gv.pvdc,
									   widget=forms.NumberInput(attrs={'class': 'form-control'}),
									   help_text=FM.p_value_help)
	fisher_p_value = forms.DecimalField(required=False, label=FM.fisher_p_value_label, initial=gv.pvdc,
										widget=forms.NumberInput(attrs={'class': 'form-control'}),
										help_text=FM.p_value_help)
	fdr = forms.BooleanField(initial=True, label=FM.fdr_correction_label,
							 widget=forms.CheckboxInput())
	effect_size = forms.DecimalField(required=False, label=FM.effect_size_label, initial=0,
									 widget=forms.NumberInput(attrs={'class': 'form-control'}))
	directionality = forms.BooleanField(initial=True, label=FM.direction_label,
										widget=forms.CheckboxInput())
	aas = forms.BooleanField(initial=True, label=FM.annotated_all_sig_genes_label,
							 widget=forms.CheckboxInput())
	genes = forms.CharField(widget=forms.TextInput(
		attrs={'class': 'form-control', 'placeholder': 'EZH2 SUZ12 EED', 'style': 'min-width: 100%'}),
							label=FM.annotate_genes_label, required=False)