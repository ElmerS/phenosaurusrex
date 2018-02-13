from django.shortcuts import render, redirect
from django.urls import reverse

from .. views import BaseView

from forms import screenform
from forms import parameterform
from comparativeanalysis import ComparativeAnalysis

# Dev imports
import logging
logger = logging.getLogger(__name__)

class SelectScreenView(BaseView):

	form_class = screenform.ScreenForm
	template_name = 'SL/selectscreen.html'

	def get(self, request, *args, **kwargs):
		super(SelectScreenView, self).get(request)
		self.context['form'] = self.form_class(self.user_details)
		return render(request, self.template_name, self.context)


class SelectParametersView(BaseView):

	form_class = parameterform.ParameterForm
	template_name = 'SL/selectparameters.html'

	def get(self, request, *args, **kwargs):
		super(SelectParametersView, self).get(self, request, *args, **kwargs)
		if screenform.ScreenFormInput(self.user_details, self.formdata).check():
			self.context['form'] = self.form_class(self.user_details, self.formdata['screenid'][0])
			return render(request, self.template_name, self.context)
		else: # Redirect to SelectScreenView if user has modified url illegally.
			return redirect(reverse('Plot a Synthetic Lethal Screen - select a screen')) # does not work yet


class ScreenPlotView(BaseView):

	template_name = 'SL/results.html'

	def get(self, request, *args, **kwargs):
		super(ScreenPlotView, self).get(self, request, *args, **kwargs)
		if True == True: # this needs to be replaced by if parameterform.ParameterFormInput(self.user_details, self.formdata).check():
			#logger.error("Formdata: %s" % str(self.formdata))
			comparison = ComparativeAnalysis(self.user_details, self.formdata)
			renderobjects = comparison.process()
			self.context.update(renderobjects)
		else:
			pass # parse some error


		return render(request, self.template_name, self.context)

