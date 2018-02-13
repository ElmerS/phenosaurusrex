class FormMessages(object):
	'''
	A bunch for text variables for the SynthethicLethalForms
	'''
	no_controls_available = "No other analyses possibles because no available controls"
	binom_choice = 'Internal binomial analysis'
	compare_choice = 'Compare against controls'
	gc_choice = 'Link to Genecards'
	hah_choice = 'Label and highlight datapoint'
	gp_choice = 'Geneplot upon click'
	screen_choice_label = "Choose screen"
	control_choice_label = 'Select controls(s)'
	analysis_choices = 'Select analysis'
	binom_p_value_label = "For binomial-test"
	fisher_p_value_label = "For Fisher-exact test"
	p_value_help = '(p-values can also be written as 1E-xx)'
	fdr_correction_label = "FDR correction for Fisher Exact test"
	effect_size_label = "Cut-off"
	direction_label = "Demand identical directionality"
	custom_list_label = 'and/or select a track'
	annotated_all_sig_genes_label = "Annotate all significant hits"
	annotate_genes_label = 'Enter genename(s), space separated'

class SenseRatioGraphMessages(object):
	'''
	A bunch for text variables for the SenseRatioGraphs
	'''
	x_axis_label = "Insertions [10log]"
	y_axis_label = "Sense insertions (%)"
	hover_tooltip_p_values = 'P-Value'
	hover_tooltip_gene = 'Gene'
	hover_tooltip_custom = 'Custom info'