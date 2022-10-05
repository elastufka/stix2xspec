import numpy as np
import os
from astropy.io import fits
from astropy import constants
import warnings
from datetime import datetime as dt
from datetime import timedelta as td

#from .read_elut import read_elut
from .spectrogram import Spectrogram
from .triggergram import Triggergram
from .spectrogram_utils import *
from matplotlib import pyplot as plt

def convert_spectrogram(fits_path_data, fits_path_bk = None, shift_duration = 0, energy_shift = 0, distance = 1.0,  flare_location= [0,0], elut_filename = None, replace_doubles = False, keep_short_bins = True, apply_time_shift = True, to_fits= False, use_discriminators = True, testing = False):
    """Convert STIX spectrogram for use in XSPEC (translation of stx_convert_spectrogram.pro, which coverts STIX spectrograms for use with OPSEX) """
    spec = Spectrogram(fits_path_data, shift_duration = shift_duration, replace_doubles = replace_doubles, keep_short_bins = keep_short_bins, background = False, use_discriminators = use_discriminators)
    dist_factor = 1./(spec.distance**2.) #when is this used?
    spec.apply_elut(elut_filename = elut_filename)

    if spec.counts.ndim == 2: #it's from a L4 spectrogram
        #spec.data_level = 4
        counts_spec = spec.counts
    else:
        counts_spec = np.sum(spec.counts,axis=1) #sum over detectors
    spec.correct_counts()
    
    #print(".......... BACKGROUND ........")
    #background
    spec_bk = Spectrogram(fits_path_bk, shift_duration = None, replace_doubles = replace_doubles, keep_short_bins = keep_short_bins, background = True, use_discriminators = False)
    spec_bk.control_data.energy_bin_mask = spec.control_data.energy_bin_mask
    spec_bk.pixel_mask = spec.pixel_mask
    spec_bk.detector_mask = spec.detector_mask
    spec_bk.apply_elut(elut_filename = elut_filename, n_energies = spec.n_energies)
    spec_bk.n_energies = 32
    spec_bk.correct_counts()
    
    #print(".......... BACKGROUND SUBTRACTION ........")
    #extra background corrections - stx_convert_science_data2ospex 153-190
    if not testing:
        spec_in_corr, total_error = background_subtract(spec, spec_bk, counts_spec)
    else:
        rdict = background_subtract(spec, spec_bk, counts_spec, testing = testing)
        rdict['spec'] = spec
        rdict['spec_bk'] = spec_bk
        return rdict
    
    emin = 1
    emax = 150
    new_edges = np.where(np.logical_and(spec.e_axis.edges_1 > emin, spec.e_axis.edges_1 <= emax))[0] #makes sense to be <= rather than just <
    new_energy_edges = spec.e_axis.edges_1[new_edges]
    if not np.array_equal(spec.e_axis.edges_1, new_energy_edges): #different shape or values
        new_eaxis, new_energies = new_energy_axis(spec)
        setattr(spec, "e_axis", new_eaxis) #check that this overwrites if different shape
    else:
        new_energies = list(range(spec.n_energies))
    
    spec.counts = spec_in_corr[:,new_energies]
    spec.error = total_error[:,new_energies] #for some reason this doesn't consistently overwrite
    spec.total_error = total_error[:,new_energies] #eventually get rid of redundant attributes
    spec.history += f"+background_subtracted_{fits_path_bk}"
    
    if not to_fits: #for testing
        return spec
    
    else: #write background-corrected counts to fits
        fitsfilename = f"stx_spectrum_{spec.t_axis.time_mean[0] :%Y%m%d_%H%M%S}.fits"
        #print(f"spec.e_axis {spec.e_axis.energy_mean}")
        spec.spectrum_to_fits(fitsfilename)
        return f"{os.getcwd()}/{fitsfilename}"

def bk_count_manipulations(bk_counts, duration, timedel, energy_bins, eff_ewidth, ntimes, name = 'corrected_counts_bk', error = False):
    """Adjust input counts for effective energy width and duration"""
    if error:
        #dim1 = bk_counts.shape[-1]
        bk_counts = np.sqrt(np.sum(bk_counts**2,axis = 0))
        bk_counts = np.sqrt(bk_counts**2/np.sum(timedel))
    else:
        bk_counts = np.sum(bk_counts,axis = 0)/np.sum(timedel)
    
    bk_counts = bk_counts[energy_bins]

    if bk_counts.ndim == 1:
        bk_counts = np.expand_dims(bk_counts, 1)
    bk_counts = np.outer(duration, bk_counts.T)
    
    bk_counts =  bk_counts/np.tile(eff_ewidth, ntimes).reshape(( ntimes,energy_bins.size))

    return bk_counts
        
