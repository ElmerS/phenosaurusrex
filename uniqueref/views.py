from django.shortcuts import render, render_to_response
from bokeh.plotting import figure, output_file, show, ColumnDataSource, vplot
from bokeh.models import HoverTool, TapTool, OpenURL, Circle, Text, CustomJS
from bokeh.models.widgets import Select, Slider, DataTable, DateFormatter, TableColumn, StringEditor, tables, StringFormatter
from bokeh.models.layouts import WidgetBox
from django.http import HttpResponse

from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.layouts import column
from django_pandas.io import read_frame
import pandas as pd
import numpy as np
from django.contrib.auth.decorators import login_required
from django import forms
import operator
from django.db.models import Q, Avg, Max, Min	# To find min and max values in QS
from collections import namedtuple
from .models import *
from custom_functions import *
import forms
from plots import *
import plots
import custom_functions as cf


@login_required
def get_authorized_screens(request):
	gids = request.user.groups.values_list('id',flat=True)
	authorized_screens = get_authorized_screens_from_gids(gids)
	return authorized_screens

@login_required
def landing(request):
	return render(request, 'uniqueref/landing.html', {})

@login_required
def help(request):
	return render(request, "uniqueref/help.html", {})

@login_required
# This view does not use a GET request so the authorization still need to happen. Pass list of authorized screens on to first function that is called (list_screens)
def listscreens(request):
	ipdata = list_screens('IP', get_authorized_screens(request)) # Generate the table
	psdata = list_screens('PS', get_authorized_screens(request)) # Generate the table
	return render(request, "uniqueref/listscreens.html", {'ipdata':ipdata, 'psdata':psdata})	

@login_required
# This view does not use a GET request so the authorization still need to happen. Pass user-ID to to list_tracks
def listtracks(request):
	data = list_tracks(request.user) # Generate the table
	return render(request, "uniqueref/listtracks.html", {'data':data})

@login_required
def updates(request):
	updates = get_qs_updates().order_by('-date')
	return render(request, "uniqueref/updates.html", {'updates':updates})

@login_required
# Authorization not required
def listgenes(request):
	data = list_genes() # Generate the table
	return render(request, "uniqueref/listgenes.html", {'data':data})

@login_required
def uploadtrack(request):
	uploadform = forms.UploadCustomTrack()
	data = ""
	if request.POST:	
		uploadform = forms.UploadCustomTrack(request.POST)
		# This needs some more validation! Is the name unique? Do the given genes actually exist in the databse?
		if uploadform.is_valid():
			userform = uploadform.save(commit=False)
			userform.user = request.user
			userform.save()
			data = succes_track_upload
			#return redirect('/uniqueref/succesmod')
		else:
			data = failed_track_upload
	return render(request, "uniqueref/uploadtrack.html", {'form': uploadform, 'data': data})

@login_required
# This needs a lot of validation. Validation in the form and in additional function to check if GET request (URL) has not been modified in illegal way.
def deletetrack(request):
	filter = forms.GetCustomTracks(user=request.user)
	customgenelistids = request.GET.getlist('customgenelistid', '')
	if (customgenelistids != ''):
		data = validate_delete_track(customgenelistids, user=request.user)
	else:
		data = formerror
	return render(request, "uniqueref/deletetrack.html", {'filter': filter, 'data': data})

	
