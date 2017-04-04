from django_pandas.io import read_frame
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
import sys
import ast
from uniqueref.plots import pfishtailplot
import pandas as pd
import numpy as np
import operator
import math
from globalvars import *  # The file globalvars.py includes all globally used variables like colors, p-value cuttoffs etc.
from django.db.models import Q, Avg, Max, Min
from .models import *
from django.shortcuts import render
import requests
from bokeh.palettes import Inferno10, Reds9, RdYlBu10, Viridis10, RdYlGn10, RdPu9, Purples9, PuRd9, PRGn10, Greens4, PiYG10, PuOr10, Spectral10
from collections import Counter
import plots
import globalvars as gv

##########################################################
# 1. General Functions                                   #
##########################################################

##########################################################
#               QuerySet Authorization                   #
#    !!!! Querysets are EXCLUSIVELY allowd here!!!!!     #
##########################################################

# This function creates a list of all screen-id's based on the users group ids (GIDS)
# The authorized querysets use this function to determine which screens and/or datapoints can be queried by a certain user
def get_authorized_screens_from_gids(gids):
    authorized_screens =  Screen.objects.filter(groups__in=gids).distinct().values_list('id',flat=True) #### THIS IS NOT A TRUE PYTHON LIST! KEEP THAT IN MIND, CANNOT DO str(list) because you will get [1,2,3...,19, ...(remaining elements truncated)]
    return authorized_screens

def authorized_qs_screen(authorized_screens):
    qs_screen = Screen.objects.filter(id__in=authorized_screens)
    return qs_screen

def authorized_qs_IPSDatapoint(authorized_screens):
    qs_IPSDatapoint = IPSDatapoint.objects.filter(relscreen_id__in=authorized_screens)
    return qs_IPSDatapoint

def authorized_qs_PSSDatapoint(authorized_screens):
    qs_PSSDatapoint = PSSDatapoint.objects.filter(relscreen_id__in=authorized_screens)
    return qs_PSSDatapoint

# Query the genes and create dataframe, always needed, no authorization required
def get_qs_gene():
    qs_gene = Gene.objects.all()
    return qs_gene

# This is a bit of a special case as all authorization is checked by forms. Still... the queryset can get a bit safer
def get_qs_customtracks(onlypublic=False):
    if (onlypublic==True):
        qs_customtracks = CustomTracks.objects.filter(user__username=gv.publicuser)
    else:
        qs_customtracks = CustomTracks.objects.all()
    return qs_customtracks

def get_qs_updates():
    qs_updates = UpdateHistory.objects.all()
    return qs_updates

def get_qs_summary(authorized_screens):
    qs_summary = SeqSummary.objects.filter(relscreen_id__in=authorized_screens)
    return qs_summary

def get_qs_custom_variables():
    qs_custom_variables = CustomVariables.objects.all()
    return qs_custom_variables

##########################################################
#  !!!!     NO QUERYSETS ALLOWED BELOW THIS LINE!!!      #
##########################################################

def create_df_gene():
    df_gene=get_qs_gene().to_dataframe() #Create a dataframe from all genes
    return df_gene

# Find max mi value of current dataframe
def findmax(df):
    max = df['mi'].max()
    max = max*1.1
    return max

# Find min mi value of current dataframe
def findmin(df):
    min = df['mi'].min()
    min = min*1.1
    return min

# Create a dataframe for the screen summaries
def create_df_summary(qs):
    df_summary=qs.to_dataframe()
    return df_summary

# A general function for splitting arrays, use as split(array, new arraylength)
def split(arr, size):
     arrs = []
     while len(arr) > size:
         pice = arr[:size]
         arrs.append(pice)
         arr   = arr[size:]
     arrs.append(arr)
     return arr
 
 # Convert values to log, we do it here because it makes it easy to change the log-value app-wide at once 
def logconversion(val):
    logval = np.log2(val)
    return logval

# A function to determine the size of text-labels
def set_textsize(giventextsize):
    if not giventextsize:
        textsize = standard_text_size # Standard font-size if not given
    else:
        textsize = giventextsize
    return textsize

# A fuctions to set the p-value cutoff
def set_pvalue(givenpvalue):
    if not givenpvalue:
        pvcutoff = pvdc # Standard cutoff p-value if not given
    else:
        pvcutoff = float(givenpvalue)    # Convert the given p-value to a float
    return pvcutoff

# Function to generate the title for a plot displaying a single screen
def title_single_screen_plot(screenid, authorized_screens):
    df_screenname = authorized_qs_screen(authorized_screens).filter(id=screenid).to_dataframe()
    screendesc = df_screenname.get_value(0, 'description') # Extract the description of the screen
    return screendesc

def create_genes_array(input_string, upload=False):
    # First receive the list of genes given by the user as a string and split that string into an array, values are space separated
    input_list = input_string.split()
    qs_gene = get_qs_gene()
    # Before parsing back the list as array it is really essential to check if the genes actually exist in the database, otherwise we may run into NaN errors
    # Therefore, use the list to query the gene-table return whatever matched the gene-names in the table
    # We may want to raise an error....?
    validated_list = qs_gene.filter(name__in=input_list).to_dataframe()['name'].tolist()
    validated_array = np.asarray(validated_list)
    if (len(input_list) != len(validated_list)):
        non_match_list = list(set(input_list) - set(validated_list)) # Find the items that do not match the databse
        if (upload==True):
            non_match_string = ' '.join(non_match_list)
            error = "Could not find these genes: %s. Copy-paste the following list to continue without the missing genes: %s" %(non_match_string, str(' '.join(validated_array)))
        else:
            url_list = []
            for x in non_match_list:
                url_list.append(''.join(('<a href=\"', ucsc_link, x, '\"', '>', x, '</a>'))) # The quotation marks before join are the separator, ie. theres is no separator
            url_list_join = ','.join(url_list) # The genes themself we want to separate by a comma
            suggested_genes = find_somewhat_matching_gene_names(non_match_list)
            error = "%s %s %s<br>%s %s<p>" %(gene_not_found_error, url_list_join, genome_browser_link_text, suggested_genes_text, suggested_genes)
    else:
        error = ''
    return validated_array, error

def find_somewhat_matching_gene_names(non_match_list):
    qs_gene = get_qs_gene()
    contains_list = []
    for x in non_match_list:
        contains_list = np.concatenate((contains_list, qs_gene.filter(name__icontains=x).to_dataframe()['name'].tolist()), axis=0)
    suggestedlist = ','.join(contains_list)
    return suggestedlist

def link_pss_to_gene(df_pps):
    a = []
    prevgene=''
    prevscreen=''
    # Interate through the df_pps by making a tuple from it (that speeds things up a bit, although its a small always a good thing to do)
    for row in df_pps.itertuples():
        if (row[2]==prevgene):
            prevscreen=prevscreen + ", " + row[1]
            # If case this is the first row and prevgene and prevscreen are still empty
        elif (prevscreen==''):
            prevscreen=row[1]
            prevgene=row[2]
        else:
            a.append([prevgene, prevscreen])
            prevscreen=row[1]
            prevgene=row[2]
    # Because we're looking backwards before printing, we miss the last line, so lets append that to the list a as well.
    a.append([prevgene, prevscreen])
    # And build a dataframe from it
    df = pd.DataFrame(a)
    return df

def convert_geneids_to_genenames(geneids_array):
    qs_gene = get_qs_genes()
    genes_array = qs_gene.filter(id__in=geneids_array).to_dataframe()['name'].tolist()
    return genes_array

def gene_array_from_trackids(trackids):
    # Check if we received a valid list of track ids
    if ((len(trackids)<1)):
        empty_array = []
        return empty_array
    else:
        qs_customtracks = get_qs_customtracks()
        # Unlike the create_genes_array function, there is no check for the genenames. 
        # --> It is assumed that custom_gene_lists only contain valid genenames because this is checked when uploading a track
        # --> If multiple tracks are selected, multiple times the same genes can occur in the array, hence we remove duplicates using set list(set())
        cstring = ''
        for i in trackids:
            cstring = ' '.join([cstring, qs_customtracks.filter(id=i).to_dataframe()['genelist'].values[0]])
        genes_list = cstring.split()
        genes_list = list(set(genes_list))
        genes_array = np.array(genes_list)
        return genes_array # This is an array of gene-names

def create_gene_plot_url(relgenestring, authorized_screens):
    gene_list = relgenestring.split()
    screenids = authorized_qs_screen(authorized_screens).filter(screentype='IP').to_dataframe()['id'].values.tolist()
    screen_part_url = ''
    for i in screenids:
        curr_scr = 'screens='+str(i)+'&'
        screen_part_url = ''.join([screen_part_url, curr_scr])
    genes = '+'.join(relgenestring.split())
    url = '../opengenefinder/?'+screen_part_url+'genes='+genes+'&pgh=on&oca=gc&pvalue=&pvaluepss=&cb=cbpv&textsize=11px'
    return url

##########################################################
# 2. Functions specific for positive selections screens  #
##########################################################

# 2.1: A function to create a dataframe for displaying positive selection screens
# Used by: ppsbubbleplot (to draw the bubble plot) and ppstophits (to list the significant hits in a table)
def generate_df_ppss(screenid, pvcutoff, sepbool, authorized_screens):
    # Grab the properties of the selected screen from the database according to screenid
    df_gene = create_df_gene()
    qs_datapoint = authorized_qs_PSSDatapoint(authorized_screens)
    df_datapoint = qs_datapoint.filter(relscreen_id=screenid).to_dataframe()
    df_datapoint['logfcpv'] = -1*np.log10(df_datapoint['fcpv'])

    # To support dynamic scaling of the datapoints, determine how many insertions are in the largest circle, and scale the other datapoints accordingly
    df_datapoint['dotsize'] = df_datapoint['radius']*2

    # Add an extra column containing the genennames depening on cutoff, needed for displaying all significant genes at once
    df_datapoint['signame'] = np.where(df_datapoint['fcpv']<pvcutoff, df_datapoint['relgene'], "")
    
    # And two extra columns holding the xy values for the datalabels
    # These guys are a 45deg angle top right + 10px of the outline of the bubble
    # df_datapoint['dotsize']/2 = radius of bubble
    # df_datapoint['txval'] = df_datapoint['seq']+((np.sqrt((((df_datapoint['dotsize']/2)**2)/2))+10)*10)
    # This step is computationally rather intensive :-()
    df_datapoint['txval'] = df_datapoint['seq'] + ((np.sqrt((((df_datapoint['radius'])**2)/2)))*(len(df_datapoint.index)/bubbleplotheight)+1)
    df_datapoint['tyval'] = df_datapoint['logfcpv'] + ((np.sqrt((((df_datapoint['radius'])**2)/2)))*375/bubbleplotheight+1)
    
    # Color options
    if sepbool == True:
        # Color all significant hits according to the globalvar colorspace
        df_datapoint['cid'] = df_datapoint['seq']%100
        df_datapoint['color'] = np.where(df_datapoint['fcpv']<pvcutoff, df_colorspace.color[df_datapoint['cid']], pss_color_ns)
    else:
        # Color all significant datapoints with a fixed color (pss_color_s) defined in globalvars
        df_datapoint['color'] = np.where(df_datapoint['fcpv']<pvcutoff, pss_color_s, pss_color_ns)
    
    df = pd.merge(df_gene, df_datapoint, left_on='name', right_on='relgene')
    # Rename the columns reflecting the x and y values to xval and y val to be able to re-use code
    df.rename(columns={'seq': 'xval', 'logfcpv': 'yval'}, inplace=True)
    return df

# 2.2: A tiny wee little function to generate a table from all significant hits in the dataframe
# As this file is actually all about data manipulation and the generate_ps_tophits is more about displaying data, is should be moved at some point to another file dedicated to displaying data
def generate_ps_tophits_list(df):
    df_top = df[(df['signame'] != "")]
    data = df_top[['relgene','fcpv','nm']].sort('fcpv').to_html(index=False)
    return data





#############################################################
# 3. Functions specific for intracellular phenotype screens #
#############################################################

# 3.1 The basic function to build the dataframe to draw a fishtail plot for a single screen
def generate_df_pips(screenid, pvcutoff, authorized_screens):

    # Query the datapoints from the database
    qs_datapoint=authorized_qs_IPSDatapoint(authorized_screens).filter(relscreen_id=screenid).only('relgene', 'fcpv', 'mi', 'insertions')
    df_datapoint=qs_datapoint.to_dataframe() # Get all datapoints that match screenid from the QuerySet and create a Dataframe
    df_gene = create_df_gene()

    # Create a new column in the dataframe datapoint that functions as the colorlabel, depending on the cutoff p-value 
    df_datapoint['color'] = np.where(df_datapoint['fcpv']<=pvcutoff, np.where(df_datapoint['mi']<1, color_sb, color_st), color_ns)
    df_datapoint['linecolor'] = df_datapoint['color']

    # Convert raw data into 10log values
    df_datapoint['loginsertions'] = np.log10(df_datapoint['insertions'])
    df_datapoint['logmi'] = np.log2(df_datapoint['mi'])
    # Create an extra column in the dataframe that 
    df_datapoint['signame'] = np.where(df_datapoint['fcpv']<=pvcutoff, df_datapoint['relgene'], "")
    # Merge the dataframe holding all genes and datapoints, as the gene-descriptions in the genes tables is not yet filled, this has no function yet.... except for slowing down everything
    df = pd.merge(df_gene, df_datapoint, left_on='name', right_on='relgene')
    return df

# 3.2 An add-on module for dataframes designated to draw fishtail-plots that links the fixed screens to the positive selection screens
# It accepts a dataframe and, for each significant genes, it looks up in the table of positive selection screens whether it has ever been a hit in those screens and subsequently changes the color.
# To determine whether a hit is signicant, is uses the 'color' value that was previously determined in either generate_df_pips or generate_df_pips_uniquefinder. By using the color instead of the given p-value cutoff this functions can also be used by the uniquefinder
def mod_df_linecolor_for_pss(df, ppscutoff, authorized_screens):
    qs_pps = authorized_qs_PSSDatapoint(authorized_screens)
    # This is a bit of a compount query: 
    # First it queries the PPS table in such a way that it only select those rows that meet 2 criteria:
    #   1. Match only genes in the IPS dataframe that were not colored with the global color for non-signifcant genes
    #   2. Matches a cutoff for when a positive selection hit is considered significant (ppscutoff)
    # From those rows it creates a dataframe that only holds the columns relscreen and relgene and subsequently sorts the dataframe on genename (relgene)
    df_pps = qs_pps.filter(Q(relgene__name__in=df[df['color'] != color_ns]['relgene'].values.tolist()) & Q( fcpv__lte=ppscutoff)).to_dataframe()[['relscreen','relgene']].sort('relgene')
    # Create an empty list that we will use to concate the screennames in which a certain gene was found as a significant hit in a positive selection screen
    df_pps_conc = link_pss_to_gene(df_pps)
    # (Re)name the columns of the table
    df_pps_conc = df_pps_conc.rename(columns={0: 'relgene', 1: 'adddescription'}) #adddescription = addition description
    # Merge with the orginal dataframe
    df_merged=pd.merge(df, df_pps_conc, left_on='relgene', right_on='relgene', how='left')
    # Get rid of NaN values intoduced by the merge
    df_merged = df_merged.fillna('')
    # And change the linecolor column values according to whether there's a addition description added (which only is the case of it was a hit)
    df_merged['linecolor'] = np.where(df_merged['adddescription']!='', pss_highlight_color, df_merged['color'])
    return df_merged

def color_fishtail_by_track(df, customgenelistid, user, pvcutoff):
    qs_track = get_qs_customtracks()
    df_track = qs_track.filter(Q(user__username=publicuser) | Q(user__username=user)).filter(id__in=customgenelistid).to_dataframe()
    # Assign a color to a track is such a way that the same trackid always has the same color. The risk is that one might plot two tracks that end up having the same color.
    # What should have priority?
    df_track['colorid'] = df_track['id']%df_custom_track_colors.shape[0]
    df_colored_track = pd.merge(df_track, df_custom_track_colors, left_on='colorid', right_on='id',  how='left')
    df_colored_genes = pd.DataFrame({'relgene': [], 'color': []})
    for row in df_colored_track.itertuples():
        gene_list = row[5].split()
        df_colored_genes_in_current_track = pd.DataFrame({'relgene': gene_list})
        df_colored_genes_in_current_track['color'] = row[8]
        df_colored_genes = pd.concat([df_colored_genes, df_colored_genes_in_current_track])
    
    # In case multiple tracks are selected, the same gene may occur in multiple tracks.
    # It is desirable that those genes are colored in such way that one can see they do belong to both track
    # This is accomplished in the following way:
    # Using df.duplicated we create a series where only the first occurence of duplicate genes is labeled keep=True
    # These values we use to create a dataframe that only exists of single entries of genes that occur more than one and assign them the color exception_color
    # Secondly we from the dataframe with possible dupliate genes we remove all genes that occur more than once using drop_duplicates (keep=False)
    # We then merge the dataframe that has only the duplicate genes with the dataframe were all genes that occur more than oce are removed
    # The final output from these steps is df_colored_genes_unique[['relgene', 'color']]
    boolean_list_duplicates_to_keep  = df_colored_genes.duplicated(subset='relgene')
    gene_df_nonunique_tmp = pd.concat([df_colored_genes, boolean_list_duplicates_to_keep], axis=1)
    gene_df_nonunique = gene_df_nonunique_tmp.loc[gene_df_nonunique_tmp[0]==True]
    gene_df_nonunique['color'] = exception_color
    gene_df_unique = df_colored_genes.drop_duplicates(subset='relgene', keep=False)
    df_colored_genes_unique = pd.concat([gene_df_nonunique[['relgene', 'color']], gene_df_unique])

    # The dataframe (df) that is received from views already has a color and linecolor, let's get rid of that first
    input_df = df[['relgene', 'relscreen', 'fcpv', 'logmi', 'loginsertions', 'mi', 'insertions']]
    output_df = pd.merge(input_df, df_colored_genes_unique, how='left', on='relgene')
    output_df = output_df.fillna('')
    output_df['color'] = np.where(output_df['color']=='', np.where(output_df['fcpv']<=pvcutoff, color_sig_non_colored, color_ns), output_df['color'])
    output_df['linecolor'] = output_df['color']
    output_df['signame'] = np.where(output_df['color']!=color_ns, np.where(output_df['color']!=color_sig_non_colored, output_df['relgene'], ""), "")

    # To make life a little easier, let's add a legend to indicate what color matches the tracks
    legend = df_colored_track[['name', 'color']]
    if (legend.shape[0] > 1):
        legend = legend.append([{'name': 'In multiple tracks', 'color': exception_color}])
    return output_df, legend

# 3.3: A tiny wee little function to generate a table from all significant hits in the dataframe
# As this file is actually all about data manipulation and the generate_ps_tophits is more about displaying data, is should be moved at some point to another file dedicated to displaying data
def generate_ips_tophits_list(df):
    df_top = df[(df['signame'] != "")]
    if (not df_top.empty):  # We need this because if someone plots a track of which none of the genes is present in the screen it will crash
        data = df_top[['relgene','fcpv', 'insertions', 'mi', 'adddescription']].sort('fcpv').to_html(index=False)
    else:
        data = ""
    return data

