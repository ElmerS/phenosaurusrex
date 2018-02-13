from django.contrib import admin
from import_export import resources, widgets, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from django.contrib.auth.models import Group
from models import *
import models
import logging

logger = logging.getLogger(__name__)

class ForeignKeyGeneWidget(ForeignKeyWidget):

	def get_queryset(self, value, row):
		"""
		Extension of ForeignKeyWidget.get_queryset method hat does the following:
			- Finds the entry of the associated gene in the table of genes taking the identifier (shortname) of the
			  reference genome into account
			- Checks if not only the reference is present in the database but also whether the reference has been
			  linked to the associated screen.
		:param value:
		:param row:
		:return: QuerySet
		"""
		#if row['relrefname'] in models.Screen.objects.filter(name__exact=row['relscreenname']):
		return self.model.objects.filter(relref__shortname=row['relrefname'])
		#else:
		#	return None


class IPSDatapointResource(resources.ModelResource):
	'''
	For import of new fixed screen datasets
	'''
	pass_relscreen = fields.Field(
		column_name='relscreenname',
		attribute='relscreen',
		widget=ForeignKeyWidget(models.Screen,'name'))
	pass_relgene = fields.Field(
		column_name='relgenename',
		attribute='relgene',
		widget=ForeignKeyGeneWidget(models.Gene, 'name'))

	
	class Meta:
		model = models.IPSDatapoint	# Must be put into the class Datapoint (from oldref.model)
		skip_unchanged = True	# Skip if already exists, this function doesn't work at all when a new ID is given...
		report_skipped = True	# Perhaps this better be True?
		fields = ('id',
			'pass_relscreen', # Link to correct screen
			'pass_relgene', # Link to correct gene
			'low', 
			'lowtotal', 
			'high', 
			'hightotal', 
			'insertions',
			'lowcor', 
			'lowtotalcor', 
			'highcor', 
			'hightotalcor', 
			'pv', 
			'fcpv', 
			'mi',
		)

class IPSDatapointAdmin(ImportExportModelAdmin):
	def get_relgene(self, obj):
		return obj.relgene.name

	def get_relscreen(self, obj):
		return obj.relscreen.name

	def get_relref(self, obj):
		return obj.relgene.relref.shortname

	get_relgene.short_description = 'Gene'
	get_relscreen.short_description = 'Associated Screen'
	get_relref.short_description = 'Associated ref annotation'
	resource_class = IPSDatapointResource
	list_display = ('id', 'get_relscreen', 'mi', 'fcpv', 'get_relgene', 'get_relref')
	pass





class PSSDatapointResource(resources.ModelResource):
	'''
	For import of new positive selection datasets
	'''

	pass_relscreen = fields.Field(column_name='relscreenname', attribute='relscreen', widget=ForeignKeyWidget(Screen,'name'))
	pass_relgene = fields.Field(column_name='relgenename', attribute='relgene', widget=ForeignKeyWidget(Gene,'name'))
	
	class Meta:
		model = PSSDatapoint	# Must be put into the class Datapoint (from oldref.model)
		skip_unchanged = True	# Skip if already exists
		report_skipped = True	# Perhaps this better be True?
		fields = ('id',
			  'pass_relscreen', # Link to correct screen
			  'pass_relgene', # Link to correct gene
			  'nm',
			  'tnm', 
		  	  'ct', 
			  'tct', 
			  'cct',
			  'ctct', 
			  'pv', 
			  'ti',
			  'fcpv', 
			  'mi',
			  'radius',
			  'seq',
		  )

class PSSDatapointAdmin(ImportExportModelAdmin):
	def get_relgene(self, obj):
		return obj.relgene.name
	def get_relscreen(self, obj):
		return obj.relscreen.name
	get_relgene.short_description = 'Gene'
	get_relscreen.short_description = 'Associated Screen'
	resource_class = PSSDatapointResource
	list_display = ('id', 'get_relscreen', 'fcpv', 'get_relgene')
	pass



class SLSDatapointResource(resources.ModelResource):
	'''
	For import of new synthetic lethal datasets
	'''

	pass_relscreen = fields.Field(
		column_name='relscreenname',
		attribute='relscreen',
		widget=ForeignKeyWidget(models.Screen,'name'))
	pass_relgene = fields.Field(
		column_name='relgenename',
		attribute='relgene',
		widget=ForeignKeyGeneWidget(models.Gene, 'name'))

	class Meta:
		model = SLSDatapoint  # Must be put into the class Datapoint (from oldref.model)
		skip_unchanged = True  # Skip if already exists
		report_skipped = True  # Perhaps this better be True?
		fields = ('id',
				  'pass_relscreen',  # Link to correct screen
				  'pass_relgene',  # Link to correct gene
				  'replicate',
				  'sense',
				  'antisense',
				  'sense_normalized',
				  'antisense_normalized',
				  'insertions',
				  'senseratio',
				  'binom_fdr',
				  'pv_control_1',
				  'pv_control_2',
				  'pv_control_3',
				  'pv_control_4',
				  'fcpv_control_1',
				  'fcpv_control_2',
				  'fcpv_control_3',
				  'fcpv_control_4',
				  )