@login_required
# Requires authorization on form level (which screens to show)
# Requires URL validation to check if GET request (URL) has not been modified in illegal way.
# After these validators the methods can be considered safe. 
def PSSBubblePlot(request):
	# Call the search- and customization form
	# Check user groups to see which screen are allowed to be seen by the user
	authorized_screens=get_authorized_screens(request)
	filter = forms.SinglePSSBubblePlot(authorized_screens=authorized_screens) # First load the filter from forms
	# Fetch the input data from the URL
	screenid = request.GET.get('screen', '') # screenid is parsed as a number
	givenpvalue = request.GET.get('pvalue', '') # This is for setting p-value cutoff for coloring
	sepcolor = request.GET.get('sepcolor')
	scaling = request.GET.get('scaling')
	sag = request.GET.get('sag','') # if label all genes is on, label all genes
	oca = request.GET.get('oca', '') # What to do when clicking on a hit
	showtable = request.GET.get('showtable', '') # What to do when clicking on a hit
	giventextsize = request.GET.get('textsize', '')	# This is for determining the size of labels next to a gene
	# If the form is empty (defied by no screenid given) then just display an empty form
	if not screenid:
		return render(request, "uniqueref/pssbubbleplot.html", {'filter':filter})
	# This elif statement is IMPORTANT and always required for GET requests.
	# It checks whether the user is actually allowed to request the data he/she is asking for
	elif int(screenid) in authorized_screens:
		if sepcolor == "on":
			sepbool=True
		else:
			sepbool=False
		textsize = set_textsize(giventextsize)
		pvcutoff = set_pvalue(givenpvalue)
		title = title_single_screen_plot(screenid, authorized_screens) # Get the title for the plot, contains a QS --> authorized_screens required
		df = generate_df_ppss(screenid, pvcutoff, sepbool, authorized_screens) # Generate the dataframe for the plot, contains a QS --> authorized_screens required
		p = pbubbleplot(title, df, scaling, oca, sag, textsize, authorized_screens) # Generate the plot, contains a QS --> authorized_screens required
		if showtable == "on":
			data = generate_ps_tophits_list(df) # Generate the table
		else:
			data = ""
		script, div = components(p, CDN)
		return render(request, "uniqueref/pssbubbleplot.html", {"the_script":script, "the_div":div, "filter":filter, 'data':data})
	# If use 
	else:
		data = request_screen_authorization_error
		return render(request, "uniqueref/pssbubbleplot.html", {'filter':filter, 'data':data})


@login_required
def IPSFishtail(request):
	# Call the search- and customization form
	# Check user groups to see which screen are allowed to be seen by the user
	authorized_screens=get_authorized_screens(request)
	strigefied_authorized_screens = ''
	for i in range(0, len(authorized_screens)):
		strigefied_authorized_screens = strigefied_authorized_screens+','+str(authorized_screens[i])
	input = str(request.user)+'|'+strigefied_authorized_screens.lstrip(',')
	filter = forms.SingleIPSPlotForm(compound_input=input) # First load the filter from .form
	# Fetch the input data from the URL
	oca = request.GET.get('oca', '') # What to do when clicking on a hit
	screenid = request.GET.get('screen', '') # screenid is parsed as a number packed in a string
	giventextsize = request.GET.get('textsize', '')	# This is for determining the size of labels next to a gene
	givenpvalue = request.GET.get('pvalue', '') # This is for setting p-value cutoff for coloring
	sag = request.GET.get('sag','') # if label all genes is on, label all genes
	showtable = request.GET.get('showtable', '')
	highlightpps = request.GET.get('highlightpps', '')
	givenpvaluepps = request.GET.get('pvaluepps', '')
	customgenelistid = request.GET.getlist('customgenelistid', '')
	# Test if input is given, otherwise do nothing
	if screenid=='':
		data=formerror
		return render(request, "uniqueref/singlescreen.html", {'filter':filter, 'data':data})
	# This elif statement is IMPORTANT and always required for GET requests.
	# It checks whether the user is actually allowed to request the data he/she is asking for
	elif int(screenid) in authorized_screens:
		textsize = set_textsize(giventextsize)
		pvcutoff = set_pvalue(givenpvalue)
		pvcutoffpps = set_pvalue(givenpvaluepps)
		title = title_single_screen_plot(screenid, authorized_screens)
		df = generate_df_pips(screenid, pvcutoff, authorized_screens)
		legend = pd.DataFrame()
		if (len(customgenelistid)>=1):
			df, legend = color_fishtail_by_track(df, customgenelistid, request.user, pvcutoff)
		if highlightpps == 'on':
			df = mod_df_linecolor_for_pss(df, pvcutoffpps, authorized_screens)
		else:
			df['adddescription'] = ''
		p = pfishtailplot(title, df, sag, oca, textsize, authorized_screens, legend)
		if showtable == "on":
			data = generate_ips_tophits_list(df) # Generate the table# If input has been given then the fun starts
		else:
			data = ""
		script, div = components(p, CDN)
		return render(request, "uniqueref/singlescreen.html", {"the_script":script, "the_div":div, 'filter':filter, 'data':data})
	elif (screenid in authorized_screens)==False: # If something else is the case then someone has been screwing around with the URL. That we do not accept.
		data = request_screen_authorization_error
		return render(request, "uniqueref/singlescreen.html", {'filter':filter, 'data':data})
	else:
		return render(request, "uniqueref/singlescreen.html", {'filter':filter, 'data':data})

