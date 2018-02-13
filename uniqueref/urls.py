from django.conf.urls import url, include
from django.conf import settings
import views

urlpatterns = [
	url(r'^$', views.home, name='home'),
	url(r'^sources/', include('uniqueref.misc.urls')),  # Import urls for misc views (such as lists of genes etc.)
	url(r'^synthetic-lethality/', include('uniqueref.SL.urls')),  # Imports urls file for synthetic lethality
	url(r'^fixedscreensummary/', views.FixedScreenSummary, name='Screen Summary'),
	url(r'^simpleplot/', views.IPSFishtail, name='Single Intracellular Fixed Screen'),
	url(r'^listscreens/', views.listscreens, name='List all Screens'),
	url(r'^listtracks/', views.listtracks, name='List all Tracks'),
	url(r'^listgenes/', views.listgenes, name='List all Genes'),
	url(r'^uploadtrack/', views.uploadtrack, name='Upload new track'),
	url(r'^deletetrack/', views.deletetrack, name='Delete track'),
	url(r'^opengenefinder/', views.opengenefinder, name='Find gene'),
	url(r'^uniquefinder/', views.uniquefinder, name='UniqueFinder'),
	url(r'^pssbubbleplot/', views.PSSBubblePlot, name='BubblePlot'),
	url(r'^help/', views.help, name='Documentation'),
	url(r'^updates/', views.updates, name='Update History'),
	url(r'^switch-reference-genome/', views.SwitchReference.as_view(), name='Switch Reference Genome')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns