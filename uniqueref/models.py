from django.db import models
from django.utils import timezone
from django.utils.encoding import force_bytes
from django_pandas.managers import DataFrameManager
from django.contrib.auth.models import Group

class Screen(models.Model):			# Model for screens
	name = models.TextField()	
	scientist = models.ForeignKey('auth.User')
	description = models.TextField()
	longdescription = models.TextField()
	sequenceids = models.TextField()
	directory = models.TextField()
	groups = models.ManyToManyField(Group, through='ScreenPermissions', verbose_name="Group permissions")
	induced = models.BooleanField(
		default=False)
	knockout = models.BooleanField(
		default=False)
	celllines = (
		('HAP1', 'HAP1'),
		('KBM7', 'KBM7')
	)
	celline = models.CharField(max_length=4,
		choices=celllines,
		default='HAP1')
	screen_date = models.DateTimeField(
		blank=True, null=True)
	screentypes = (
		('PS', 'Positive Selection'	),
		('SL', 'Synthetic Lethality'),
		('IP', 'Intracellular Phenotype')
	)
	screentype = models.CharField(max_length=2, 
		choices=screentypes,
		default='IP')

  	objects = DataFrameManager()		# For django_pandas

	def __str__(self):	
		return self.name		# Return the name of screen, already str so no conversion needed

	class Meta:
		verbose_name = 'Name, descriptions and type of a screen'
 		verbose_name_plural = 'screens and their individual properties'

# A crosstable to store the association between groups (gids) and screens
class ScreenPermissions(models.Model):
	relscreen = models.ForeignKey(Screen)
	relgroup = models.ForeignKey(Group)

	objects = DataFrameManager()		# For django_pandas

	def __str__(self):	
		return force_bytes('%s' % (self.relscreen_id))		# Return the name of screen, already str so no conversion needed

class Gene(models.Model):
	name = models.CharField(max_length=400)
	description = models.TextField()
	chromosome = models.CharField(max_length=2)
	orientation = models.CharField(max_length=1)
	objects = DataFrameManager()   		# For django_pandas

	def __str__(self):				# Returns the name of a gene
		return force_bytes('%s' % (self.name))	# From char to str

	class Meta:
		verbose_name = 'Gene entry'
 		verbose_name_plural = 'the genes in the database'

class Location(models.Model):					# One gene can have multiple, non-overlapping, locations on the (same) chromosome
	relgene = models.ForeignKey(Gene)
	startpos = models.IntegerField()
	endpos = models.IntegerField()
	objects = DataFrameManager()

	def __str__(self):
		return force_bytes('%s' % (self.startpos))

	class Meta:
		verbose_name = 'Genomic location of a gene'
 		verbose_name_plural = 'genomic locations (of genes)'

class PSSDatapoint(models.Model):			# A model that holds each indiviual datapoint for positive selection screens
	relscreen = models.ForeignKey(Screen)	# The screen it is associated with
	relgene = models.ForeignKey(Gene) 	# Instead of using an MD5 hash to find the right gene, we now use the -unique- name of a gene
	nm = models.IntegerField() # NM=number of mutations in positively selected populations of HAP1 cells
	tnm = models.IntegerField() # TNM=Total number of mutations in enriched population minus mutations in associated gene
	ct = models.IntegerField()	# CT=number of mutations in non-selected control populations
	tct = models.IntegerField() # TCT=Total number of mutations in control population minus mutations in associted gene
	cct = models.IntegerField() # CCT=CT Corrected for zeros
	ctct = models.IntegerField() # TCTC=TCT Corrected (for zeros)
	pv = models.FloatField()	# P-value
	fcpv = models.FloatField()	# FDR corrected P-value
	ti = models.IntegerField()	# TI=Total Insertions (NM+CCT)
	mi = models.FloatField()	# Mutational index, doesn't say much but we do calculate it nevertheless
	radius = models.FloatField()
	seq = models.IntegerField()	# The element of the gene on the x-scale in the graph
	objects = DataFrameManager()	# Again, needed for django_pandas+

	def __str__(self):
		return force_bytes('%s' % (self.pv))	# Return name of related gene

	class Meta:
		verbose_name = 'Datapoint of a positive selection screen'
 		verbose_name_plural = 'datapoints of positive selection screens'