@login_required	        	   	
def uniquefinder(request):
	# Check user groups to see which screen are allowed to be seen by the user
	authorized_screens=get_authorized_screens(request)
	# Call the filterform
	filter = forms.UniqueHitFinderForm(authorized_screens=authorized_screens) # First load the filter from .forms
	# Retrieve all form input
	comparison = request.GET.get('comparison', '')
	oca = request.GET.get('oca', '') # Check whether input has already been given
	screenid = request.GET.get('screen', '') # screenid is parsed as a number (the PK of screen)
	against_list = request.GET.getlist('againstscreen', '') # This is the actual name of gene, or a wildcard, case insensitive 
	showtable = request.GET.get('showtable', '')
	sag = request.GET.get('sag', '') # if label all genes is on, label all genes
	giventextsize = request.GET.get('textsize', '')	# This is for determining the size of labels next to a gene
	givenpvalue = request.GET.get('pvalue', '') # This is for setting p-value cutoff for coloring
	highlightpps = request.GET.get('highlightpps', '')
	givenpvaluepps = request.GET.get('pvaluepps', '')
	customgenelistid = request.GET.getlist('customgenelistid', '')

	# First check the whether the data given by the user makes any sense at all...0
	error = validate_uniquefinder_input(against_list, screenid, comparison, authorized_screens)
	if (error != ''):
		return render(request, "uniqueref/uniquefinder.html", {'filter':filter, 'error':error})

	else: # Only if user didn't change the URL illegally continue with the plot
		if (not against_list and comparison=='unique'):
			against_list = list(cf.authorized_qs_screen(authorized_screens).filter(screentype='IP').exclude(id=screenid).order_by('name').distinct().values_list('id',flat=True))
		data = ''
		textsize = set_textsize(giventextsize)
		pvcutoff = set_pvalue(givenpvalue)
		pvcutoffpps = set_pvalue(givenpvaluepps)
		title = title_ips_uniquefinder(screenid, against_list, comparison, authorized_screens)
		df, df_arrow, legend = generate_df_pips_uniquefinder(screenid, against_list, pvcutoff, comparison, authorized_screens)
		# This depends on the screen 
		if highlightpps == 'on':
			df = mod_df_linecolor_for_pss(df, pvcutoffpps, authorized_screens)
		else:
			df['adddescription'] = ''
			df['linecolor'] = df['color']
		p = pfishtailplot(title, df, sag, oca, textsize, authorized_screens, legend, df_arrow)
		if showtable == "on":
			data = generate_ips_tophits_list(df) # Generate the table# If input has been given then the fun starts
		script, div = components(p, CDN)
		return render(request, "uniqueref/uniquefinder.html", {"the_script":script, "the_div":div, 'filter':filter, 'data':data})
	  	
