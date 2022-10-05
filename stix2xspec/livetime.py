import numpy as np
import pandas as pd
#from astropy.io import fits
#from astropy import constants
import warnings
from datetime import datetime as dt
from datetime import timedelta as td
from .triggergram import Triggergram
from importlib import resources

#def pileup_corr_parameter():
#    subc = construct_subcollimator()
#    pixel_areas = subc.det.pixel.area
#    detector_area = (subc.det.area)[0]
#    big_pixel_fraction = pixel_areas[0]/detector_area
#    prob_diff_pix = (2./big_pixel_fraction - 1.)/(2./big_pixel_fraction)
#    return prob_diff_pix
        
def livetime_fraction(triggergram, det_used, adg_file = 'adg_table.json'):
    with resources.path('stix2xspec.data', adg_file) as aa:
        adg_sc = pd.read_json(aa) #should probably be in STIX-CONF
    adg_sc.drop(0, inplace= True) # drop first row
    det_select = det_used + 1#np.arange(32) + 1
    ntrig = triggergram.triggerdata.shape[0]
    tau_array = 10.1e-6 + np.zeros(ntrig) #10.1 microseconds readout time per event
    eta_array = 2.63e-6 + np.zeros(ntrig) #2.63 microseconds latency time per event
    beta = 0.940591 #pileup_corr_parameter() for now
    
    idx_select = [row.ADG_IDX for i,row in adg_sc.iterrows() if row.SC in det_select]
    # these are the agd id needed (1-16)

    # supposed to select the adg_idx of the corresponding collimator
    ix_fordet = [list(triggergram.adg_idx).index(i) for i in idx_select]
    
    ndt = len(triggergram.t_axis.duration)
    duration = np.tile(triggergram.t_axis.duration, ntrig).reshape((ntrig, ndt))
    tau_rate =  np.tile(tau_array, ndt).reshape((ndt, ntrig)).T / duration
    eta_rate =  np.tile(eta_array, ndt).reshape((ndt, ntrig)).T / duration
    nin = triggergram.triggerdata / (1. -  triggergram.triggerdata * (tau_rate + eta_rate))
    livetime_frac = np.exp( -1 * beta * eta_rate * nin) /(1. + (tau_rate + eta_rate) * nin)

    sc_idx = list(adg_sc[adg_sc.SC.isin(det_select)].reset_index().sort_values(by='SC').index.values)
    new_idx = [ix_fordet[idx] for idx in sc_idx]

    if livetime_frac.squeeze().ndim == 1:
        result = livetime_frac[new_idx]
    else:
        result = livetime_frac[new_idx,:] #should be 32xM
    
    return result
    
def spectrogram_livetime(spectrogram, level = 4):
    """currently accurate to 1e-3, which does lead to differences with IDL of up to 1 count in the test spectrum"""
    ntimes = spectrogram.n_times#counts.shape[-1]
    nenergies = spectrogram.n_energies
    det_used = np.where(spectrogram.detector_mask == 1)[0]
    ndet = det_used.size
    err_low = -1 * spectrogram.triggers_err
    err_none = np.zeros_like(spectrogram.triggers_err)
    err_high = spectrogram.triggers_err
    
    livetime_fracs = []
    for err in [err_low, err_none, err_high]:
        if level == 1:
            dim_counts = (ndet, nenergies, ntimes)
            trig = spectrogram.triggers + err
            
        elif level == 4:
            dim_counts = (nenergies,ntimes)
            trig = np.transpose((spectrogram.triggers + err) * (np.ones(16)/16.))
        
        if np.sum(np.sign(err))/err.size == -1:
            trig[trig <=0] = 0

        triggergram = Triggergram(trig, spectrogram.t_axis)
        livetime_frac = livetime_fraction(triggergram, det_used)
        if level == 4:
            livetime_frac = livetime_frac[0,:]
        livetime_frac = np.tile(livetime_frac,nenergies).reshape(dim_counts) #formerly tile by shape0
        if level == 4:
            livetime_frac = livetime_frac.T
        livetime_fracs.append(livetime_frac)
    
    if level not in [1,4]:
        warnings.warn('Currently supported compaction levels are 1 (pixel data) and 4 (spectrogram)')
    spec_counts = spectrogram.counts.copy()
    corrected_counts_lower =  spec_counts/livetime_fracs[0]
    corrected_counts =  spec_counts/livetime_fracs[1]
    corrected_counts_upper =  spec_counts/livetime_fracs[2]

    error_from_livetime = (corrected_counts_upper - corrected_counts_lower)/2.
    temp_err = spectrogram.error.copy()#np.zeros_like(spectrogram.error.T) #should probably not be zeros at this point... mention to Ewan
    if temp_err.shape != livetime_fracs[1].shape: #still neccesary?
        temp_err = spectrogram.error.T #np.zeros_like(spectrogram.error.T) for testing only!
    
    corrected_error = np.sqrt((temp_err/livetime_fracs[1])**2. + error_from_livetime**2.)

    return corrected_counts, corrected_error, livetime_fracs[1]
    
