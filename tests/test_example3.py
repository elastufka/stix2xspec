#test 3rd example in readme
import xspec
from stix2xspec.xspec_utils import *
import sunxspex
from sunxspex import xspec_models
import os

if __name__ == "__main__" :

    os.chdir('../stix2xspec/data')
    mod_th = sunxspex.xspec_models.ThermalModel()
    xspec.AllModels.addPyMod(mod_th.model, mod_th.ParInfo, 'add')
    mod_th.print_ParInfo() # see the initial configuration of parameters

    mod_nt = sunxspex.xspec_models.ThickTargetModel()
    xspec.AllModels.addPyMod(mod_nt.model, mod_nt.ParInfo, 'add')
    mod_nt.print_ParInfo() # see the initial configuration of parameters

    xspec.AllData.clear() # get rid of any data that is still loaded from previous runs
    xspec.AllData(f"1:1 {'stx_spectrum_20220723_122031.fits'}{{1140}}") # fit the 1140th data row in the converted spectrogram file. make sure the .srm file is in the same folder as the spectrogram file.
    spectime = fits_time_to_datetime('stx_spectrum_20220723_122031.fits', idx=1140)
    plot_data(xspec, erange = [4,50],title = f'STIX spectrum at {spectime:%Y-%m-%d %H:%M:%S}').show()
    model, chisq = fit_thermal_nonthermal(xspec, thmodel = 'vth', ntmodel = 'bremsstrahlung_thick_target', lowErange = [3,10])

    show_model(model, df=True)
    fig, plotdata0 = plot_fit(xspec, model, fitrange = [3,30],erange=[2,35], plotdata_dict = True)
    fittext = annotate_plot(model, chisq=chisq, exclude_parameters = ['norm','Abundanc','Redshift'], MK=True)
    fig.update_layout(width=650, yaxis_range = [-2,3])
    fig.add_annotation(x=1.75,y=.5,text=fittext,xref='paper',yref='paper', showarrow = False)
    fig.show()
