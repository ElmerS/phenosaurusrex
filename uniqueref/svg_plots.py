import pygal
from custom_functions import *

def svg_fishtail():

    df = generate_df_pips(89, 0.05, [89])
    siggenes = df[df['fcpv'] < 0.05]
    siggenespos = siggenes[siggenes['mi'] > 0]
    siggenesneg = siggenes[siggenes['mi'] <= 0]

    sigposcoord = [((i[1][22], i[1][23])) for i in siggenespos.iterrows()]
    signegcoord = [((i[1][22], i[1][23])) for i in siggenesneg.iterrows()]
    xy_chart = pygal.XY(stroke=False)
    xy_chart.add('Negative regulators', signegcoord)
    xy_chart.add('Positive regulators', sigposcoord)

    return (xy_chart)