class SLSDatapoint(models.Model):			# Holds the information of for all datapoints of Synthetic Lethal Screens
	relscreen = models.ForeignKey(Screen)	# The screen it is associated with
	relgene = models.ForeignKey(Gene) 	# The name of the associated gene for each datapoint
	replicate = models.IntegerField() # Number of associated replicate
	sense = models.IntegerField() # Number of sense mutations (non-normalized, non-zero corrected)
	antisense = models.IntegerField() # Number of antisense mutations (non-normalized, non-zero corrected)
	sense_normalized = models.IntegerField() # Number of sense mutations (normalized, non-zero corrected)
	antisense_normalized = models.IntegerField() # Number of antisense mutations (normalized, non-zero corrected)
	senseratio = models.FloatField()	# Sense ratio (corrected sense / corrected total) (on non-normalized counts, zero-corrected counts)
	insertions = models.IntegerField()	# Total number of sense and antisense integrations (zero-corrected counts)
	binom_fdr = models.FloatField() # Bionomial test sense vs. antisense, FDR Corrected
	pv_control_1 = models.FloatField() # Fisher Exact test against control 1, non-FDR Corrected
	pv_control_2 = models.FloatField() # Fisher Exact test against control 2, non-FDR Corrected
	pv_control_3 = models.FloatField()	# Fisher Exact test against control 3, non-FDR Corrected
	pv_control_4 = models.FloatField()	# Fisher Exact test against control 4, non-FDR Corrected
	fcpv_control_1 = models.FloatField() # Fisher Exact test against control 1, FDR Corrected
	fcpv_control_2 = models.FloatField() # Fisher Exact test against control 2, FDR Corrected
	fcpv_control_3 = models.FloatField()	# Fisher Exact test against control 3, FDR Corrected
	fcpv_control_4 = models.FloatField()	# Fisher Exact test against control 4, FDR Corrected
	objects = DataFrameManager()	# Needed for Django Pandas

	def __str__(self):
		return force_bytes('%s' % (self.replicate))	# Return name of related gene

	class Meta:
		verbose_name = 'Datapoint of a Synthetic Lethal selection screen'
 		verbose_name_plural = 'datapoints of synthetic lethal screens'


class IPSDatapoint(models.Model):			# A model that holds each indiviual datapoint for intracellular phenotype screens
	relscreen = models.ForeignKey(Screen)
	relgene = models.ForeignKey(Gene)
	low = models.IntegerField()
	lowtotal = models.IntegerField()
	high = models.IntegerField()
	hightotal = models.IntegerField()
	lowcor = models.IntegerField()
	lowtotalcor = models.IntegerField()
	highcor = models.IntegerField()
	hightotalcor = models.IntegerField()
	pv = models.FloatField()
	fcpv = models.FloatField()
	mi = models.FloatField()
	insertions = models.IntegerField()
	objects = DataFrameManager()	# Again, needed for django_pandas

	def __str__(self):
		return force_bytes('%s' % (self.low))	# Return name of related gene

	class Meta:
		verbose_name = 'Datapoint of a intracellular phenotype screen'
 		verbose_name_plural = 'datapoints of intracellular phenotype screens'

class CustomTracks(models.Model):
	user = models.ForeignKey('auth.User')
	name = models.CharField(max_length=100) # Name of track, eg. genes in cholesterol synthesis
	description = models.CharField(max_length=400) # Whatever one wants to say about this track
	genelist = models.TextField() # Space sepearated list of genes
	objects = DataFrameManager() # For Django Pandas

	def __str__(self):
		return force_bytes('%s' % (self.name))	# Return name of related gene

	class Meta:
		verbose_name = 'Custom track (list of genes)'
 		verbose_name_plural = 'Custom tracks (list of genes)'

class UpdateHistory(models.Model):
	date = models.DateField(blank=False)
	version = models.CharField(max_length=10)
	changes = models.TextField()	# Textfield to list all changes for a certain version
	objects = DataFrameManager()    # Again, needed for django_pandas

        def __str__(self):
               	return self.version

        class Meta:
               	verbose_name = 'Changelog'
                verbose_name_plural = 'changelogs'

class SeqSummary(models.Model):			# A model that holds each indiviual datapoint for intracellular phenotype screens
	relscreen = models.ForeignKey(Screen)
	high_dist = models.TextField() # Looks like "[0.16416445990269316, ...,  0.058667589596514823]"
	high_readsmappedtotophits =  models.TextField() # Looks like "[29356, 882943]"
	high_topreads_counts = models.TextField() # Looks like "{' TTCCCCCCTTTTTCTGGAGACTAAATAAAATCTTTTATTTTATCGATGCG': 4851039,... }"
	high_totalmappedreads = models.IntegerField()
	high_totalreads = models.IntegerField()
	high_totaltopreads = models.IntegerField()
	high_totaluniquereads = models.IntegerField()
	low_dist = models.TextField()
	low_readsmappedtotophits = models.TextField()
	low_topreads_counts = models.TextField()
	low_totalmappedreads = models.IntegerField()
	low_totalreads = models.IntegerField()
	low_totaltopreads = models.IntegerField()
	low_totaluniquereads = models.IntegerField()
	objects = DataFrameManager()	# Again, needed for django_pandas

	def __str__(self):
		return force_bytes('%s' % (self.relscreen))	# Return name of related screen

	class Meta:
		verbose_name = 'Summary of screen sequencing results'
 		verbose_name_plural = 'summaries of screen sequencing results'

class CustomVariables(models.Model):
	custom_track_list_for_summary = models.IntegerField()
	def __str__(self):
		return force_bytes('%s' % (self.custom_track_list_for_summary))  # Return name of related screen

	class Meta:
		verbose_name = 'custom variable'
		verbose_name_plural = 'custom variables'

class Settings(models.Model):
	variable_name = models.CharField(max_length=50)
	value = models.TextField()
	comment = models.TextField()
	def __str__(self):
		return force_bytes('%s: %s' % (self.variable_name, self.value))

	class Meta:
		verbose_name = 'Manual setting entry'
		verbose_name_plural = 'Settings for Phenosaurus'