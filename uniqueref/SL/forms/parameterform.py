# Import Django related libraries and functions
from django import forms
from django.db.models import Q

# Import other custom phenosaurus functions
from uniqueref import globalvars as gv
from uniqueref import models as db
from uniqueref.SL.sharedvars import formvars as fv  # form variables, gonna need a lot of them
from uniqueref.generalforms.forminput import FormInput

# Specific Synthetic Lethal imports
from uniqueref.SL.baseclasses import ValidatedSLIQuerySet


class ParameterForm(forms.Form):
	def __init__(self, user_details, screen_id, *args, **kwargs):
		super(ParameterForm, self).__init__(*args, **kwargs)
		self.user_details = user_details
		self.screenid = screen_id
		self.controls, self.controlname = self.lookupcontrols()
		self.error = False
		# This is a potentially slow query... need to think of something better
		self.fields['replicates'] = forms.MultipleChoiceField(
			label='Select replicates',
			choices=[(r[0], str(r[0])) for r in list(
				db.SLSDatapoint.objects.filter(relscreen_id=self.screenid).values_list('replicate').distinct())],
			widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control', 'checked':'checked'}))
		# The following is really a bit disgusting: is simple pulls the previously fetched variable through the second
		# http GET request. It's gross. Don't wanna talk about it and should be fixed asap into something more pretty.
		self.fields['screenid'] = forms.IntegerField(
			initial=self.screenid,
			widget=forms.HiddenInput())
		self.fields['controls'] = forms.MultipleChoiceField(
			choices=self.controls,
			label=self.controlname,
			widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control', 'checked':'checked'}))
		self.fields['customgenelist'] = forms.ModelMultipleChoiceField(
			queryset=db.CustomTracks.objects.filter(
				Q(user__username=gv.publicuser) | Q(user=self.user_details['uid'])).order_by('name'),
			widget=forms.SelectMultiple(attrs={'size': '5', 'class': 'form-control'}),
			label=fv.custom_list_label,
			required=False)



	rendering_mode = forms.ChoiceField(label=fv.rendering_mode_label, choices=fv.rendering_mode, initial='default',
								 widget=forms.Select(attrs={'class': 'form-control'}))

	oca = forms.ChoiceField(label='Select action on click', choices=fv.onclickactionchoices, initial=fv.default_oca,
							widget=forms.Select(attrs={'class': 'form-control'}))

	binom_p_value = forms.DecimalField(required=False, label=fv.binom_p_value_label, initial=gv.pvdc,
									   widget=forms.NumberInput(attrs={'class': 'form-control'}),
									   help_text=fv.p_value_help)

	fisher_p_value = forms.DecimalField(required=False, label=fv.fisher_p_value_label, initial=gv.pvdc,
										widget=forms.NumberInput(attrs={'class': 'form-control'}),
										help_text=fv.p_value_help)

	fdr = forms.BooleanField(required=False, initial=True, label=fv.fdr_correction_label,
							 widget=forms.CheckboxInput())

	effect_size = forms.DecimalField(required=False, label=fv.effect_size_label, initial=fv.default_effect_size,
									 widget=forms.NumberInput(attrs={'class': 'form-control'}))

	directionality = forms.BooleanField(required=False, initial=fv.default_directionality_constraint, label=fv.direction_label,
										widget=forms.CheckboxInput())

	aas = forms.BooleanField(required=False, initial=fv.default_aas, label=fv.annotated_all_sig_genes_label,
							 widget=forms.CheckboxInput())

	aggregate = forms.BooleanField(required=False, initial=fv.aggregate, label=fv.aggregate_label,
							 widget=forms.CheckboxInput())

	genes = forms.CharField(widget=forms.TextInput(
		attrs={'class': 'form-control', 'placeholder': 'EZH2 SUZ12 EED', 'style': 'min-width: 100%'}),
		label=fv.annotate_genes_label, required=False)

	rendering = forms.ChoiceField(label='Select alternative rendering', choices=fv.renderingchoices,
							widget=forms.Select(attrs={'class': 'form-control'}))

	table = forms.BooleanField(required=False, initial=fv.table, label=fv.table_label,
							 widget=forms.CheckboxInput())


	def lookupcontrols(self):
		"""
		To each screen there's only one control (comprising of 4 replicates) associated. However, diferent screens can\
		be analyzed with different controls so which control is assocaited is stored in database model of the screen.
		So first the associated controls need to be queryed and checked whether the user actually has permission to the
		associated controls as well. Then a list of the available replicates for the should be made.
		"""
		controls = []
		controlname = None
		qs = ValidatedSLIQuerySet(self.user_details)
		control_id = int(qs.queryset_single_screen(self.screenid).values_list('controlscreen')[0][0])
		if control_id and control_id in self.user_details['authorized_screens']:
			controls = [(r[0], str(r[0])) for r in list(db.SLSDatapoint.objects.filter(
				relscreen__id=control_id).values_list('replicate').distinct())]
			controlname = "(Name wildtype control: " + db.Screen.objects.filter(id=control_id).values_list('name')[0][0] + ")"
		else:
			self.error = fv.no_controls_available
		return controls, controlname

class ParameterFormInput(FormInput):
	def checkparameterforminput(self):
		valid = int(self.formdata['screenid'][0]) in self.user_details['authorized_screens']
		"""if not valid:
			self.context['error'] = errors.request_screen_authorization_error"""
