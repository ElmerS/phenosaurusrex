from ... import globalvars as gv

'''
A bunch of variables and messages for showing the forms to build synthetic lethal plots
'''

no_controls_available= 'Either no control was associated with this screen, a control was associated but not uploaded' + \
					   ' or you do not have permission to query the control'
rendering_mode_label = 'Rendering mode'
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
custom_list_label = 'and/or select one or multiple a tracks'
annotated_all_sig_genes_label = "Or, if no genes specified, label all significant genes"
annotate_genes_label = 'Enter genename(s) that you want to label in the plot, space separated'
aggregate_label = 'Aggregate control replicates'
table_label = 'List significant genes in table'

rendering_mode = (
	('default', 'Default'),
	('svg', 'SVG'),
	('opengl', 'OpenGL')
)

onclickactionchoices = (
	('gc', gc_choice),
	('hah', hah_choice),
	('gp', gp_choice)
)

renderingchoices = (
	('webgl', "WebGL"),
	('svg', "SVG")
)

default_oca = 'gc'
default_fdr = True  # Default for whether or not using FDR corrected p-values
default_effect_size = 0.2  # Minimal change in effect versus wildtype control
default_directionality_constraint = True
default_aas = True  # Annotate All Significant (genes)
default_analysis = 'compare'
aggregate = False
table = True

'''

options = {'ParameterForm':
				{'screenid': None,
				 'replicates': None,
				 'controls': None,
				 'customgenelist': None,
				 'genes': None,
				 'analysis': default_analysis,
				 'oca': default_oca,
				 'binom_p_value': gv.pvdc,
				 'fisher_p_value': gv.pvdc,
				 'fdr': default_fdr,
				 'effect_size': default_effect_size,
				 'directionality': default_directionality_constraint,
				 'aas': default_aas,
				 'aggregate' = False
				 },
			'ScreenForm':
			 	{'screenid': None
				 }
			 }
'''