import numpy as np
from numpy.testing import assert_allclose
from astropy.io import fits
from astropy import constants
import warnings
from datetime import datetime as dt
from datetime import timedelta as td

from .read_elut import read_elut
from .spectrogram import Spectrogram
from .triggergram import Triggergram
from .spectrogram_axes import stx_time_axis, stx_energy_axis
from .spectrogram_utils import *
from .convert_spectrogram import *
from matplotlib import pyplot as plt
from ml_utils import print_arr_stats
import pidly
import os

def get_l4_testfiles():
    l4_test  ="/Users/wheatley/Documents/Solar/STIX/single_event/220430/solo_L1_stix-sci-xray-spec_20220430T144000-20220430T204502_V01_2204309235-49292.fits"
    bg_file = "/Users/wheatley/Documents/Solar/STIX/single_event/220430/solo_L1A_stix-sci-xray-l1-2204299453_20220429T202959-20220429T211459_058943_V01.fits"
    return l4_test, bg_file

def get_l1_testfiles():
    l1pix = "/Users/wheatley/Documents/Solar/STIX/single_event/220806/solo_L1A_stix-sci-xray-l1-2208046494_20220804T132609-20220804T134138_080909_V01.fits"
    bg_file = "/Users/wheatley/Documents/Solar/STIX/single_event/220806/solo_L1A_stix-sci-xray-l1-2207295463_20220729T083652-20220729T092452_079271_V01.fits"
    return l1pix, bg_file

def mean_minmax(arr):
    vals = list(arr.shape)
    vals.extend([np.mean(arr),np.min(arr),np.max(arr)])
    return vals
    
