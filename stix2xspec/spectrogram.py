import pandas as pd
import numpy as np
import os
from datetime import datetime as dt
from datetime import timedelta as td
from importlib import resources
from astropy.table import Table
from astropy.io import fits
from astropy.time import Time
import warnings
from .spectrogram_utils import *
from .livetime import *
from astropy.table import Table
from .write_spectrum2fits import *
from matplotlib import pyplot as plt

class Spectrogram:
    def __init__(self, filename, background = False, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, time_bin_filename = None, det_ind = None, pix_ind = None):
        """For L4 files, need to specify that alpha = 0"""
        self.filename = filename
        if 'spectrogram' in filename: #this isn't a sure thing but if it's from the SDC it will be in the filename
            self._alpha = 0
            self._data_level = 4
        self.background = background
        self.det_ind = det_ind
        self.pix_ind = pix_ind
        self.history = "init"
        self._from_fits(use_discriminators = use_discriminators, replace_doubles = replace_doubles, keep_short_bins = keep_short_bins, shift_duration = shift_duration, time_bin_filename = time_bin_filename)
        
    #attributes that are important to be read-only
    @property
    def data_level(self):
        return self._data_level
    
    @property
    def alpha(self):
        return self._alpha
        
    def _alpha_from_header(self, primary_header):
        processing_level = primary_header['LEVEL']
        alpha = 1 if processing_level.strip() == 'L1A' else 0
        self._alpha = alpha
        
    def _remove_short_bins(self, hstart_str, replace_doubles = False):
        counts_for_time_bin = sum(self.counts[1:10,:],1) # shape is ex. (32,)
        idx_short = np.where(counts_for_time_bin >= 1400)[0]

        # List when we have 1 second time bins, short or normal bins
        mask_long_bins = np.ones(self.n_time-1)
        
        min_time_table = pd.read_csv(f"{os.environ['STX_CONF']}/detector/min_time_index.csv")

        min_time = min_time_table.where(hstart_str < min_time_table.where(hstart_str > min_time_table[' start_date'])[' end_date']).dropna(how='all')['Mininmum time [cs]'].values[0]/10.

        if idx_short.size > 0:
            idx_double = np.where(self.duration[idx_short] == min_time)[0]
            if idx_double.size > 0:
                idx_short_plus = [idx_short, idx_short[idx_double]-1] #check
            else:
                idx_short_plus = idx_short

        if idx_double.size > 0 and replace_doubles:
            mask_long_bins[idx_short] = 0
            self.duration[idx_short[idx_double]-1] = (self.duration[max(np.where(self.duration[0:idx_short[idx_double]] > 1))] + self.duration[min(np.where(self.duration[idx_short[idx_double]:-1] > 1)) + idx_short[idx_double]])/2.
        else:
            mask_long_bins[idx_short_plus] = 0

        idx_long = np.where(mask_long_bins == 1)[0]

        self.time_bin_center = self.time_bin_center[idx_long]
        self.n_time = self.time_bin_center.size
        self.duration = self.duration[idx_long]
        self.counts = self.counts[idx_long,:]
        self.counts_err = self.counts_err[idx_long,:]
        self.triggers = self.triggers[idx_long]
        self.triggers_err = self.triggers_err[idx_long]
        
    def _get_energy_edges(self, energy, energies_used, energy_shift):
        energy_edges_2 = np.transpose([[energy.data.e_low[energies_used]], [energy.data.e_high[energies_used]]])
        _, _, _, energy_edges_1, _ = edge_products(energy_edges_2.squeeze())
        
        energy_edges_all2 = np.transpose([[energy.data.e_low], [energy.data.e_high]])
        _, _, _, energy_edges_all1, _ = edge_products(energy_edges_2.squeeze())
       
        use_energies = np.where(energy_edges_all1 == energy_edges_1)[0]

        energy_edges_used = (energy_edges_all1 + energy_shift)[use_energies]
        out_mean, out_gmean, width, edges_1, edges_2 = edge_products(energy_edges_used)
        return use_energies, out_mean, out_gmean, width, edges_1, edges_2
        
    def _get_used_indices(self):
        if self.alpha and not self.background: #pixel data - but don't use on L4 background data!
            mask_use_detectors = get_use_detectors(self.det_ind)
            mask_use_pixels = get_use_pixels(self.pix_ind)
            
            pixels_used = np.where(np.logical_and(np.sum(self.pixel_mask[0],0), mask_use_pixels))[0]
            detectors_used = np.where(np.logical_and(self.detector_mask[0], mask_use_detectors))[0]

        else: #L4
            try:
                pixels_used = np.where(self.pixel_mask[0,:] == 1)[0]
                detectors_used = np.where(self.detector_mask[0,:] == 1)[0]
            except IndexError: #pixel mask is 1-D array probably passed from data spectrogram to background one
                pixels_used = np.where(self.pixel_mask == 1)[0]
                detectors_used = np.where(self.detector_mask == 1)[0]
        return pixels_used, detectors_used
        
    def _get_eff_ewidth(self, pixels_used, detectors_used):
        energy_edges_used = np.append(self.e_axis.low_fsw_idx,self.e_axis.high_fsw_idx[-1]+1)
        gain, offset, adc, ekev_actual = read_elut(elut_filename = self.elut_filename)
        self.ekev_actual = ekev_actual #for testing
        
        ave_edge = np.mean(np.mean(np.swapaxes(ekev_actual, 0,2)[energy_edges_used][:,pixels_used][:,:,detectors_used],axis=1),axis=1)
        _, _, ewidth, _, _ = edge_products(ave_edge)
        true_ewidth = self.e_axis.width[~np.isinf(self.e_axis.width)]
        
        eff_ewidth =  true_ewidth/ewidth
        self.eff_ewidth = eff_ewidth
        
    def _from_fits(self, use_discriminators = True, replace_doubles = False, keep_short_bins = True, shift_duration = None, time_bin_filename = None):
        """Read spectrogram FITS file. Same function as stx_read_spectrogram_fits_file and stx_read_pixel_data_fits_file
        
        args:
        
        fits_path_data : str
        The path to the sci-xray-spec (or sci-spectrogram) observation file
        
        kwargs:
        
        background : bool, default = False
        Is the input file a background file or not
        
        energy_shift : optional, float, default=0.
        Shift all energies by this value in keV. Rarely needed only for cases where there is a significant shift in calibration before a new ELUT can be uploaded.
        
        alpha : bool, default=0
        Set if input file is an alpha e.g. L1A
        
        use_discriminators : bool, default=False
        an output float value

        shift_duration : None
        Shift all time bins by 1 to account for FSW time input discrepancy prior to 09-Dec-2021. N.B. WILL ONLY WORK WITH FULL TIME RESOLUTION DATA WHICH IS USUALLY NOT THE CASE FOR SPECTROGRAM DATA.
         """
        short_bins_dt = dt.strptime('2020-11-25T00:00:00',"%Y-%m-%dT%H:%M:%S")
        shift_duration_dt = dt.strptime('2021-12-09T00:00:00',"%Y-%m-%dT%H:%M:%S")
        energy_shift_low_dt = dt.strptime('2020-11-15T00:00:00',"%Y-%m-%dT%H:%M:%S")
        energy_shift_high_dt = dt.strptime('2021-12-04T00:00:00',"%Y-%m-%dT%H:%M:%S")

        distance, time_shift = get_header_corrections(self.filename)
        primary_header, control, data, energy = open_spec_fits(self.filename)
        counts_err = np.sqrt(data.data.counts_err**2 + data.data.counts)
        triggers_err = np.sqrt(data.data.triggers_err**2 + data.data.triggers)
        
        self.n_time = data.data['time'].size
        energies_used = np.where(control.data.energy_bin_mask == 1)[1]

        hstart_str, hstart_time = get_hstart_time(primary_header)
        
        if not hasattr(self, 'alpha'):
            self._alpha_from_header(primary_header)
            
        if not hasattr(self, 'data_level'): #is there a nicer way to do this
            self._data_level = [int(c) for c in primary_header['LEVEL'].strip() if c in ['1','4']][0]
            
        #trigger_zero should always be 0 as far as I know... it gets modified by mreadfits 2.26
    #    try:
    #        trigger_zero = data.header['TZERO3']
    #    except KeyError:
    #        trigger_zero = 0
    #    new_triggers = np.array(trigger_zero) + data.data.triggers # 1D array
    #    data.data.triggers[:] = new_triggers
    ##    except KeyError:
    ##        pass

        if hstart_time < shift_duration_dt:
            shift_duration = 1

        #If time range of observation is during Nov 2020 RSCW apply average energy shift by default
        self.energy_shift = 0
        if hstart_time > energy_shift_low_dt and hstart_time < energy_shift_high_dt:
            energy_shift = -1.6
            self.energy_shift = energy_shift
            warnings.warn(f"Warning: Due to the energy calibration in the selected observation time a shift of {energy_shift} keV has been applied to all science energy bins.")

        if not keep_short_bins and hstart_time < short_bins_dt:
            warnings.warn(f"Automatic short bin removal should not be attempted on observations before {short_bins_dt:%Y-%m-%d}")

        shift_step = 0
        if shift_duration is not None and hstart_time > shift_duration_dt:
            warnings.warn(f"Shift of duration with respect to time bins is no longer needed after {shift_duration_dt:%Y-%m-%d}")

        if shift_duration is not None and hstart_time < shift_duration_dt and self.n_time > 1: # Shift counts and triggers by one time step - for use in background file?
            #print("shifting forward by 1 timestep")
            shift_step = -1 #otherwise default is zero and nothing happens
            self.history += f"+time_shift_step={shift_step}"
        
        axis = -1 if self.alpha else 0 #time axis is last for pixel data but first for spectrogram data
        
        self.counts = shift_one_timestep(data.data.counts, shift_step = shift_step, axis = axis)
        self.counts_err = shift_one_timestep(counts_err, shift_step = shift_step, axis = axis)
        self.triggers = shift_one_timestep(data.data.triggers, shift_step = shift_step, axis = axis)
        self.triggers_err = shift_one_timestep(triggers_err, shift_step = shift_step, axis = axis)
        self.duration = shift_one_timestep(data.data.timedel, shift_step = -1*shift_step)
        self.time_bin_center = shift_one_timestep(data.data.time, shift_step = -1*shift_step)
        self.control_index = shift_one_timestep(data.data.control_index, shift_step = -1*shift_step)
        if not keep_short_bins:
            # Remove short time bins with low counts
            self._remove_short_bins(hstart_str, replace_doubles = replace_doubles)
            self.history += "+remove_short_bins"

        rcr = data.data.rcr # byte array
        if self.alpha: # things specific to L1A files
            try:
                rcr = control.data.rcr #need to reshape?
            except AttributeError:
                pass

        elif self.data_level == 1: # L1 files only?
            try:
                full_counts = np.zeros((self.n_time,32))
                full_counts[:, energies_used] = self.counts
                self.counts = full_counts.copy()

                full_counts_err = np.zeros((self.n_time, 32))
                full_counts[:,energies_used] = self.counts_err
                self.counts_err = full_counts_err
            except ValueError:
                pass #don't do this for L4

        if 'pixel_masks' in control.data.names:
            self.pixel_mask = control.data.pixel_masks
            self.detector_mask = control.data.detector_masks
        elif 'pixel_mask' in control.data.names:
            self.pixel_mask = control.data.pixel_mask
            self.detector_mask = control.data.detector_mask
        else:
            self.pixel_mask = data.data.pixel_masks
            self.detector_mask = data.data.detector_masks

        if self.background:
            self.pixel_mask = np.ones((1,12)) #will be changed in convert_spectrogram later
            self.detector_mask = np.ones((1,32))
            self.num_pixel_sets = data.data.num_pixel_sets
            self.num_energy_groups = data.data.num_energy_groups

        # Create time axis
        #TUNIT1 is Time unit
        if data.header['TUNIT1'].strip() == 's':
            factor = 1
        elif data.header['TUNIT1'].strip() == 'cs':
            factor = 100

        start_time = hstart_time + td(seconds = time_shift)
        t_start = [start_time + td(seconds = bc/factor - d/(2.*factor)) for bc,d in zip(self.time_bin_center, self.duration)]
        t_end = [start_time + td(seconds = bc/factor + d/(2.*factor)) for bc,d in zip(self.time_bin_center, self.duration)]
        t_mean = [start_time + td(seconds = bc/factor) for bc in self.time_bin_center]
        t_axis = stx_time_axis(time_mean = t_mean, time_start = t_start, time_end = t_end, duration = self.duration/factor)

        if (control.data.energy_bin_mask[0][0] or control.data.energy_bin_mask[0][-1]) and use_discriminators:
            control.data.energy_bin_mask[0][0] = 0
            control.data.energy_bin_mask[0][-1] = 0
            self.counts[...,0] = 0. #originally [0,:]
            self.counts[...,-1] = 0.
            self.counts_err[...,0] = 0.
            self.counts_err[...,-1] = 0.
            
        energies_used = np.where(control.data.energy_bin_mask == 1)[1]
        use_energies, out_mean, out_gmean, width, edges_1, edges_2 = self._get_energy_edges(energy, energies_used, self.energy_shift)
        
        energy_low = edges_2[:,0]
        energy_high  = edges_2[:,1]
        low_fsw_idx = use_energies[:-1]
        high_fsw_idx = use_energies[1:]-1
        e_axis = stx_energy_axis(num_energy = len(use_energies) - 1, energy_mean = out_mean, gmean = out_gmean, width = width, low = energy_low, high = energy_high, low_fsw_idx = low_fsw_idx, high_fsw_idx = high_fsw_idx, edges_1 = edges_1, edges_2 = edges_2)

        #probably don't need to keep original FITS stuff around but just in case for now
        self.primary_header = primary_header
        self.data_header = data.header
        self.data = data.data
        self.control_header = control.header
        self.control_data = control.data
        self.energy_header = energy.header
        self.energy_data = energy.data
        self.t_axis = t_axis
        self.e_axis = e_axis
        self.distance = distance
        self.time_shift = time_shift
        self.hstart_str = hstart_str
        self.request_id = control.data.request_id[0]
        
    def apply_elut(self, elut_filename = None, n_energies = None):
        """All the stuff that happens after stx_read_..._fits_file and before stx_convert_science_data2ospex. """
            
        # Find corresponding ELUT
        if not elut_filename:
            self.elut_filename = f"{os.environ['STX_CONF']}/elut/{date2elut_file(self.hstart_str)}"
        else:
            self.elut_filename = elut_filename
            
        counts_in = self.counts
        #self.counts_in = counts_in
        counts_err_in = self.counts_err
        #self.counts_err_in = counts_err_in
        dim_counts = counts_in.shape
        self.n_times = 1

        if len(dim_counts) > 1:
            self.n_times = dim_counts[0] #correct for both L1 and L4

        energy_bin_mask = self.control_data.energy_bin_mask
        energy_bins = np.where(energy_bin_mask[0] == 1)[0]
        if not n_energies:
            self.n_energies = len(energy_bins)
        else:
            self.n_energies = n_energies

        pixels_used, detectors_used = self._get_used_indices()
        
        pixel_mask_used = np.zeros(12)
        pixel_mask_used[pixels_used] = 1
        self.n_pixels = int(sum(pixel_mask_used))

        detector_mask_used = np.zeros(32)
        detector_mask_used[detectors_used] = 1
        self.n_detectors = int(sum(detector_mask_used))

        if not self.background:
            self._get_eff_ewidth(pixels_used, detectors_used)
        
            if not self.alpha: #L4
                spec_in = counts_in.T.copy()
                counts_spec =  np.transpose(spec_in[energy_bins,:] / np.repeat(self.eff_ewidth, self.n_times).reshape((self.n_energies, self.n_times)))#transpose back to make life easier
                error_in = counts_err_in.T.copy()
                counts_err = np.transpose(error_in[energy_bins,:]/ np.repeat(self.eff_ewidth, self.n_times).reshape((self.n_energies, self.n_times)))
            else: #L1
                counts_spec = counts_in[...,energy_bins]/np.reshape(np.tile(self.eff_ewidth, self.n_times*32*12),(self.n_times,32,12,self.n_energies))
                counts_err = counts_err_in[...,energy_bins]/np.reshape(np.tile(self.eff_ewidth, self.n_times*32*12),(self.n_times,32,12,self.n_energies))
        else:
            counts_spec = counts_in
            counts_err = counts_err_in
                            
        if self.alpha: #L1 and background, sum over pixels
            counts_spec = np.sum(counts_spec[:,detectors_used][:,:,pixels_used], axis = 2)
            counts_err = np.sqrt(np.sum(counts_err[:,detectors_used][:,:,pixels_used]**2, axis = 2))

        #insert the information from the telemetry file into the expected stx_fsw_sd_spectrogram structure
        self.type = "stx_spectrogram"
        self.counts = counts_spec

        #how does this differ from self.triggers? shouldn't that be sufficient?
        #change self.trigger to self.triggers...
        if not self.background:
#            self.trigger = self.data['triggers'].squeeze().T  #is squeeze strictly necessary?
#            self.trigger_err = self.data['triggers_err'].squeeze().T
            self.triggers = self.triggers.squeeze().T
            self.triggers_err = self.triggers_err.squeeze().T
        else:
            self.triggers = self.triggers.T #data['triggers'].T
            self.triggers_err = self.triggers_err.T #data['triggers_err'].T
        if self.triggers.ndim == 1: #still want the first dim to be 1
            self.triggers = np.expand_dims(self.triggers,-1)
            self.triggers_err = np.expand_dims(self.triggers_err,-1)
         
        self.pixel_mask = pixel_mask_used
        self.detector_mask = detector_mask_used
        self.rcr = self.data['rcr']
        self.error = counts_err
        self.history += f"+applied_{self.elut_filename}"
        
    def correct_counts(self):
        """Perform livetime correction of counts"""
        if self.alpha:
            self.counts = np.moveaxis(self.counts,0,2)
            self.error = np.moveaxis(self.error,0,2)
            
        if self.background:
            self.n_energies = 32
        
        self.counts_before_livetime = self.counts.copy()
        corrected_counts, corrected_error, livetime_frac = spectrogram_livetime(self, level = self.data_level) #4?
        
        if self.alpha: #move it back
            livetime_frac = np.moveaxis(livetime_frac,1,0)
            corrected_counts = np.moveaxis(corrected_counts,1,0)
            corrected_error = np.moveaxis(corrected_error,1,0)
            if not self.background: #sum over detectors
                corrected_counts = np.sum(corrected_counts, 1).T #might need to fix tests to account for this
                #self.counts_before_livetime = np.sum(self.counts_before_livetime,0).T
                corrected_error = np.sqrt(np.sum(corrected_error**2, 1)).T

        self.counts = corrected_counts
        self.error = corrected_error
        self.livetime_fraction = livetime_frac
        self.history += "+livetime_correction"
        
    def to_rate(self):
        """convert counts to count rate"""
        self._counts_to_rate()
    
    def _counts_to_rate(self):
        '''convert counts to rate for writing to FITS'''
        try:
            ltarr = np.tile(self.eff_livetime_fraction, self.n_energies).reshape((self.n_energies,self.eff_livetime_fraction.size)).T #not sure why this and the next line need to be different for reshape
        except AttributeError:
            self.eff_livetime_fraction = self._get_eff_livetime_fraction(expanded = False)
            ltarr = np.tile(self.eff_livetime_fraction, self.n_energies).reshape((self.n_energies,self.eff_livetime_fraction.size)).T
        durarr = np.tile(self.t_axis.duration, self.n_energies)
        if 'background_subtracted' in self.history:
            durarr = durarr.reshape((self.duration.size,self.n_energies))
        else: #not sure why this is different tbh
            durarr = durarr.reshape((self.n_energies,self.duration.size)).T
        rate = self.counts.squeeze()/(durarr * ltarr) #fdiv... replace denominator 0s with 1s (but there shouldn't be any zeros in duration or livetime fraction)
        try:
            rate_err = self.total_error.squeeze()/(durarr * ltarr) #fdiv... replace denominator 0s with 1s
        except AttributeError:
            #if self.counts.shape != self.error.shape:
            #    self.error = self.error.T #need to check if this is correct. so far is only true for background files
            rate_err = self.error.squeeze()/(durarr * ltarr) #no total error due to background correction
        self.rate = rate
        self.stat_err = rate_err
        self.history += "+counts_to_rate"
        
    def _get_eff_livetime_fraction(self, expanded = True):
        if self.data_level == 4:
            eff_livetime_fraction = np.sum(self.counts_before_livetime,axis=1)
        else:
            eff_livetime_fraction = np.sum(np.sum(self.counts_before_livetime,axis=0),axis=0) #sum over detector and energy
        
        eff_livetime_fraction = eff_livetime_fraction/np.sum(self.counts,axis=1)
        eff_livetime_fraction[np.isnan(eff_livetime_fraction)] = 1 #does f_div only do this for denominator values though? check

        if not expanded:
            return eff_livetime_fraction
        else:
            eff_livetime_fraction_expanded = np.tile(eff_livetime_fraction,self.n_energies).reshape((self.n_energies,self.n_times)) #unchanged for now

            return eff_livetime_fraction_expanded

    def _energy_dependent_sys_err(self):
        """Create SYS_ERR array for rate table"""
        #xspec in gneral works with energy dependent systematic errors
        sys_err  = np.zeros(self.e_axis.energy_mean.size) + 0.03
        sys_err[np.where(self.e_axis.energy_mean < 10.)] = 0.05 #below 10 keV
        sys_err[np.where(self.e_axis.energy_mean < 7.)] = 0.07 #below 7 keV
        sys_err = np.tile(sys_err, self.n_times).reshape((self.n_times,self.n_energies))
        return sys_err
        
    def _select_energy_channels(self, elow):
        """Trim converted data to match the channels in an existing srm file, since unable to generate srm files via Python at the moment """
        ll=list(self.e_axis.low)
        chan_idx = [ll.index(e) for e in ll if e in elow]
        #fix energy axis
        self.e_axis.num_energy = len(chan_idx)
        for a in ['energy_mean','gmean','low','high','edges_1','edges_2']: #,'low_fsw_idx','high_fsw_idx' #leave out for now, have to think about how to handle this
            attr = getattr(self.e_axis,a)
            setattr(self.e_axis,a,attr[chan_idx])
        
        #fix rate array etc
        self.n_energies = len(chan_idx)
        self.counts = self.counts[:,chan_idx]
        self.error = self.error[chan_idx,:]
        
    def _write_srm_from_file(self, srm_file = "stx_srm_full.fits"):
        """For now, write SRM by selecting matching energy channels from pre-generated .srm file and writing to a new file if necessary."""
        with resources.path('stix2xspec.data',srm_file) as srmfile:
            srm = fits.open(str(srmfile)) # Need to match the number of channels in here!
        self._select_energy_channels(srm[2].data.E_MIN + self.energy_shift) #have to add energy shift if necessary!
        srm_nenergies = srm[1].data.N_CHAN[0]
        if srm_nenergies != self.n_energies or self.energy_shift:
            srm_edges = np.array([[mn,mx] for mn,mx in zip(srm[2].data.E_MIN + self.energy_shift, srm[2].data.E_MAX + self.energy_shift)])
            spec_edges = np.float32(self.e_axis.edges_2)
            srm_channels = [np.where(srm_edges == e1)[0][0] for e1 in spec_edges if e1 in srm_edges]
            respfile = write_cropped_srm(srm,srm_channels, request_id = self.request_id, energy_shift = self.energy_shift)
        else:
            respfile = srm_file[srm_file.rfind('/')+1:]
        srm.close()
        print(f"Response file: {respfile}")
        self.respfile = respfile
    
    def spectrum_to_fits(self, fitsfilename, srm_file = "stx_srm_full.fits", write_srm = True):
        """Write the spectrogram to an OGIP-compatible FITS file. It can either be background-subtracted or not. Currently cannot be used to write background files."""
        
        if write_srm:
            self._write_srm_from_file()
            
        try:
            timedict = ogip_time_calcs(self)
        except AttributeError:
            self.eff_livetime_fraction = self._get_eff_livetime_fraction(expanded = False) #can't do this after backgrounds subtraction, counts will be wrong...
            timedict = ogip_time_calcs(self)

        self.exposure = timedict['exposure']
        # Make the primary header
        primary_header = make_stix_header(self,primary = True)

        # Make the rate table
        rate_names = ['RATE', 'STAT_ERR', 'CHANNEL', 'LIVETIME', 'SPEC_NUM', 'TIME', 'TIMEDEL','SYS_ERR']
        
        if not "counts_to_rate" in self.history:
            self._counts_to_rate()
        sys_err = self._energy_dependent_sys_err()
        rate_table = Table([self.rate, self.stat_err, timedict['channel'].astype('>i4'), self.eff_livetime_fraction, timedict['specnum'].astype('>i2'), Time(timedict['timecen']).mjd, timedict['timedel'].astype('>f4'),sys_err], names = rate_names)

        # Make the energy channel table
        # Update keywords that need updating
        ct_edges_2 = self.e_axis.edges_2
        energy_names = ('CHANNEL', 'E_MIN', 'E_MAX')
        energy_table = Table([timedict['channel'][0].astype('>i4'), ct_edges_2[:,0].astype('>f4'), ct_edges_2[:,1].astype('>f4')], names = energy_names)

        # Make the attenuator state table
        # Get the rcr states and the times of rcr changes from the ql_lightcurves structure
        ut_rcr = np.array(self.t_axis.time_start) #ok to write datetimes to FITS
        ## IDL          #find_changes, rcr, index, state, count=count
        change_idx = np.where(self.rcr[:-1] != self.rcr[1:])[0] # An array of indices into inarray where the value of the array changes
        change_state = self.rcr[change_idx] #and an array of the value of inarray at each change.
        change_idx = np.insert(change_idx,0,0) #insert index 0 at beginning
        change_state = np.insert(change_state,0,self.rcr[0])
        ##   ;add the rcr information to a specpar structure so it can be incuded in the spectrum FITS file
        ##   specpar = { sp_atten_state :  {time:ut_rcr[index], state:state} }
        att_names = ('SP_ATTEN_STATE$$TIME', 'SP_ATTEN_STATE$$STATE')
        att_table = Table([Time(ut_rcr[change_idx]).mjd, change_state.astype('u1')], names = att_names)

        primary_HDU = fits.PrimaryHDU(header = primary_header)
        rate_HDU = fits.BinTableHDU(data = rate_table)
        energy_HDU = fits.BinTableHDU(data = energy_table)
        att_HDU = fits.BinTableHDU(data = att_table)
        # fill out headers
        make_rate_header(rate_HDU.header, self, respfile = self.respfile) #should update in place
        make_stix_header(self,hdr = energy_HDU.header, extname='ENEBAND', respfile = self.respfile)
        make_stix_header(self, hdr = att_HDU.header, extname='STIX Spectral Object Parameters', respfile = self.respfile)
        hdul = fits.HDUList([primary_HDU, rate_HDU, energy_HDU, att_HDU])
        hdul.writeto(fitsfilename)
        print(f"Spectrogram written to {os.getcwd()}/{fitsfilename}")
    