def new_energy_axis(spec, emin = 1, emax = 150):
    """Correct energy axis if required"""
    new_edges = np.where(np.logical_and(spec.e_axis.edges_1 > emin, spec.e_axis.edges_1 <= emax))[0] #makes sense to be <= rather than just <
    new_energy_edges = spec.e_axis.edges_1[new_edges]

    out_mean, out_gmean, width, edges_1, edges_2 = edge_products(new_energy_edges)
    energy_low = edges_2[:,0]
    energy_high  = edges_2[:,1]
    low_fsw_idx = new_edges[1:]
    high_fsw_idx = new_edges[2:]-1

    e_axis_new = stx_energy_axis(num_energy = len(new_energy_edges) - 1, energy_mean = out_mean, gmean = out_gmean, width = width, low = energy_low, high = energy_high, low_fsw_idx = low_fsw_idx, high_fsw_idx = high_fsw_idx, edges_1 = edges_1, edges_2 = edges_2)

    new_energies = [i for i,e in enumerate(spec.e_axis.energy_mean) if e in e_axis_new.energy_mean]
    #print(self.e_axis.__dict__)
    #print(new_energies, len(new_energies), spec_in_corr.shape)
    #self.e_axis = e_axis_new
    #self.counts =  spec_in_corr[new_energies,:]
    #self.error = total_error[new_energies,:]
    return e_axis_new, new_energies

def background_subtract(spectrogram, spectrogram_bk, counts_spec, testing = False):
    """Perform background subtraction of spectrogram counts
    
    Inputs:
    
    spectrogram: Spectrogram
       The spectrogram of the signal that will be background subtracted
       
    spectrogram_bk: Spectrogram
       The spectrogram of the background that will be subtracted from the signal
       
    counts_spec: numpy array
        Original, uncorrected counts of input spectrogram"""
    corrected_counts = spectrogram.counts
    corrected_error = spectrogram.error
    corrected_error_bk = spectrogram_bk.error[...,0].T

    ntimes_bk, n_energies_bk, _, _ = spectrogram_bk.data['counts'].shape #check

    detectors_used = np.where(spectrogram.detector_mask == 1)[0]
    pixels_used = np.where(spectrogram.pixel_mask == 1)[0]
    n_detectors_bk = detectors_used.size
    n_pixels_bk = pixels_used.size
    ntimes = spectrogram.n_times
    energy_bins = spectrogram.e_axis.low_fsw_idx +1 #, spectrogram.e_axis.high_fsw_idx[-1]+1)
    
    corrected_counts_bk = spectrogram_bk.counts[...,0].T#[:,0] #sum over detectors. shape goes from (30,32) to (32) #np.sum(spectrogram_bk.data['counts'][0][detectors_used][:,pixels_used,:],axis=1)#counts #should already be correct shape
    spec_in_bk = np.sum(spectrogram_bk.data['counts'][0][:,pixels_used,:][:,:,detectors_used],axis=1).T #sum over pixels
    
    if spectrogram.t_axis.duration.ndim == 1:
        spectrogram.t_axis.duration = np.expand_dims(spectrogram.t_axis.duration,1)
    
    corrected_counts_bk = bk_count_manipulations(corrected_counts_bk, spectrogram.t_axis.duration, spectrogram_bk.data['timedel'], energy_bins, spectrogram.eff_ewidth, ntimes)
    spec_in_bk = bk_count_manipulations(spec_in_bk, spectrogram.t_axis.duration, spectrogram_bk.data['timedel'], energy_bins, spectrogram.eff_ewidth, ntimes, name = 'spec_in_bk')
    error_bk = bk_count_manipulations(corrected_error_bk, spectrogram.t_axis.duration, spectrogram_bk.data['timedel'], energy_bins, spectrogram.eff_ewidth, ntimes, name = 'error_bk', error = True)

    spec_in_corr = corrected_counts - corrected_counts_bk
    spec_in_uncorr = counts_spec - spec_in_bk #is this neccessary to keep or is it an OSPEX thing? would simplify input if didn't need to pass in counts_spec
    total_error = np.sqrt(corrected_error**2. + error_bk**2.)

    eff_livetime_fraction_expanded = spectrogram._get_eff_livetime_fraction()
    spectrogram.eff_livetime_fraction = eff_livetime_fraction_expanded[0]
    spec_in_corr *= eff_livetime_fraction_expanded.T
    total_error *= eff_livetime_fraction_expanded.T
    
    if testing:
        rdict = {'spec_in_corr':spec_in_corr,'spec_in_uncorr':spec_in_uncorr,'corrected_counts':corrected_counts, 'corrected_counts_bk':corrected_counts_bk, 'counts_spec':counts_spec, 'spec_in_bk':spec_in_bk,'total_error':total_error,'corrected_error':corrected_error, 'error_bk':error_bk, 'eff_lt':eff_livetime_fraction_expanded} #do this differently
        return rdict
    return spec_in_corr, total_error