class SLSDatapointAdmin(ImportExportModelAdmin):
	def get_relgene(self, obj):
		return obj.relgene.name

	def get_relscreen(self, obj):
		return obj.relscreen.name

	def get_relref(self, obj):
		return obj.relgene.relref.shortname

	get_relgene.short_description = 'Gene'
	get_relscreen.short_description = 'Associated Screen'
	get_relref.short_description = 'Associated ref annotation'
	resource_class = SLSDatapointResource
	list_display = ('get_relscreen', 'get_relgene', 'get_relref', 'replicate', 'senseratio', 'binom_fdr')
	pass




class GeneResource(resources.ModelResource):
	'''
	For import of new reference annotations
	'''
	pass_relref = fields.Field(
		column_name='relref',
		attribute='relref',
		widget=ForeignKeyWidget(ReferenceGenome, 'shortname')
	)

	class Meta:
		model = Gene
		skip_unchanged = True
		report_skipped = True
		fields = ('pass_relref', 'id', 'name', 'description', 'chromosome', 'orientation')


class GeneAdmin(ImportExportModelAdmin):
	def get_relref(self, obj):
		return obj.relref.shortname

	get_relref.short_description = 'Reference'
	list_display = ('name', 'chromosome', 'orientation', 'get_relref', 'description')
	resource_class = GeneResource
	pass


class SeqSummaryResource(resources.ModelResource):
	pass_relscreen = fields.Field(column_name='relscreenname', attribute='relscreen',
								  widget=ForeignKeyWidget(Screen, 'name'))

	class Meta:
		model = SeqSummary  # Must be put into the class Datapoint (from oldref.model)
		skip_unchanged = True  # Skip if already exists
		report_skipped = True  # Perhaps this better be True?
		fields = ('id',
				  'pass_relscreen',  # Link to correct screen
				  'high_dist',
				  'high_readsmappedtotophits',
				  'high_topreads_counts',
				  'high_totalmappedreads',
				  'high_totalreads',
				  'high_totaltopreads',
				  'high_totaluniquereads',
				  'low_dist',
				  'low_readsmappedtotophits',
				  'low_topreads_counts',
				  'low_totalmappedreads',
				  'low_totalreads',
				  'low_totaltopreads',
				  'low_totaluniquereads'
				  )




class SeqSummaryAdmin(ImportExportModelAdmin):
	def get_relscreen(self, obj):
		return obj.relscreen.name

	get_relscreen.short_description = 'Associated Screen'
	resource_class = SeqSummaryResource
	list_display = ('id', 'get_relscreen')
	pass


# Class LocationResource to define
class LocationResource(resources.ModelResource):

        pass_relgene = fields.Field(column_name='relgenename', attribute='relgene', widget=ForeignKeyWidget(Gene,'name'))

	class Meta:
		model = Location
		skip_unchanged = True
		report_skipped = True
		fields = ('id',
			  'pass_relgene',
			  'startpos',
			  'endpos',
		)

class LocationAdmin(ImportExportModelAdmin):
	def get_relgene(self, obj):
		return obj.relgene.name
	get_relgene.short_description = 'Gene'
	resource_class = LocationResource
	list_display = ('id', 'get_relgene', 'startpos', 'endpos')
	pass

class ScreenPermissionsInline(admin.TabularInline):
	model = ScreenPermissions
	extra = 3

class ScreenAdmin(admin.ModelAdmin):
	list_display = ('name', 'screentype', 'induced', 'knockout', 'description', 'celline', 'screen_date', 'list_refs_as_str', 'list_groups_as_str')

class UpdateHistoryAdmin(admin.ModelAdmin):
	list_display=('date', 'version', 'changes')

class CustomVariablesAdmin(admin.ModelAdmin):
	list_display=('custom_track_list_for_summary',)

class CustomTrackAdmin(admin.ModelAdmin):
	list_display = ('user', 'name', 'description', 'genelist')

class GroupAdmin(admin.ModelAdmin):
	inlines = (ScreenPermissionsInline,)

class SettingsAdmin(admin.ModelAdmin):
	list_display = ('variable_name', 'value', 'comment')

class ReferenceGenomeAdmin(admin.ModelAdmin):
	list_display = ('shortname', 'longname')

admin.site.register(models.ReferenceGenome, ReferenceGenomeAdmin)
admin.site.register(Screen, ScreenAdmin)	
admin.site.register(Gene, GeneAdmin)
admin.site.register(IPSDatapoint, IPSDatapointAdmin)
admin.site.register(PSSDatapoint, PSSDatapointAdmin)
admin.site.register(SLSDatapoint, SLSDatapointAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Settings, SettingsAdmin)
admin.site.register(CustomTracks, CustomTrackAdmin)
admin.site.unregister(Group) # To disable the standard form for modifying groups
admin.site.register(Group, GroupAdmin)
admin.site.register(UpdateHistory, UpdateHistoryAdmin)
admin.site.register(SeqSummary, SeqSummaryAdmin)