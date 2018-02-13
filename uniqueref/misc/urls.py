from django.conf.urls import url, include
import django.contrib.auth.views
from . import views

urlpatterns = [
	url(r'^annotations/', views.ListReferenceAnnotations.as_view(), name='List all reference annotations')
		]