class stx_time_axis:
    def __init__(self, time_mean = None, time_start = None, time_end = None, duration = None):
        for k,v in locals().items():
            if k != 'self':
                setattr(self,k,v)
        self.type = 'stx_time_axis'
    
    def RHESSI_format_times(self):
        """for FITS header """
        tstart = Time(self.time_start[0]).mjd
        tstop = Time(self.time_end[-1]).mjd
        timezeri = int(tstart)
        tstartf = tstart - timezeri #fraction of day #int(np.rint((tstart - timezeri)*8.64e7)) #ms since start of day
        #timezerf = 0.0
        tstopi = int(tstop)
        tstopf = tstop - tstopi
        return timezeri, tstartf, tstopi, tstopf
        
    def _to_IDL_MJD(self):
        """convert from datetimes to IDL- like MJD structure with tags MJD and TIME, for comparison. Dataframe for ease of use """
        #int(np.rint((tstart - timezeri)*8.64e7)) #ms since start of day
        return None
        
class stx_energy_axis:
    def __init__(self, num_energy = 32, energy_mean = None, gmean = None, low = None, high = None, low_fsw_idx = None, high_fsw_idx = None, edges_1 = None, edges_2 = None, width = None):
        for k,v in locals().items():
            if k != 'self':
                if v is not None:
                    setattr(self,k,v)
                else:
                    setattr(self,k,self.default_value(k))
        self.type = 'stx_energy_axis'

    def default_value(self, k):
        defaults = {'energy_mean': np.zeros(self.num_energy),
                    'gmean': np.zeros(self.num_energy),
                    'low': np.zeros(self.num_energy),
                    'high': np.zeros(self.num_energy),
                    'low_fsw_idx': list(range(self.num_energy)),
                    'high_fsw_idx': list(range(self.num_energy)),
                    'edges_1': np.zeros(self.num_energy + 1),
                    'edges_2': np.zeros((2,self.num_energy)),
                    'width': np.zeros(self.num_energy)
                   }
        return defaults[k]