# 3.4: Function to generate the title for a compound fishtail 
def title_ips_uniquefinder(screenid, against_list, comparison, authorized_screens):
    qs_screen = authorized_qs_screen(authorized_screens)
    df_screenname = qs_screen.filter(id=screenid).to_dataframe()
    primaryscreen = df_screenname.get_value(0, 'name')
    against_array = np.asarray(against_list)
    against_name = ""
    if len(against_array)>1: # If A is compared against multiple screens concatenate their names
        against_name = '%s other screens' % (str(len(against_array)))
    else:
        against_name = str(qs_screen.filter(id__in=against_array).to_dataframe()['name'].values.tolist()[0])
    # Format the title according to the choosen comparison
    if (comparison=='unique'):
        title = 'Uniqueness of regulators in %s compared to %s' % (primaryscreen, against_name)
    elif (comparison=='coloroverlay'):
        title = 'Plot of %s, genes coloured according to %s' % (primaryscreen, against_name)
    elif (comparison=='mi-arrows'):
        title = 'Plot of %s, MI-shifts compared to %s' % (primaryscreen, against_name)
    return title

# 3.5: The function to generate the dataframe for the uniquefinder function
def generate_df_pips_uniquefinder(screenid, against_list, pvcutoff, comparison, authorized_screens):
    # QuerySet for the IPSDatapoint model
    qs_datapoint = authorized_qs_IPSDatapoint(authorized_screens)
    df_arrow = pd.DataFrame()
    legend = pd.DataFrame()

    if (comparison=='unique'):
    # 1. We create three dataframes for the primary screen
    # 1.2. holds all negative regulators (top hits, where fcpv <= pvcutoff and mi>1)
    # 1.2. holds all non-significant hits (fcpv >= 0.05)
    # 1.3. holds all positive regultaors (bottom hits, where fcpv <= pvcutoff and mi<1)
    ### nb. these rules do not cover the situation where mi=1 and pv <= 0.05 but when mi=1 the pv will never be <= 0.05 and therefore it is not a problem
    ### The reason that it is done like this is that it makes it very easy and uncluttered to separate the positive and negative hits, there is no need to compare colors
    # 2. Then from dataframe 1 and 3 we extract the genes. These genes, in combination with the againstscreenlist are then used to query the IPSData for all significant hits with a MI > 1 > MI and drop entries with duplicate genename
    # 4. An extra column is added to these dataframes to prepare for a merge with df_1 and df_2 (if the dataframe only exists of a genename and we merge on genename there's nothing left). The extra columns is called unique and holds the boolean False
    # 5. The dataframes are 'left' merged on genename 
    # 6. Create the color column based if False then grey, else do the standard coloring based on mi and fcpv
      
        # Get the coordinates for the fishtailplot by querying all datapoints for the input screen    
        coordinates = qs_datapoint.filter(relscreen_id=screenid).to_dataframe(['relgene','mi','fcpv','insertions'])

        # Extract the positive and negative regulators from this dataframe
        posreg = coordinates[(coordinates.mi < 1) & (coordinates.fcpv <= pvcutoff)]['relgene'].tolist()
        negreg = coordinates[(coordinates.mi >= 1) & (coordinates.fcpv <= pvcutoff)]['relgene'].tolist()

        # Use these lists to specifically query the database for these genes in the screens to compare against
        # Also add the input_screen (screen_id) to against lis because it saves some steps in the calculations later on
        against_list.append(screenid)
        posreg_query = list(qs_datapoint.filter(relscreen_id__in=against_list, mi__lt=1, fcpv__lte=pvcutoff, relgene__name__in=posreg).values_list('relgene__name', flat=True))
        negreg_query = list(qs_datapoint.filter(relscreen_id__in=against_list, mi__gte=1, fcpv__lte=pvcutoff, relgene__name__in=negreg).values_list('relgene__name', flat=True))

        # Merge both lists together, count the number of occurences in each list 
        reg_query = []
        reg_query.extend(posreg_query)
        reg_query.extend(negreg_query)
        reg_counts = pd.Series(dict(Counter(reg_query)),name='regoccurences')

        # Merge the pd.Series to the coordinates dataframe and fill na
        coordinates = coordinates.join(reg_counts, how='left', on='relgene')
        coordinates = coordinates.fillna(0) # The non-significant hits
        colorpalette = PiYG10[::-1]

        size_palette = len(colorpalette)
        # Roots root of the number of screens (for which gene x is a regulator) to create a better seperation for smaller n (screens) than for a high n
        rts = []
        for i in range(1, len(against_list)+1):
            rts.append(i**(1/float(1000))-1)
        # Normalize square roots for different numbers of screens to compare, yield a values between 1 and lenth of colorpallette
        optnormrts = []
        minval = min(rts)
        maxval = max(rts)
        currentrange = maxval-minval
        for i in rts:
            tmp = (int(math.ceil(((i-minval)*len(colorpalette))/currentrange)))
            if tmp==0:
                tmp=1
            tmp = tmp-1
            optnormrts.append(tmp)
        colors = []
        colorsdict = {}
        for i in optnormrts:
            colors.append(colorpalette[i])
        for i in range(0,len(colors)):
            colorsdict[i+1] = colors[i]
        color_screen_scores = pd.Series(colorsdict, name='color')
        coordinates = coordinates.join(color_screen_scores, how='left', on='regoccurences')

        # Finally some administation for plotting
        coordinates['logmi'] = np.log2(coordinates['mi'])
        coordinates['loginsertions'] = np.log10(coordinates['insertions'])
        coordinates = coordinates.fillna(color_ns)
        df = coordinates[['relgene', 'fcpv', 'loginsertions', 'mi', 'logmi', 'color', 'insertions', 'regoccurences']]

        # And a legend to make interpretation of the colors a bit easier
        legend_columns = ['name', 'color']
        legend = pd.DataFrame(columns=legend_columns)
        pv = colorsdict.itervalues().next()
        mincolorsdict = min(colorsdict.iteritems(), key=operator.itemgetter(0))[0]
        maxcolorsdict = max(colorsdict.iteritems(), key=operator.itemgetter(0))[0]
        for i in colorsdict:
            if colorsdict[i]!=pv:
                legend = legend.append([{'name': 'in <= %s other screens' % (i-1-mincolorsdict), 'color':pv}])
                pv = colorsdict[i]
        legend = legend.append([{'name': 'in <= %s other screens' % (maxcolorsdict-1), 'color': pv}])




    elif (comparison=='coloroverlay'):
    # The way the database is queried is different if the color-overlay mode is enabled.
    # In the color-overlay mode we query the primary screen and the secondary screen. 
    # 1. Calculate the log-mi and log-insertions for the primary screen
    # 2. Calculate the color of the secondary screen based on fcpv and mi.
    # 3. Subset the dataframe of the secondary screen to only contain the genename of the gene and the color
    # 4. Merge the dataframe of the primary screen and the genename/color subset of the secondy screen (left merge on primary screen)
    # 5. There is a chance that not all genes that were a hit in the primary screen were also a hit in the secondary screen and subsequently a small number of cells in the color column may are filled with NaN. Fillna to fill these with the non-significant color.
        df_pri_scr = qs_datapoint.filter(relscreen_id=screenid).to_dataframe()
        df_sec_scr = qs_datapoint.filter(relscreen_id__in=against_list).to_dataframe()  # This can only be a single screen, but it's is still parsed in an array
        df_pri_scr['logmi'] = np.log2(df_pri_scr['mi'])
        df_pri_scr['loginsertions'] = np.log10(df_pri_scr['insertions'])
        df_sec_scr['color'] = np.where(df_sec_scr['fcpv']<pvcutoff, np.where(df_sec_scr['mi']<1, color_sb, color_st), color_ns)
        df_sec_scr_subset = df_sec_scr[['relgene', 'color']]
        df = pd.merge(df_pri_scr, df_sec_scr_subset, on='relgene', how='left')
        df = df.fillna(color_ns)

    elif (comparison=='mi-arrows'):
        df = generate_df_pips(screenid, pvcutoff, authorized_screens)
        df, df_arrow = generate_arrows_for_uniquefinder(df, against_list, pvcutoff, authorized_screens)

    # The columns signame is used to selectively give gene-labels to those genes that are colored with a significant color
    df['signame'] = np.where(df['color']!=color_ns, df['relgene'], "")

    
    return df, df_arrow, legend