def test_config(atol = 1e-4, background = False, pixel = False, energy_shift = 0, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
    return locals()
    
def test_l4_from_fits(**kwargs):
    l4_test, _ = get_l4_testfiles()
    test_from_fits(l4_test, **kwargs)
    
def test_l1_from_fits(**kwargs):
    l1_test, _ = get_l1_testfiles()
    kwargs['pixel'] = True
    test_from_fits(l1_test, **kwargs)
    
#def test_l1a_from_fits(atol = 1e-4,energy_shift = 0, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
#    l4_test, _ = get_l4_testfiles(**kwargs)
#    test_from_fits(l4_test)
    
def test_l1bg_from_fits(**kwargs):
    _, l1bg_test = get_l1_testfiles()
    kwargs['pixel'] = True
    kwargs['background'] = True
    kwargs['use_discriminators'] = False
    test_from_fits(l1bg_test, **kwargs)
    
def test_from_fits(fitsfile, background = False, pixel=False, atol = 1e-4,energy_shift = 0, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
    spec = Spectrogram(fitsfile, background = background)
    
    ## same in IDL
    idl = pidly.IDL(os.environ['PIDLY_IDL'])
    idl("add_path, getenv('SSW_STIX'), /expand")
    idl(".compile mrdfits")
    idl("spec", fitsfile)
    idl("energy_shift", energy_shift)
    #if spec.alpha:
    #    idl("alpha", 1)
    if not use_discriminators:
        idl("use_discriminators", 0) #defalut is 1
    else:
        idl("use_discriminators", 1)
    if replace_doubles:
        idl("replace_doubles", 1)
    else:
        idl("replace_doubles",0)
    if keep_short_bins:
        idl("keep_short_bins", 1)
    else:
        idl("keep_short_bins",0)
    #idl("bkspec", bg_file)
    if not pixel:
        idl("stx_read_spectrogram_fits_file, spec, 0., primary_header = primary_header, data_str = data_str, data_header = data_header, control_str = control_str, control_header= control_header, energy_str = energy_str, energy_header = energy_header, t_axis = t_axis, energy_shift = energy_shift,  e_axis = e_axis , use_discriminators = use_discriminators, replace_doubles = replace_doubles, keep_short_bins = keep_short_bins")
    else:
        idl("stx_read_pixel_data_fits_file, spec, 0., primary_header = primary_header, data_str = data_str, data_header = data_header, control_str = control_str, control_header= control_header, energy_str = energy_str, energy_header = energy_header, t_axis = t_axis, energy_shift = energy_shift,  e_axis = e_axis , use_discriminators = use_discriminators, alpha = alpha")

    ## compare counts, triggers, and errors
    idl("counts = data_str.counts")
    idl("counts_err = data_str.counts_err")
    idl("triggers = data_str.triggers")
    idl("triggers_err = data_str.triggers_err")
    idl_counts = idl.counts
    idl_counts_err = idl.counts_err
    idl_triggers = idl.triggers
    idl_triggers_err = idl.triggers_err
    
    if background:
        assert_allclose(spec.counts[0], idl_counts, atol=atol)
        assert_allclose(spec.counts_err[0], idl_counts_err, atol=atol)
        assert_allclose(spec.triggers[0], idl_triggers, atol=atol)
        assert_allclose(spec.triggers_err[0], idl_triggers_err, atol=atol)
    else:
        assert_allclose(spec.counts, idl_counts, atol=atol)
        assert_allclose(spec.counts_err, idl_counts_err, atol=atol)
        assert_allclose(spec.triggers, idl_triggers, atol=atol)
        assert_allclose(spec.triggers_err, idl_triggers_err, atol=atol)
    
    ## compare time_bin_center and duration
    idl("time = data_str.time")
    idl("timedel = data_str.timedel")
    idl_time_bin_center = idl.time
    idl_duration = idl.timedel
    assert_allclose(spec.time_bin_center, idl_time_bin_center, atol=atol)
    assert_allclose(spec.t_axis.duration, idl_duration, atol=atol)
    
    ## compare energy axis
    idl("energy_mean = e_axis.mean")
    idl("energy_gmean = e_axis.gmean")
    idl("energy_low = e_axis.low")
    idl("energy_high = e_axis.high")
    idl("energy_width = e_axis.width")
    idl("energy_low_fsw_idx = e_axis.low_fsw_idx")
    idl("energy_high_fsw_idx = e_axis.high_fsw_idx")
    idl_energy_mean = idl.energy_mean
    idl_energy_gmean = idl.energy_gmean
    idl_energy_low = idl.energy_low
    idl_energy_high = idl.energy_high
    idl_energy_width = idl.energy_width
    idl_energy_low_fsw_idx = idl.energy_low_fsw_idx
    idl_energy_high_fsw_idx = idl.energy_high_fsw_idx
    idl.close()
    assert_allclose(spec.e_axis.energy_mean, idl_energy_mean, atol=atol)
    assert_allclose(spec.e_axis.gmean, idl_energy_gmean, atol=atol)
    assert_allclose(spec.e_axis.low, idl_energy_low, atol=atol)
    assert_allclose(spec.e_axis.high, idl_energy_high, atol=atol)
    assert_allclose(spec.e_axis.width, idl_energy_width, atol=atol)
    assert_allclose(spec.e_axis.low_fsw_idx+1, idl_energy_low_fsw_idx, atol=atol)
    assert_allclose(spec.e_axis.high_fsw_idx+1, idl_energy_high_fsw_idx, atol=atol)

    print("test passed successfully")
    
def test_l4_apply_elut(**kwargs):
    l4_test, _ = get_l4_testfiles()
    test_apply_elut(l4_test, **kwargs)
    
def test_l1_apply_elut(**kwargs):
    l1_test, _ = get_l1_testfiles()
    kwargs['pixel'] = True
    test_apply_elut(l1_test, **kwargs)

def test_l1bg_apply_elut(**kwargs):
    _, l1bg_test = get_l1_testfiles()
    kwargs['pixel'] = True
    kwargs['background'] = True
    kwargs['use_discriminators'] = False
    test_apply_elut(l1bg_test, **kwargs)
    
def test_apply_elut(fitsfile, background = False, pixel=False, atol = 1e-4,energy_shift = 0, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
    spec = Spectrogram(fitsfile, background = background)
    spec.apply_elut()

    ## same in IDL
    #os.chdir('/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/')
    idl = pidly.IDL('/Users/wheatley/Documents/Solar/sswidl_py.sh')
    idl("add_path, '/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/' + get_delim() +'stix', /expand")
    idl("setenv, 'SSW_STIX=/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/stix'")
    idl(".compile mrdfits")
    #idl("cd, '/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW'")
    idl("fits_path_data", fitsfile)
    idl("energy_shift", energy_shift)
    #if spec.alpha:
    #    idl("alpha", 1)
    if not use_discriminators:
        idl("use_discriminators", 0) #defalut is 1
    else:
        idl("use_discriminators", 1)
    if replace_doubles:
        idl("replace_doubles", 1)
    else:
        idl("replace_doubles",0)
    if keep_short_bins:
        idl("keep_short_bins", 1)
    else:
        idl("keep_short_bins",0)
    #idl("bkspec", bg_file)
    if not pixel:
        idl("stx_convert_spectrogram_test, fits_path_data=fits_path_data, fits_path_bk = fits_path_bk, time_shift=0., energy_shift = energy_shift, distance = distance, flare_location= flare_location, replace_doubles = replace_doubles, keep_short_bins = keep_short_bins, apply_time_shift = apply_time_shift, shift_duration = shift_duration, no_attenuation=no_attenuation, sys_uncert = sys_uncert, generate_fits = generate_fits, specfile = specfile, srmfile = srmfile, xspec = xspec, background_data = background_data, plot = plot, ospex_obj = ospex_obj, spectrogram = spectrogram,eff_ewidth = eff_ewidth")
    elif not background:
        idl("stx_convert_pixel_data_test, fits_path_data=fits_path_data, fits_path_bk = fits_path_bk, time_shift=0., energy_shift = energy_shift, distance = distance, flare_location= flare_location, shift_duration = shift_duration, no_attenuation=no_attenuation, sys_uncert = sys_uncert, generate_fits = generate_fits, specfile = specfile, srmfile = srmfile, xspec = xspec, background_data = background_data, plot = plot, ospex_obj = ospex_obj, spectrogram = spectrogram, eff_ewidth = eff_ewidth")
    else: #background stuff is subset of stx_convert_science_data2ospex
        idl("stx_read_pixel_data_fits_file, fits_path_data, 0., primary_header = primary_header, data_str = data_str, data_header = data_header, control_str = control_str, control_header= control_header, energy_str = energy_str, energy_header = energy_header, t_axis = t_axis, energy_shift = energy_shift,  e_axis = e_axis , use_discriminators = use_discriminators, alpha = alpha")
        idl("bk_data_level = 1")
        idl("counts_in_bk = data_str.counts")
        idl("dim_counts_bk = counts_in_bk.dim")
        idl("ntimes_bk = n_elements(dim_counts_bk) gt 3 ? dim_counts_bk[3] : 1")
        #idl("pixels_used = [0, 1, 2, 3, 4, 5, 6, 7]")
        idl("pixels_used = [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11]")
        idl("detectors_used = [ 0,  1,  2,  3,  4,  5,  6,  7, 13, 14, 15, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]")
        idl("n_pixels_bk = n_elements(pixels_used)")
        idl("n_detectors_bk = n_elements(detectors_used)")
        idl("spec_in_bk = total(reform(data_str.counts[*,pixels_used,detectors_used,*], dim_counts_bk[0], n_pixels_bk, n_detectors_bk, ntimes_bk  ),2)")
        idl("counts = reform(spec_in_bk, dim_counts_bk[0],n_detectors_bk, ntimes_bk)")
        idl("error_in_bk = sqrt(total(reform(data_str.counts_err[*,pixels_used,detectors_used,*], dim_counts_bk[0], n_pixels_bk, n_detectors_bk, ntimes_bk  )^2.,2))")
        idl("counts_err = reform(error_in_bk, dim_counts_bk[0],n_detectors_bk, ntimes_bk)")
        idl("trigger = transpose(data_str.triggers)")
        idl("trigger_err = transpose(data_str.triggers_err)")

    if not background:
        idl_eff_ewidth = idl.eff_ewidth
        assert_allclose(spec.eff_ewidth, idl_eff_ewidth, atol=atol)

    ## compare counts, triggers, and errors
    if not background:
        idl("counts = spectrogram.counts")
        idl("counts_err =  spectrogram.error")
        idl("trigger = spectrogram.trigger")
        idl("trigger_err = spectrogram.trigger_err")
    idl_counts = idl.counts
    idl_counts_err = idl.counts_err
    idl_trigger = idl.trigger
    idl_trigger_err = idl.trigger_err

    if background:
        assert_allclose(spec.counts[0], idl_counts, atol=atol)
        assert_allclose(spec.error[0], idl_counts_err, atol=atol)
        assert_allclose(spec.trigger, idl_trigger, atol=atol)
        assert_allclose(spec.trigger_err, idl_trigger_err, atol=atol)
    else:
        assert_allclose(spec.counts, idl_counts, atol=atol)
        assert_allclose(spec.error, idl_counts_err, atol=atol)
        assert_allclose(spec.trigger, idl_trigger, atol=atol)
        assert_allclose(spec.trigger_err, idl_trigger_err, atol=atol)

    idl.close()
    print("test passed successfully")
    
def test_l4_correction(**kwargs):
    l4_test, _ = get_l4_testfiles()
    test_correction(l4_test, **kwargs)
    
def test_l1_correction(**kwargs):
    l1_test, _ = get_l1_testfiles()
    kwargs['pixel'] = True
    test_correction(l1_test, **kwargs)
    
#def test_l1a_from_fits(atol = 1e-4,energy_shift = 0, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
#    l4_test, _ = get_l4_testfiles(**kwargs)
#    test_from_fits(l4_test)
    
def test_l4bg_correction(**kwargs):
    _, l4bg_test = get_l4_testfiles()
    kwargs['pixel'] = True
    kwargs['background'] = True
    kwargs['use_discriminators'] = False
    test_correction(l4bg_test, **kwargs)

def test_l1bg_correction(**kwargs):
    _, l1bg_test = get_l1_testfiles()
    kwargs['pixel'] = True
    kwargs['background'] = True
    kwargs['use_discriminators'] = False
    test_correction(l1bg_test, **kwargs)
    
def test_correction(fitsfile, background = False, pixel=False, atol = 1e-4,energy_shift = 0, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
    spec = Spectrogram(fitsfile, background = background)
    spec.apply_elut()
    if not spec.alpha:
        spec.data_level = 4
    spec.correct_counts()

    ## same in IDL
    #os.chdir('/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/')
    idl = pidly.IDL('/Users/wheatley/Documents/Solar/sswidl_py.sh')
    idl("add_path, '/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/' + get_delim() +'stix', /expand")
    idl("setenv, 'SSW_STIX=/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/stix'")
    idl(".compile mrdfits")
    #idl("cd, '/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW'")
    idl("fits_path_data", fitsfile)
    idl("energy_shift", energy_shift)
    #if spec.alpha:
    #    idl("alpha", 1)
    if not use_discriminators:
        idl("use_discriminators", 0) #defalut is 1
    else:
        idl("use_discriminators", 1)
    if replace_doubles:
        idl("replace_doubles", 1)
    else:
        idl("replace_doubles",0)
    if keep_short_bins:
        idl("keep_short_bins", 1)
    else:
        idl("keep_short_bins",0)
    #idl("bkspec", bg_file)
    if not pixel:
        idl("stx_convert_spectrogram_test, fits_path_data=fits_path_data, fits_path_bk = fits_path_bk, time_shift=0., energy_shift = energy_shift, distance = distance, flare_location= flare_location, replace_doubles = replace_doubles, keep_short_bins = keep_short_bins, apply_time_shift = apply_time_shift, shift_duration = shift_duration, no_attenuation=no_attenuation, sys_uncert = sys_uncert, generate_fits = generate_fits, specfile = specfile, srmfile = srmfile, xspec = xspec, background_data = background_data, plot = plot, ospex_obj = ospex_obj, spectrogram = spectrogram")
        idl("data_dims = spectrogram.counts.dim")
        idl("n_energies = data_dims[0]")
        idl("n_detectors = 1")
        idl("n_pixels = 1")
        idl("n_times = data_dims[1]")
        #idl("counts_spec  = spectrogram.counts")
        idl("livetime_frac =  stx_spectrogram_livetime( spectrogram, corrected_counts = corrected_counts, corrected_error = corrected_error, level = 4 )")
        #idl("corrected_counts = total(reform(corrected_counts, [n_energies, n_detectors, n_times ]),2)")
        #idl("counts_spec = total(reform(counts_spec,[n_energies, n_detectors, n_times ]),2)")
        #idl("corrected_error = sqrt(total(reform(corrected_error, [n_energies, n_detectors, n_times ])^2.,2))")
    elif not background:
        idl("stx_convert_pixel_data_test, fits_path_data=fits_path_data, fits_path_bk = fits_path_bk, time_shift=0., energy_shift = energy_shift, distance = distance, flare_location= flare_location, shift_duration = shift_duration, no_attenuation=no_attenuation, sys_uncert = sys_uncert, generate_fits = generate_fits, specfile = specfile, srmfile = srmfile, xspec = xspec, background_data = background_data, plot = plot, ospex_obj = ospex_obj, spectrogram = spectrogram, eff_ewidth = eff_ewidth")
        idl("data_dims = spectrogram.counts.dim")
        idl("n_energies = data_dims[0]")
        idl("n_detectors = data_dims[1]")
        idl("n_pixels = 1")
        idl("n_times = data_dims[2]")
        #idl("print, 'trigger before',spectrogram.trigger.dim")
        #idl("spectrogram_new = {counts:spectrogram.counts, trigger:transpose(spectrogram.trigger),trigger_err:transpose(spectrogram.trigger_err),time_axis:spectrogram.time_axis,energy_axis:spectrogram.energy_axis,error:spectrogram.error, detector_mask:spectrogram.detector_mask,pixel_mask:spectrogram.pixel_mask}")
        #idl("print, 'trigger after',spectrogram_new.trigger.dim")
        #idl("spectrogram.trigger_err = transpose(spectrogram.trigger_err)")
        #idl("counts_spec  = spectrogram.counts")
        idl("livetime_frac =  stx_spectrogram_livetime( spectrogram, corrected_counts = corrected_counts, corrected_error = corrected_error, level = 1 )") #should sum counts and error over detectors

    else: #background stuff is subset of stx_convert_science_data2ospex
        idl("stx_read_pixel_data_fits_file, fits_path_data, 0., primary_header = primary_header, data_str = data_str, data_header = data_header, control_str = control_str, control_header= control_header, energy_str = energy_str, energy_header = energy_header, t_axis = t_axis, energy_shift = energy_shift,  e_axis = e_axis , use_discriminators = use_discriminators, alpha = alpha")
        idl("bk_data_level = 1")
        idl("counts_in_bk = data_str.counts")
        idl("dim_counts_bk = counts_in_bk.dim")
        idl("ntimes_bk = n_elements(dim_counts_bk) gt 3 ? dim_counts_bk[3] : 1")
        #idl("pixels_used = [0, 1, 2, 3, 4, 5, 6, 7]")
        idl("pixels_used = [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11]")
        idl("detectors_used = [ 0,  1,  2,  3,  4,  5,  6,  7, 13, 14, 15, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]")
        idl("n_pixels_bk = n_elements(pixels_used)")
        idl("n_detectors_bk = n_elements(detectors_used)")
        idl("pixel_mask = [1,1,1,1,1,1,1,1,1,1,1,1]")
        idl("detector_mask = [1,1,1,1,1,1,1,1,0,0,0,0,0,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1]")
        idl("spec_in_bk = total(reform(data_str.counts[*,pixels_used,detectors_used,*], dim_counts_bk[0], n_pixels_bk, n_detectors_bk, ntimes_bk  ),2)")
        idl("counts = reform(spec_in_bk, dim_counts_bk[0],n_detectors_bk, ntimes_bk)")
        idl("error_in_bk = sqrt(total(reform(data_str.counts_err[*,pixels_used,detectors_used,*], dim_counts_bk[0], n_pixels_bk, n_detectors_bk, ntimes_bk  )^2.,2))")
        idl("counts_err = reform(error_in_bk, dim_counts_bk[0],n_detectors_bk, ntimes_bk)")
        idl("trigger = transpose(data_str.triggers)")
        idl("trigger_err = transpose(data_str.triggers_err)")
        idl("spectrogram_bk = {counts:spec_in_bk, trigger:trigger,trigger_err:trigger_err,time_axis:t_axis,energy_axis:e_axis,error:error_in_bk,pixel_mask:pixel_mask,detector_mask:detector_mask}")
        idl("livetime_frac =  stx_spectrogram_livetime(spectrogram_bk, corrected_counts = corrected_counts,  corrected_error = corrected_error, level = 1)")

    ## compare counts, triggers, and errors

    idl("counts = corrected_counts")
    idl("counts_err =  corrected_error")
    idl("livetime_frac = livetime_frac")
    idl_counts = idl.counts
    idl_counts_err = idl.counts_err
    idl_livetime_frac = idl.livetime_frac

    if background:
        assert_allclose(spec.livetime_fraction[...,0], idl_livetime_frac.T, atol=atol)
        assert_allclose(spec.counts[...,0], idl_counts.T, atol=atol)
        assert_allclose(spec.error[...,0], idl_counts_err.T, atol=atol)
    else:
        assert_allclose(spec.livetime_fraction, idl_livetime_frac.T, atol=atol)
        assert_allclose(spec.counts, idl_counts.T, atol=atol)
        assert_allclose(spec.error, idl_counts_err.T, atol=atol)

    idl.close()
    print("test passed successfully")

def test_l4_conversion(**kwargs):
    l4_test, bg_file = get_l4_testfiles()
    test_conversion(l4_test, bg_file, **kwargs)
    
def test_l1_conversion(**kwargs):
    l1_test, bg_file = get_l1_testfiles()
    kwargs['pixel'] = True
    test_conversion(l1_test, bg_file, **kwargs)
    
#def test_l1a_from_fits(atol = 1e-4,energy_shift = 0, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
#    l4_test, _ = get_l4_testfiles(**kwargs)
#    test_from_fits(l4_test)
    
def test_conversion(fitsfile, bgfile, atol = 1e-4,energy_shift = 0, pixel=False, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, alpha = None, time_bin_filename = None):
    rdict = convert_spectrogram(fitsfile, bgfile)
    spec = rdict['spec']
    spec_bk = rdict['spec_bk']
    ## same in IDL
    #os.chdir('/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/')
    idl = pidly.IDL('/Users/wheatley/Documents/Solar/sswidl_py.sh')
    idl("add_path, '/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/' + get_delim() +'stix', /expand")
    idl("setenv, 'SSW_STIX=/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW/stix'")
    idl(".compile mrdfits")
    #idl("cd, '/Users/wheatley/Documents/Solar/STIX/code/STIX-GSW'")
    idl("fits_path_data", fitsfile)
    idl("fits_path_bk", bgfile)
    idl("energy_shift", energy_shift)
    #if spec.alpha:
    #    idl("alpha", 1)
    if not use_discriminators:
        idl("use_discriminators", 0) #defalut is 1
    else:
        idl("use_discriminators", 1)
    if replace_doubles:
        idl("replace_doubles", 1)
    else:
        idl("replace_doubles",0)
    if keep_short_bins:
        idl("keep_short_bins", 1)
    else:
        idl("keep_short_bins",0)
    #idl("bkspec", bg_file)
    if not pixel:
        idl("stx_convert_spectrogram_full_test, fits_path_data=fits_path_data, fits_path_bk = fits_path_bk, time_shift=0., energy_shift = energy_shift, distance = distance, flare_location= flare_location, replace_doubles = replace_doubles, keep_short_bins = keep_short_bins, apply_time_shift = apply_time_shift, shift_duration = shift_duration, no_attenuation=no_attenuation, sys_uncert = sys_uncert, generate_fits = generate_fits, specfile = specfile, srmfile = srmfile, xspec = xspec, background_data = background_data, plot = plot, ospex_obj = ospex_obj, spectrogram = spectrogram, out_spec = out_spec")
    else:
        idl("stx_convert_pixel_data_full_test, fits_path_data=fits_path_data, fits_path_bk = fits_path_bk, time_shift=0., energy_shift = energy_shift, distance = distance, flare_location= flare_location, shift_duration = shift_duration, no_attenuation=no_attenuation, sys_uncert = sys_uncert, generate_fits = generate_fits, specfile = specfile, srmfile = srmfile, xspec = xspec, background_data = background_data, plot = plot, ospex_obj = ospex_obj, spectrogram = spectrogram, eff_ewidth = eff_ewidthj, out_spec = out_spec")

    ## compare counts, errors
    idl("counts = out_spec.counts")
    idl("error = out_spec.error")
    idl("corrected_counts = out_spec.corrected_counts")
    idl("corrected_error = out_spec.corrected_error")
    idl("counts_spec = out_spec.counts_spec")
    idl("eff_lt = out_spec.eff_livetime_fraction_expanded")
    idl("counts_bk = background_data.counts")
    idl("error_bk = background_data.error")
    idl("counts_in_bk = background_data.counts_in_bk")
    idl("spec_in_bk = background_data.spec_in_bk")
    idl("livetime_corrected_counts_bk = background_data.livetime_corrected_counts_bk")
    idl("livetime_corrected_err_bk = background_data.livetime_corrected_err_bk")
    idl_counts = idl.counts
    idl_error = idl.error
    idl_corrected_counts = idl.corrected_counts
    idl_corrected_error = idl.corrected_error
    idl_counts_spec = idl.counts_spec
    idl_eff_lt = idl.eff_lt
    idl_counts_bk = idl.counts_bk
    idl_error_bk = idl.error_bk
    idl_counts_in_bk = idl.counts_in_bk
    idl_spec_in_bk = idl.spec_in_bk
    idl_lt_counts = idl.livetime_corrected_counts_bk
    idl_lt_err = idl.livetime_corrected_err_bk

    assert_allclose(rdict['corrected_counts'], idl_corrected_counts, atol=atol)
    assert_allclose(rdict['corrected_error'], idl_corrected_error, atol=atol)
    assert_allclose(rdict['corrected_counts_bk'], idl_counts_bk, atol=atol)
    assert_allclose(rdict['error_bk'], idl_error_bk, atol=atol)
    #assert_allclose(rdict['spec'].counts_before_livetime, idl_counts_spec, atol=atol)
    assert_allclose(rdict['eff_lt'], idl_eff_lt.T, atol=atol)
    assert_allclose(rdict['spec_in_corr'], idl_counts, atol=atol)
    assert_allclose(rdict['total_error'], idl_error, atol=atol)
    
    ## compare energy axis
    idl("energy_mean = out_spec.energy_axis.mean")
    idl("energy_gmean = out_spec.energy_axis.gmean")
    idl("energy_low = out_spec.energy_axis.low")
    idl("energy_high = out_spec.energy_axis.high")
    idl("energy_width = out_spec.energy_axis.width")
    idl("energy_low_fsw_idx = out_spec.energy_axis.low_fsw_idx")
    idl("energy_high_fsw_idx = out_spec.energy_axis.high_fsw_idx")
    idl_energy_mean = idl.energy_mean
    idl_energy_gmean = idl.energy_gmean
    idl_energy_low = idl.energy_low
    idl_energy_high = idl.energy_high
    idl_energy_width = idl.energy_width
    idl_energy_low_fsw_idx = idl.energy_low_fsw_idx
    idl_energy_high_fsw_idx = idl.energy_high_fsw_idx
    idl.close()
    assert_allclose(spec.e_axis.energy_mean, idl_energy_mean, atol=atol)
    assert_allclose(spec.e_axis.gmean, idl_energy_gmean, atol=atol)
    assert_allclose(spec.e_axis.low, idl_energy_low, atol=atol)
    assert_allclose(spec.e_axis.high, idl_energy_high, atol=atol)
    assert_allclose(spec.e_axis.width, idl_energy_width, atol=atol)
    assert_allclose(spec.e_axis.low_fsw_idx+1, idl_energy_low_fsw_idx, atol=atol)
    assert_allclose(spec.e_axis.high_fsw_idx+1, idl_energy_high_fsw_idx, atol=atol)

    idl.close()
    print("test passed successfully")

def test_ogip_time_calcs():
    l4_test, _ = get_l4_testfiles()
    spec_l4 = Spectrogram(l4_test)
    spec_l4.apply_elut()
    timedict_l4 = ogip_time_calcs(spec_l4)
    
    print("L4 test passed successfully")
    
    l1_test, _ = get_l1_testfiles()
    spec_l1 = Spectrogram(l1_test)
    spec_l1.apply_elut()
    timedict_l1 = ogip_time_calcs(spec_l1)
    print("L1 test passed successfully")
