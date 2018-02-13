from django.conf.urls import url, include
#	import django.contrib.auth.views
import views

urlpatterns = [
	url(r'^selectscreen/', views.SelectScreenView.as_view(), name='Plot a Synthetic Lethal Screen - select a screen'),
	url(r'^selectcontrol/', views.SelectScreenView.as_view(), name='Analyze Wiltype control screens'),
	url(r'^selectparameters/', views.SelectParametersView.as_view(), name='Plot a Synthetic Lethal Screen - set paramters'),
	url(r'^results/', views.ScreenPlotView.as_view(), name='Plot a Synthetic Lethal Screen - results')
]