# 3.6: A function to draw arrows of the uniquefinder function

def generate_arrows_for_uniquefinder(df, against_list, pvcutoff, authorized_screens):
    qs_datapoint = authorized_qs_IPSDatapoint(authorized_screens)
    # In views it is already checked if only a single screen is passed so no need to do that now
    df_sec_scr = qs_datapoint.filter(relscreen_id__in=against_list).to_dataframe()
    ####################################################################################
    # The following part (till the next hashes) is a bit experimental so it might needs to be removed again
    ####################################################################################
    # This part is a means to correct for differences in the number of insertions and sensitiviy. A large discrepancy in the number of insertions causes very skewed lines, which, by itself is not that bad but it also results in altered MI values. 
    # These differences in the range of MI scores can seriously screw up this analysis.
    # First find the average of the number of insertions in both screens, then calcuate the ration and correct the number of insertions in the secondary screen with that ratio
    df_ins_mean = df['insertions'].mean(axis=0)
    df_sec_scr_ins_mean = df_sec_scr['insertions'].mean(axis=0)
    ins_mean_correction = df_ins_mean/df_sec_scr_ins_mean
    df_sec_scr['insertions_corrected'] = df_sec_scr['insertions'] * ins_mean_correction

    # And do the same with the MI-values (pmi/nmi = positive/negative mutational index value). We do this individually to correct for differences in the two channels
    df_pmi_mean = df.loc[df['mi']>1]['mi'].mean(axis=0)
    df_nmi_mean = df.loc[df['mi']<1]['mi'].mean(axis=0)
    df_sec_scr_pmi_mean = df_sec_scr.loc[df_sec_scr['mi']>1]['mi'].mean(axis=0)
    df_sec_scr_nmi_mean = df_sec_scr.loc[df_sec_scr['mi']<1]['mi'].mean(axis=0)
    pmi_mean_correction = df_pmi_mean/df_sec_scr_pmi_mean
    nmi_mean_correction = df_nmi_mean/df_sec_scr_nmi_mean
    df_sec_scr['mi_corrected'] = np.where(df_sec_scr['mi']>1, df_sec_scr['mi']*pmi_mean_correction, np.where(df_sec_scr['mi']<1, df_sec_scr['mi']*nmi_mean_correction, df_sec_scr['mi']))

    df_sec_scr['logmi_corrected'] = np.log2(df_sec_scr['mi_corrected'])
    df_sec_scr['loginsertions_corrected'] = np.log10(df_sec_scr['insertions_corrected'])
    ###################################################################################

    df_sec_scr['logmi'] = np.log2(df_sec_scr['mi'])
    df_sec_scr['loginsertions'] = np.log10(df_sec_scr['insertions'])
    #df_sec_scr['logmi'] = df_sec_scr['logmi_corrected']
    #df_sec_scr['loginsertions'] = df_sec_scr['loginsertions_corrected']

    df_merge = pd.merge(df, df_sec_scr, left_on='name', right_on='relgene', how='left')
    df_merge = df_merge.fillna(1)   # 1 because we are woking with the logmi values
    df_merge['absdiff_logmi_corrected'] = np.where(df_merge['fcpv_x']<=pvcutoff, np.abs(np.subtract(df_merge['logmi_x'], df_merge['logmi_corrected'])), np.where(df_merge['fcpv_y']<=pvcutoff, np.abs(np.subtract(df_merge['logmi_x'], df_merge['logmi_corrected'])), 0))
    df_merge = df_merge.sort_values(by='absdiff_logmi_corrected', ascending=0)
    # The dataframe has 40+ columns, we only need 5 so get rid of the rest, speeds up things a lot
    df_merge_compacted = df_merge.loc[(df_merge['absdiff_logmi_corrected']>=minimal_logmi_difference) & (df_merge['insertions_corrected']>=50) & (df_merge['insertions_x']>=50)][['logmi_x', 'logmi_y', 'loginsertions_x', 'loginsertions_y', 'relgene_x', 'absdiff_logmi_corrected']]
    # Now let's add some coloring to the lines.
    # There are a couple of considerations:
    # The length of the arrow indicates the size of the shift, to better let stand out the importance, the color of hits that have become more important should be more intense. Directionality should be indicated by color because genes that are 
    # significant in the WIRT screen but suddenly are not important any more in the KO screen are equally interesting as hits that suddently became important. The coloring should not interfere too much with the color of the gene-dots.
    # The color pallettes that are used for colore the hits that become less and more signicant are as follows
    # unique_finder_arrow_less_sign
    # unique_finder_arrow_more_sign
    # Start by determining the length of the pallettes, they must be of equal shape!
    len_pal = unique_finder_arrow_less_sign.shape[0] # len_pal = length pallete
    diff_max = df_merge_compacted.max()['absdiff_logmi_corrected']
    scalingfactor = (diff_max-minimal_logmi_difference)/(len_pal-1) # The 'amount' if diff_mi-points where the color shifts to the next color in the dataframe
    df_merge_compacted['linecolor'] = np.where(np.abs(df_merge_compacted['logmi_x'])<=np.abs(df_merge_compacted['logmi_y']), unique_finder_arrow_less_sign[np.round((df_merge_compacted['absdiff_logmi_corrected']-minimal_logmi_difference)/scalingfactor)], unique_finder_arrow_more_sign[np.round((df_merge_compacted['absdiff_logmi_corrected']-minimal_logmi_difference)/scalingfactor)])
    df_merge_compacted_to_df = df_merge_compacted[['relgene_x', 'linecolor']]
    df_merge_compacted_to_df = df_merge_compacted_to_df.rename(columns={'relgene_x': 'relgene', 'linecolor': 'linecolor'})
    df.drop('color', axis=1, inplace=True)
    df.drop('linecolor', axis=1, inplace=True)
    df = pd.merge(df, df_merge_compacted_to_df, how='left', on='relgene')
    df = df.fillna('#FFFFFF')
    df['linecolor'] = np.where(df['linecolor']!='#FFFFFF', df['linecolor'], np.where(df['fcpv']<=pvcutoff, color_sig_non_colored, color_ns))
    df['color'] = df['linecolor']
    df_merge = pd.merge(df, df_merge_compacted)
    df_arrow = df_merge_compacted
    #df_arrow['x-coordinates'] = np.array([df_arrow['logmi_x'], df_arrow['logmi_y']])
    #df_arrow['y-coordinates'] = np.array([df_arrow['loginsertions_x'], df_arrow['loginsertions_y']])
    return df, df_arrow

