# Import Django related libraries and functions
from django.contrib.auth.decorators import login_required
from django_pandas.io import read_frame
from django.shortcuts import render
from django.forms import ModelForm
from django.db.models import Q
from django import forms

# Import other custom phenosaurus functions
import globalvars as gv
import models as db
import custom_functions as cf

# Other general libraries
import pandas as pd
import numpy as np
import re

# Different textsizes for labeling the genes, there should be a more sophisticated way, right?
textsize = (
	('8px', '8px'),
	('9px', '9px'),
	('10px', '10px'),
	('11px', '11px'),
	('12px', '12px'),
	('13px', '13px'),
	('14px', '14px'),
	('15px', '15px'),
	('16px', '16px'),
	('17px', '17px'),
	('18px', '18px'),
	('19px', '19px'),
	('20px', '20px'),
)

# oca = on click options
ocao= (
        ('gc', 'Link to Genecards'),
        ('hah', 'Label and highlight datapoint'),
        ('gp', 'Geneplot upon click')
)

cbo = ( #cbo = color by option
	('cbpv','p-value'),
	('cbsc','screen'),
	('track', 'track')
)

so = ( #so = scaling options
	('lin', 'linear'),
	('log','logaritmic')
)

comparison_choices = ( #cbo = color by option
	('unique','Evaluate uniqueness of hits in A vs [B..Z]'),
	('coloroverlay','Indicate hits of screen B in screen A'),
	('mi-arrows','EXPERIMENTAL: MI-shifts A vs B')
)

plot_widths = (
	('small', "".join(['small: ', str(gv.small_geneplot_width), 'px'])),
	('normal', "".join(['normal: ', str(gv.normal_geneplot_width), 'px'])),
	('wide', "".join(['wide: ', str(gv.wide_geneplot_width), 'px'])),
	('dynamic', "".join(['dynamic: ', str(gv.dynamic_geneplot_width), ' px', ' * n screens']))
)

class FixedScreenSummaryForm(forms.Form):
        def __init__(self, *args, **kwargs):
                compound_input = kwargs.pop('compound_input')
                input_arr = compound_input.split('|')
                user = input_arr[0]
                authorized_screens = map(int, compound_input.split("|")[1].strip("[]").replace(' ', '').split(','))
                super(FixedScreenSummaryForm, self).__init__(*args, **kwargs)
                self.fields['screen'].queryset = db.Screen.objects.filter(id__in=authorized_screens).filter(screentype='IP').order_by('name')

        screen = forms.ModelChoiceField(queryset=db.Screen.objects.all(), label='Choose screen')

class SingleIPSPlotForm(forms.Form):
	def __init__(self, *args, **kwargs):
		compound_input = kwargs.pop('compound_input')
		input_arr = compound_input.split('|')
		user = input_arr[0]
		authorized_screens = map(int, compound_input.split("|")[1].strip("[]").replace(' ', '').split(','))
		super(SingleIPSPlotForm, self).__init__(*args, **kwargs)
		self.fields['screen'].queryset = db.Screen.objects.filter(id__in=authorized_screens).filter(screentype='IP').order_by('name')
		self.fields['customgenelistid'].queryset = db.CustomTracks.objects.filter(Q(user__username=gv.publicuser) | Q(user__username=user)).order_by('name')

	screen = forms.ModelChoiceField(queryset=db.Screen.objects.all(), label='Choose screen')
	customgenelistid = forms.ModelMultipleChoiceField(queryset=db.CustomTracks.objects.all(), widget=forms.SelectMultiple(attrs={'size': '5'}), label='Select track(s) to color the datapoints', required=False)

        pvalue = forms.DecimalField(required=False, label='P-value cutoff (can also be written as 1E-xx)', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1}))
	textsize = forms.ChoiceField(label='Textsize (px)', choices=textsize, initial='11px')
	oca = forms.ChoiceField(label='Select action on click', choices=ocao, initial='gc')
	sag = forms.BooleanField(required=False, label='Label all significant hits')
	showtable = forms.BooleanField(required=False, label="List all significant genes in table")
	highlightpps = forms.BooleanField(required=False, label="Encircle hits founds in positive selection screens")
	pvaluepps = forms.DecimalField(required=False, label='P-value cutoff for positive selection screens', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1}))

