'''
Here the views that render the pages under 'Data Sources' and 'Help' should be put here.
Some of these views still reside in views.py and should be moved at some point.
'''

from django.shortcuts import render

from ..views import BaseView
from . import list_functions

class ListReferenceAnnotations(BaseView):

	template_name = 'uniqueref/listannotations.html'

	def get(self, request, *args, **kwargs):
		super(ListReferenceAnnotations, self).get(request)
		self.context['table'] = list_functions.annotation_table(self.user_details).table
		return render(request, self.template_name, self.context)