# 3.7: The Fixed Screen Summary Function
def BuildFixedScreenSummary(screenid, authorized_screens, user):

    # Set some default values for both fishtail plots
    pvcutoff = pvdc # Set pvcutoff to default value in globalvars
    oca = "gp" # Set On Click Action to GenePlot (gp)
    textsize = '10px' # Set textsize to standard textsuce according to globalvars
    # Because in the summary we only take fixed screens into consideration, extract only the IP screens from this list
    authorized_screens = list(authorized_qs_screen(authorized_screens).filter(screentype='IP').order_by('name').distinct().values_list('id',flat=True))

    # Start by creating a normal fishtail plot with all significant hits labeled and default click behaviour to a geneplot.
    sag = 'on'
    fishtail_title = title_single_screen_plot(screenid, authorized_screens)
    fishtail_df = generate_df_pips(screenid, pvcutoff, authorized_screens)
    fishtail_plot = pfishtailplot(fishtail_title, fishtail_df, sag, oca, textsize, authorized_screens, toolbar_location='right', customtools='limited_set', setwidth=500, setheight=350)

    # And create a uniquefinder plot to put next to the original fishtail
    sag = 'off'
    comparison = "unique" # Set the method for the uniquefinder to unique (see forms.py)
    uniquefinder_title = title_ips_uniquefinder(screenid, authorized_screens, comparison, authorized_screens)
    uniquefinder_df, uniquefinder_df_arrow, uniquefinder_legend = generate_df_pips_uniquefinder(screenid, authorized_screens, pvcutoff, comparison, authorized_screens)
    uniquefinder_df['adddescription'] = ''
    uniquefinder_df['linecolor'] = uniquefinder_df['color']
    uniquefinder_plot = pfishtailplot(uniquefinder_title, uniquefinder_df, sag, oca, textsize, authorized_screens, toolbar_location='right', setwidth=500, setheight=350)

    # Create additional fishtail plots for all custom tracks that are listed in the custom_variables table, currently these are all squeezed into a single row
    list_custom_list_plots = []
    customlist_ids = list(get_qs_custom_variables().distinct().values_list('custom_track_list_for_summary',flat=True))
    plotable_lists = get_qs_customtracks(onlypublic=True).filter(id__in=customlist_ids).to_dataframe() # A little check to see if the custom_list_ids in custom_variables are flagged as public, only those we plot, and put all info in a df
    for row in plotable_lists.iterrows():
        plot_title = row[1][2]
        plot_df, plot_legend = color_fishtail_by_track(fishtail_df, [row[1][0]], user, pvcutoff)
        plot = pfishtailplot(plot_title, plot_df, sag, oca, textsize, authorized_screens, toolbar_location='right', customtools='limited_set', setwidth=500, setheight=350)
        list_custom_list_plots.append(plot)

    # Create a list of 10 geneplots
    uniquefinder_df['abslogmi'] = np.abs(uniquefinder_df['logmi']) # Create an extra column in the previously generated df for uniquefinder to sort on abs(logmi) value
    genes_array = [str(i) for i in uniquefinder_df[(uniquefinder_df.abslogmi > 2) & (uniquefinder_df.fcpv < 0.01)].sort_values(by=['regoccurences', 'abslogmi'], ascending = [True, False],kind = 'mergesort')[:10]['relgene'].tolist()] # Extract the top 10 unique genes
    genes_df = pd.DataFrame({'relgene': pd.Series(genes_array), 'adddescription': pd.Series(['' for i in range(0, len(genes_array))])}).sort_values(by=['relgene'])
    geneplots = plots.single_gene_plots(genes_df, authorized_screens, pvcutoff, authorized_screens, gv.small_geneplot_width)
    print(uniquefinder_df[(uniquefinder_df.abslogmi > 1.5) & (uniquefinder_df.fcpv < 0.01)].sort_values(by=['regoccurences', 'abslogmi'], ascending = [True, False], kind = 'mergesort')[:10])

    summary = plots.create_plot_screen_summary(fishtail_plot, uniquefinder_plot, list_custom_list_plots, geneplots)
    return (summary)


