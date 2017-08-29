from django.conf.urls import url
import django.contrib.auth.views
from .views import *

urlpatterns = [
    url(r'^syntheticlethal/', SyntheticLethalView, name='syntheticlethal'),
	url(r'^$', home, name='home'),
	url(r'^$', userlanding, name='landing'),
	url(r'^fixedscreensummary/', FixedScreenSummary, name='Screen Summary'),
	url(r'^fixedscreenseqsummary/', FixedScreenSeqSummary, name='Summary of Sequence Statistics Fixed Screen'),
	url(r'^simpleplot/', IPSFishtail, name='Single Intracellular Fixed Screen'),
	url(r'^listscreens/', listscreens, name='List all Screens'),
	url(r'^listtracks/', listtracks, name='List all Tracks'),
	url(r'^listgenes/', listgenes, name='List all Genes'),
	url(r'^uploadtrack/', uploadtrack, name='Upload new track'),
	url(r'^deletetrack/', deletetrack, name='Delete track'),
	url(r'^opengenefinder/', opengenefinder, name='Find gene'),
	url(r'^uniquefinder/', uniquefinder, name='UniqueFinder'),
	url(r'^pssbubbleplot/', PSSBubblePlot, name='BubblePlot'),
	url(r'^help/', help, name='Documentation'),
	url(r'^updates/', updates, name='Update History'),
]