@login_required
def opengenefinder(request):
	# Call the search- and customization form
	# Check user groups to see which screen are allowed to be seen by the user
	authorized_screens=get_authorized_screens(request)
	strigefied_authorized_screens = ''
	for i in range(0, len(authorized_screens)):
		strigefied_authorized_screens = strigefied_authorized_screens+','+str(authorized_screens[i])
	input = str(request.user)+'|'+strigefied_authorized_screens.lstrip(',')
	filter = forms.OpenGeneFinderForm(compound_input=input) # First load the filter from .forms

	# Pull the data from the URL
	oca = request.GET.get('oca', '') # What to do when clicking on a hit
	screenids = request.GET.getlist('screens', '') # screenid is parsed as a number
	genenamesstring = request.GET.get('genes', '')
	giventextsize = request.GET.get('textsize', '')	# This is for determining the size of labels next to a gene
	colorby = request.GET.get('cb', '')
	pgh = request.GET.get('pgh', '') # Plot gene histograms
	givenpvalue = request.GET.get('pvalue', '') # This is for setting p-value cutoff for coloring
	sag = request.GET.get('sag','') # if label all genees is on, label all genes
	highlightpss = request.GET.get('highlightpss', '')
	givenpvaluepss = request.GET.get('pvaluepss', '')
	customgenelistids = request.GET.getlist('customgenelistid', '')
	plot_width = request.GET.get('plot_width', '')

	# Test if input is given, otherwise do nothing
	if ((not genenamesstring and not customgenelistids) or (not screenids)):
		error=formerror
		return render(request, 'uniqueref/opengenefinder.html', {'filter':filter, 'error':error})
	# If input has been given then the fun starts
	elif set(map(int, screenids)).issubset(set(authorized_screens)):# Test if user didn't change the URL in an illegal way, if so, go to else and raise an error
		# Process the input parameters
		error = ''
		textsize = set_textsize(giventextsize) # Set the standard value if nothing given
		pvcutoff = set_pvalue(givenpvalue) # Set the standard value if nothing given
		pvcutoffpss = set_pvalue(givenpvaluepss) # Set the standard value if nothing given
		screenids_array = np.asarray(screenids)
		given_genes_array, error = create_genes_array(genenamesstring) # Call the function create_genes_array to check the given genenames against the genes-table and convert to array
		custom_gene_list_array = gene_array_from_trackids(customgenelistids) # Retrieve the genes from the custom_track
		genes_array = np.concatenate((given_genes_array, custom_gene_list_array), axis=0) # Concatenate the two arrays (from custom_track and the open search field to enter a genename)
		# If it needs to be indicated when a gene has been found as hit in a postive selection screen
		if highlightpss=="on":		# Highlighting of datapoints is not so usefull in gene-histograms or in a fishtails plot of the same gene within multiple screens but everything will be highlight.
			genes_df = mod_df_geneplot_with_pss(genes_array, pvcutoffpss, authorized_screens) # Therefore, in case of a gene-histogram, the title tells whether the gene is a hit
			data = genes_df.to_html(index=False) # And in case of a fishtailplot we create a table (hence we need the data:data tag)
		else:
			genes_df = pd.DataFrame({'relgene': pd.Series(genes_array), 'adddescription': pd.Series(['' for i in range(0, len(genes_array))])})
			data = ''
		if pgh=="on": # pgh==on means plot separate geneplots
			# Need some safety mechanism to prevent people plotting more than a certain numer (max_graphs) at the same time... that's just too much work
			if (len(genes_array)>50):
				error = max_graphs_warning
				return render(request, 'uniqueref/opengenefinder.html', {'filter':filter, 'error':error})
			# Becuase multiple plot can be created, the function to create the dataframes is called from single_gene_plots instead in advance
			plotlist = plots.single_gene_plots(genes_df, screenids_array, pvcutoff, authorized_screens, plot_width)
			p = plots.vertial_geneplots_layout(plotlist)
		else: # if pgh!=on than a compound fishtail is plotted were all datapoints of multiple screens of one ore more genes are plotted on top of each other
			df, legend = df_compound_geneplot(genes_df, screenids_array, colorby, pvcutoff, authorized_screens, customgenelistids, request.user)
			# In case a compound geneplot needs to be colored by tracks
			#if colorby=='track':
			#	df, legend = color_fishtail_by_track(df, customgenelistids, request.user, pvcutoff)
			title = create_title_for_compound_genefinder(given_genes_array, customgenelistids, authorized_screens)
			p = pfishtailplot(title, df, sag, oca, textsize, authorized_screens, legend)

		script, div = components(p)
		return render(request, 'uniqueref/opengenefinder.html', {'the_script':script, 'the_div':div, 'filter':filter, 'data':data, 'error':error})
	else:
		error = request_screen_authorization_error
		return render(request, 'uniqueref/opengenefinder.html', {'filter':filter, 'error':error})