def BuildFixedScreenSeqSummary(screenid, authorized_screens):
    # The following functions are for the sequence reads statistics
    qs_summary = get_qs_summary(authorized_screens)
    df_summary = create_df_summary(qs_summary)
    # A scatter plot for the total raw reads in both channels
    # Reshape the dataframe a bit so we get a column with screennames, a colomn with reads and colomn with a color representing low and high
    low_totalreads = df_summary[['relscreen', 'low_totalreads']].rename(index=str, columns={"low_totalreads": "yval"})
    low_totalreads['color'] = gv.color_low_rr
    high_totalreads = df_summary[['relscreen', 'high_totalreads']].rename(index=str, columns={"high_totalreads": "yval"})
    high_totalreads['color'] = gv.color_high_rr
    totalreads_df = pd.concat([low_totalreads, high_totalreads])
    totalreads_legend = pd.DataFrame([['total reads low', gv.color_low_rr],['total reads high', gv.color_high_rr]], columns=['name', 'color'])
    x_range = sorted(str(i) for i in totalreads_df['relscreen'].unique())
    totalreads_plot = plots.cross_screen_scatter(totalreads_df, gv.title_raw_reads_graph, gv.small_geneplot_width, x_range, totalreads_legend)

    # Generate the data for a scatter plot for the unique and mapped reads in both channels
    # Reshape the dataframe a bit so we get a column with screennames, a colomn with reads and colomn with a color representing low and high
    low_uniquereads = df_summary[['relscreen', 'low_totaluniquereads']].rename(index=str, columns={"low_totaluniquereads": "yval"})
    low_uniquereads['color'] = gv.color_low_ur
    high_uniquereads = df_summary[['relscreen', 'high_totaluniquereads']].rename(index=str, columns={"high_totaluniquereads": "yval"})
    high_uniquereads['color'] = gv.color_high_ur
    low_uniquemappedreads = df_summary[['relscreen', 'low_totalmappedreads']].rename(index=str, columns={"low_totalmappedreads": "yval"})
    low_uniquemappedreads['color'] = gv.color_low_mr
    high_uniquemappedreads = df_summary[['relscreen', 'high_totalmappedreads']].rename(index=str, columns={"high_totalmappedreads": "yval"})
    high_uniquemappedreads['color'] = gv.color_high_mr
    uniquereads_df = pd.concat([low_uniquereads, high_uniquereads, low_uniquemappedreads, high_uniquemappedreads])
    uniquereads_legend = pd.DataFrame([['Library complexity [LOW]', gv.color_low_ur], ['Library complexity [HIGH]', gv.color_high_ur],['Mapped reads [LOW]', gv.color_low_mr], ['Mapped reads [HIGH]', gv.color_high_mr]],columns=['name', 'color'])
    uniquereads_plot = plots.cross_screen_scatter(uniquereads_df, gv.title_unique_reads_graph, gv.small_geneplot_width, x_range, uniquereads_legend)

    # Generate the data for a bar plot for the total raw reads in both channels
    df_summary['uniquemappedratio_low'] = df_summary['low_totalmappedreads']/df_summary['low_totaluniquereads']*100
    df_summary['uniquetotalratio_low'] = df_summary['low_totaluniquereads']/df_summary['low_totalreads']*100
    df_summary['uniquemappedratio_high'] = df_summary['high_totalmappedreads']/df_summary['high_totaluniquereads']*100
    df_summary['uniquetotalratio_high'] = df_summary['high_totaluniquereads']/df_summary['high_totalreads']*100
    df_ratio_uniquemapped_low = df_summary[['relscreen', 'uniquemappedratio_low']].rename(index=str, columns={"uniquemappedratio_low": "yval"})
    df_ratio_uniquemapped_low['statistic'] = '% unique reads mapped to ref. genome [LOW]'
    df_ratio_uniquetotal_low = df_summary[['relscreen', 'uniquetotalratio_low']].rename(index=str, columns={"uniquetotalratio_low": "yval"})
    df_ratio_uniquetotal_low['statistic'] = 'Relative Library complexity [LOW]'
    df_ratio_uniquemapped_high = df_summary[['relscreen', 'uniquemappedratio_high']].rename(index=str, columns={"uniquemappedratio_high": "yval"})
    df_ratio_uniquemapped_high['statistic'] = '% unique reads mapped to ref. genome [HIGH]'
    df_ratio_uniquetotal_high = df_summary[['relscreen', 'uniquetotalratio_high']].rename(index=str, columns={"uniquetotalratio_high": "yval"})
    df_ratio_uniquetotal_high['statistic'] = 'Relative library complexity [HIGH]'
    df_ratio = pd.concat([df_ratio_uniquemapped_low, df_ratio_uniquetotal_low, df_ratio_uniquemapped_high, df_ratio_uniquetotal_high])
    print(df_ratio)
    ratio_plot = plots.barplot(df_ratio)



    #table_data = ast.literal_eval(df_summary[df_summary['relscreen'] == 'p-ERK']['high_topreads_counts'].values[0])
    #tableplot = plots.create_table_plot(table_data)

    # Glue the Bokeh plotting objects create above together using the function create_plot_screen_summary in plots.py
    summary = plots.create_plot_screen_seq_summary(totalreads_plot, uniquereads_plot, ratio_plot)

    return(summary)

#############################################################
# 4. Functions specific for GenePlots                       #
#############################################################

# This function is once called from single_gene_plots to create a single dataframe containing all genes
def df_multiple_geneplot(genes, screenids_array, pvcutoff, authorized_screens):
    qs_datapoint=authorized_qs_IPSDatapoint(authorized_screens)
    df = qs_datapoint.filter(relgene__name__in=genes, relscreen_id__in=screenids_array).to_dataframe()[['relgene', 'relscreen', 'mi', 'fcpv']]
    df['logmi'] = np.log2(df['mi'])
    df['color'] = np.where(df['fcpv']<=pvcutoff, np.where(df['mi']<1, color_sb, color_st), color_ns)
    return df

# This function is only called once when drawing many separate geneplots, it converts the array of genenames into a dataframe that also holds information whether this gene is a hit in the positive selection screens
def mod_df_geneplot_with_pss(genes_array, pvcutoffpss, authorized_screens):
    # This is a bit of a compount query: 
    # First it queries the PPS table in such a way that it only select those rows that meet 2 criteria:
    #   1. Match only in the given list
    #   2. Matches a cutoff for when a positive selection hit is considered significant (pvcutoffpss)
    # From those rows it creates a dataframe that only holds the columns relscreen and relgene and subsequently sorts the dataframe on genename (relgene)
    df_pps = authorized_qs_PSSDatapoint(authorized_screens).filter(Q(relgene__name__in=genes_array) & Q( fcpv__lte=pvcutoffpss)).to_dataframe()[['relscreen','relgene']].sort('relgene')
    df_annotation = link_pss_to_gene(df_pps) # This dataframe only includes the genes that were found as significant hits in the positive selection screen, and not all genes in genes_array
    df_annotation = df_annotation.rename(columns={0: 'relgene', 1: 'relscreen'})
    df_genes = pd.DataFrame(genes_array)
    df_genes = df_genes.rename(columns={0: 'relgene'})
    df = pd.merge(df_genes, df_annotation, on='relgene', how='left')
    # Get rid of NaN values intoduced by the merge
    df = df.fillna('')
    df['adddescription'] = np.where(df['relscreen']!='', (" ( hit in "+df['relscreen']+" )"), (" (not a hit in positive selection screens)"))
    return df[['relgene', 'adddescription']]