class UniqueHitFinderForm(forms.Form):
	def __init__(self, *args, **kwargs):
		authorized_screens = kwargs.pop('authorized_screens')
		super(UniqueHitFinderForm, self).__init__(*args, **kwargs)
		self.fields['screen'].queryset = db.Screen.objects.filter(id__in=authorized_screens).filter(screentype='IP').order_by('name')
		self.fields['againstscreen'].queryset = db.Screen.objects.filter(id__in=authorized_screens).filter(screentype='IP').order_by('name')

	screen = forms.ModelChoiceField(queryset=db.Screen.objects.all(), label='Select screen A')
	againstscreen = forms.ModelMultipleChoiceField(queryset=db.Screen.objects.all(), widget=forms.SelectMultiple(attrs={'size': '15'}), label='Select screens [B...Z]')

	oca = forms.ChoiceField(label='Select action on click', choices=ocao, initial='gc')
	comparison = forms.ChoiceField(label='Choose comparison', choices=comparison_choices, initial='unique')
	showtable = forms.BooleanField(required=False, label="List all significant genes in table")
	pvalue = forms.DecimalField(required=False, label='P-value cutoff (can also be written as 1E-xx)', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1}))
	textsize = forms.ChoiceField(label='Textsize (px)', choices=textsize, initial='11px')
	sag = forms.BooleanField(required=False, label='Label all significant hits')
	highlightpps = forms.BooleanField(required=False, label="Encircle hits founds in positivepvaluepps = forms.DecimalField(required=False, label='P-value cutoff for positive selection screens', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1})) selection screens")
	pvaluepps = forms.DecimalField(required=False, label='P-value cutoff for positive selection screens', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1}))

class OpenGeneFinderForm(forms.Form):
	def __init__(self, *args, **kwargs):
		compound_input = kwargs.pop('compound_input')
		user = compound_input.split("|")[0]
		authorized_screens = map(int, compound_input.split("|")[1].strip("[]").split(','))
		super(OpenGeneFinderForm, self).__init__(*args, **kwargs)
		self.fields['screens'].queryset = db.Screen.objects.filter(id__in=authorized_screens).filter(screentype='IP').order_by('name')
		self.fields['customgenelistid'].queryset = db.CustomTracks.objects.filter(Q(user__username=gv.publicuser) | Q(user__username=user)).order_by('name')

	screens = forms.ModelMultipleChoiceField(queryset=db.Screen.objects.all(), widget=forms.SelectMultiple(attrs={'size': '15'}), label="Select screen(s)")
	customgenelistid = forms.ModelMultipleChoiceField(queryset=db.CustomTracks.objects.all(), widget=forms.SelectMultiple(attrs={'size': '5'}), label='and/or select a track ', required=False)

	cb = forms.ChoiceField(label='Color datapoints by', choices=cbo, initial='cbpv')
	pgh = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'checked' : 'checked'}), label="Separate plots for each gene")
	oca = forms.ChoiceField(label='Select action on click', choices=ocao, initial='gc')
	genes = forms.CharField(widget=forms.TextInput(attrs={'size': '160'}), label='Enter genename(s), space separated', required=False)
	pvalue = forms.DecimalField(required=False, label='P-value cutoff (can also be written as 1E-xx)', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1}))
	textsize = forms.ChoiceField(label='Textsize (px)', choices=textsize, initial='11px')
	highlightpss = forms.BooleanField(required=False, label="Indicate if found in positive selection screens")
	pvaluepps = forms.DecimalField(required=False, label='P-value cutoff for positive selection screens', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1})) 
	plot_width = forms.ChoiceField(label='Plot width', choices=plot_widths, initial='normal')

class SinglePSSBubblePlot(forms.Form):
	def __init__(self, *args, **kwargs):
		authorized_screens = kwargs.pop('authorized_screens')
		super(SinglePSSBubblePlot, self).__init__(*args, **kwargs)
		self.fields['screen'].queryset = db.Screen.objects.filter(id__in=authorized_screens).filter(screentype='PS').order_by('name')

	screen = forms.ModelChoiceField(queryset=db.Screen.objects.all(), label="Choose screen")
	pvalue = forms.DecimalField(required=False, label='P-value cutoff (can also be written as 1E-xx)', initial=gv.pvdc, widget=forms.NumberInput(attrs={'step': 0.01, 'min': 0, 'max': 1}))
	sepcolor = forms.BooleanField(required=False, label="Indivual colors for significant hits (disable J.S. mode)")
	oca = forms.ChoiceField(label='Select action on click', choices=ocao, initial='gc')
	scaling = forms.ChoiceField(label='Y-scaling', choices=so, initial='lin')
	textsize = forms.ChoiceField(label='Textsize (px)', choices=textsize, initial='11px')
	sag = forms.BooleanField(required=False, label="Label all significant hits")
	showtable = forms.BooleanField(required=False, label="List all significant genes in table")

class UploadCustomTrack(ModelForm):
	genelist = forms.CharField(validators=[cf.validate_track_genelist], widget=forms.Textarea(attrs={'rows': 60, 'cols': 180}), label="List of genes, space separated")
	description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'cols': 180}), label="A description for this track, max 400 characters")
	name = forms.CharField(validators=[cf.validate_track_name], label="Name for new track, max 100 characters")
	class Meta:
		model = db.CustomTracks
		exclude = ('user',)

class DeleteCustomTrack(ModelForm):
	class Meta:
		model = db.CustomTracks
		fields = []

class GetCustomTracks(forms.Form):
	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user')
		super(GetCustomTracks, self).__init__(*args, **kwargs)
		self.fields['customgenelistid'].queryset = db.CustomTracks.objects.filter(user__username=user).order_by('name')

	customgenelistid = forms.ModelMultipleChoiceField(queryset=db.CustomTracks.objects.all(), widget=forms.SelectMultiple(attrs={'size': '15'}), label='Select one or more tracks to delete ')