@login_required
def FixedScreenSummary(request):
		# Check user groups to see which screen are allowed to be seen by the user
		authorized_screens = get_authorized_screens(request)
		strigefied_authorized_screens = ''
		for i in range(0, len(authorized_screens)):
			strigefied_authorized_screens = strigefied_authorized_screens + ',' + str(authorized_screens[i])
		input = str(request.user) + '|' + strigefied_authorized_screens.lstrip(',')

		# Based on the information in 'input' we can now call the search form
		filter = forms.FixedScreenSummaryForm(compound_input=input) # First load the filter from .form

		# Fetch the form input data from the URL
		screenid = request.GET.get('screen', '') # screenid is parsed as a number packed in a string

		# Test if input is given, otherwise do nothing
		if screenid=='':
			data=formerror
			return render(request, "uniqueref/fixedscreensummary.html", {'filter':filter, 'data':data})
		# The following elif statement is IMPORTANT and always required for GET requests. It checks whether the user is actually allowed to request the data he/she is asking for, this is also the only elif statement that actually displats the information that is meant to be displayed in this view
		elif int(screenid) in authorized_screens:
			p = BuildFixedScreenSummary(screenid, authorized_screens, user=request.user)
			script, div = components(p, CDN)
			return render(request, "uniqueref/fixedscreensummary.html", {"the_script":script, "the_div":div, 'data':'', 'filter':filter})
		# If something else is the case then someone has been screwing around with the URL. Raise an error
		elif (screenid in authorized_screens)==False:
			data = request_screen_authorization_error

		else:
			return render(request, "uniqueref/fixedscreensummary.html", {'filter':filter, 'data':data})


@login_required
def FixedScreenSeqSummary(request):
	# Check user groups to see which screen are allowed to be seen by the user
	authorized_screens = get_authorized_screens(request)
	# Because it is not artibrary that the sequencing statistics are present for all screens, add a little extra filtering to list only those that actually have the statistics calculated
	authorized_screens = list(cf.get_qs_summary(authorized_screens).values_list('relscreen_id', flat=True))
	strigefied_authorized_screens = ''
	for i in range(0, len(authorized_screens)):
		strigefied_authorized_screens = strigefied_authorized_screens + ',' + str(authorized_screens[i])
	input = str(request.user) + '|' + strigefied_authorized_screens.lstrip(',')

	# Based on the information in 'input' we can now call the search form, we can perfectly recycle the form made for the FixedScreenSummary (without the Seq) because the question is the same.
	filter = forms.FixedScreenSummaryForm(compound_input=input)  # First load the filter from .form

	# Fetch the form input data from the URL
	screenid = request.GET.get('screen', '')  # screenid is parsed as a number packed in a string

	# Test if input is given, otherwise do nothing
	if screenid == '':
		data = formerror
		return render(request, "uniqueref/fixedscreenseqsummary.html", {'filter': filter, 'data': data})
	# The following elif statement is IMPORTANT and always required for GET requests. It checks whether the user is actually allowed to request the data he/she is asking for, this is also the only elif statement that actually displats the information that is meant to be displayed in this view
	elif int(screenid) in authorized_screens:
		p = BuildFixedScreenSeqSummary(screenid, authorized_screens)
		script, div = components(p, CDN)
		return render(request, "uniqueref/fixedscreenseqsummary.html",
					  {"the_script": script, "the_div": div, 'data': '', 'filter': filter})
	# If something else is the case then someone has been screwing around with the URL. Raise an error
	elif (screenid in authorized_screens) == False:
		data = request_screen_authorization_error

	else:
		return render(request, "uniqueref/fixedscreenseqsummary.html", {'filter': filter, 'data': data})