# And this creates the dataframe for the fishtail-view of the geneplot
def df_compound_geneplot(genes_df, screenids_array, colorby, pvcutoff, authorized_screens, customgenelistids, user):
    qs_datapoint=authorized_qs_IPSDatapoint(authorized_screens)   
    df=qs_datapoint.filter(relgene__name__in=genes_df['relgene'].tolist(), relscreen_id__in=screenids_array).to_dataframe()[['relscreen', 'relgene', 'fcpv', 'mi', 'insertions']]

    # Convert raw data into log values   
    df['loginsertions'] = np.log10(df['insertions'])
    df['logmi'] = np.log2(df['mi'])
    
    # Here the coloring of the datapoints happens, either by p-value, screen or track
    if colorby=="cbpv": # color by p-value
        # Create a new column in the dataframe datapoint that functions as the colorlabel, depending on the cutoff p-value 
        df['color'] = np.where(df['fcpv']<pvcutoff, np.where(df['mi']<1, color_sb, color_st), color_ns)
        legend = standard_legend
    elif colorby=='cbsc': # colorby=="cbsc" or colorby="track"
        qs_screen = authorized_qs_screen(authorized_screens)
        # Create a new colom in the dataframe datapoint that functions as the colorlabel, depending on the screennumber
        df_colors = df_colorspace
        df_screen = qs_screen.filter(id__in=screenids_array).to_dataframe()[['id', 'name']]
        df_screen['cid'] = df_colors['id']%100
        df_screen_colors_full_merge = pd.merge(df_screen, df_colors, right_on='id', left_on='cid', how='left')
        df_colors_tmp_merge = pd.merge(df_screen_colors_full_merge, df, left_on='name', right_on='relscreen', how='right')
        df = pd.DataFrame() # Emtpty the dataframe
        df = df_colors_tmp_merge
        legend = df_colors_tmp_merge[['name', 'color']]
    elif colorby=='track':
        df, legend = color_fishtail_by_track(df, customgenelistids, user, pvcutoff)

    df['linecolor'] = df['color']
    # Fill the additional info/ custom info box when hovering over a datapoint with the screenname
    df['adddescription'] = df['relscreen']
    return df, legend

def create_title_for_compound_genefinder(given_genes_array, customgenelistids, authorized_screens):
    genenamesstring = ', '.join(given_genes_array)
    title = ''
    if (customgenelistids!=''):
        for track in customgenelistids:
            title = title + get_qs_customtracks().filter(id=track).to_dataframe()['name'].values[0] + " and "
    if (genenamesstring!=''):
        title = title + genenamesstring
    return title

def calc_geneplot_width(plot_width, screens):
    if plot_width == 'dynamic':
        width = screens*dynamic_geneplot_width+100
    elif plot_width == 'small':
        width = small_geneplot_width
    elif plot_width == 'normal':
        width = normal_geneplot_width
    elif plot_width == 'wide':
        width = wide_geneplot_width
    else:
        width = normal_geneplot_width
    return width


##########################################################
# 5. Data acquisition for lists (genes, screens and tracks) #
##########################################################
def list_screens(type, authorized_screens):
    qs = authorized_qs_screen(authorized_screens).filter(screentype=type).order_by('name')
    df = qs.to_dataframe()
    df = df[['name', 'description', 'longdescription', 'induced', 'knockout', 'celline', 'screen_date']]
    data = df.to_html(index=False)
    return data

def list_tracks(currentuser):
    qs = get_qs_customtracks().filter(Q(user__username=publicuser) | Q(user__username=currentuser)).order_by('name')
    df = qs.to_dataframe()[['user', 'name', 'description', 'genelist']]
    df['number of genes'] = len(df['genelist'].values[0].split())
    data = df.to_html(index=False)
    return data

def list_genes():
    df = create_df_gene()
    data = df.to_html(index=False)
    return data

##########################################################
# 6. Form validators #
##########################################################

def validate_track_genelist(genenamesstring):
    validated_array, value = create_genes_array(genenamesstring, True)
    if value != '':
        altlist = str(' '.join(validated_array))
        raise ValidationError(
            _('%(value)s'),
            params={'value': value},
        )

def validate_track_name(trackname):
    qs = get_qs_customtracks()
    df = qs.filter(name=trackname).to_dataframe()
    value = df.shape[0]
    # If queinging the CustomTracks by the given name yield a row then it means that the name is already present in the datafrane
    if value > 0:
        raise ValidationError(
            _('Given name for your custom track already present in database. You or someone else already used this name.'),
            params={'value': value},
        )

# This is not an offical form validator but it is used as such
def validate_delete_track(customgenelistids, user):
    qs = get_qs_customtracks()
    df = qs.filter(user=user).filter(id__in=customgenelistids).to_dataframe()
    if (df.shape[0]!=len(customgenelistids)):
        message = delete_track_validation_error
    else:
        message = delete_track_validation_succes + df.to_html(index=False)
        qs.filter(user=user).filter(id__in=customgenelistids).delete()
    return message

def validate_uniquefinder_input(against_list, screenid, comparison, authorized_screens):
    error = ''
    if (not screenid or (comparison!='unique' and not against_list)): # Check if screenid and or against_list are missing
        error = formerror
    elif (comparison!='unique' and screenid in against_list): # Check if user is comparing a screen with itself
        error = compare_screen_against_itself_error
    elif (((comparison=='mi-arrow') or (comparison=='coloroverlay')) and (len(against_list) > 1)): # Check if in overlay-mode on a single screen is given in against_list
        error = coloroverlay_mi_error
    elif (set(map(int, against_list)).issubset(set(authorized_screens)) and int(screenid) in authorized_screens)==False: # And finally check of the user is not requesting a screen he/she isnt allowed to see
        error = request_screen_authorization_error
    return error
