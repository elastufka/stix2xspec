import numpy as np
import pandas as pd
import os
import glob
from astropy.io import fits
from astropy.time import Time
from astropy.table import Table
from astropy import constants
import warnings
from datetime import datetime as dt
from datetime import timedelta as td


def date2elut_file(date, stx_conf = None):
    """Find the ELUT table to be applied, given the date of the observation. ELUT tables are available in STIX-CONF https://github.com/i4Ds/STIX-CONF"""
    
    if not stx_conf:
        stx_conf = os.environ['STX_CONF']
    elut_index=glob.glob(f"{stx_conf}/elut/elut_index.csv")[0]
    elut_df=pd.read_csv(elut_index)
    elut_df[' end_date'].replace('none',dt.now().strftime("%Y-%m-%dT%H:%M:%S"),inplace=True)
    elut_df['start_date'] = pd.to_datetime(elut_df[' start_date'])
    elut_df['end_date'] = pd.to_datetime(elut_df[' end_date'])
    #elut_df.drop(columns=[' start_date',' end_date'], inplace=True)
    if isinstance(date,str):
        date = pd.to_datetime(date)
    elut_filename = elut_df.query("@date > start_date and @date <= end_date")[' elut_file'].iloc[0]# elut filename that applies to desired date
    return elut_filename

def read_elut(elut_filename = None, scale1024 = True, ekev_actual = True):
    """ This function finds the most recent ELUT csv file, reads it, and returns the gain and offset used to make it along with the edges of the Edges in keV (Exact) and ADC 4096, rounded """
    stx_conf = os.environ['STX_CONF']
    if not elut_filename:
        elut_filename = sorted(glob.glob(f"{stx_conf}/elut/elut_table*.csv"), key=os.path.getmtime)[-1] #most recent ELUT
        elut_filename = f"{stx_conf}/elut/{elut_filename}"
        
    elut = pd.read_csv(elut_filename, header = 2)
        
    if scale1024:
        scl = 4.0
    else:
        scl = 1.0
        
    offset = (elut.Offset.values / scl).reshape((32,12))
    gain = (elut["Gain keV/ADC"].values * scl).reshape((32,12))
        
    adc4096 = np.transpose(elut.values[:,4:].T.reshape((31,32,12)), axes = (0,2,1)).T # 31 x 12 x 32 but in correct order
    science_energy_channels = pd.read_csv(f"{stx_conf}/detector/ScienceEnergyChannels_1000.csv", header = 21, skiprows = [22,23])
    ekev = pd.to_numeric(science_energy_channels['Energy Edge '][1:32]).values
    adc4096_dict = {"ELUT_FILE": elut_filename,
                "EKEV": ekev, # Science energy channel edges in keV
                "ADC4096": adc4096, # 4096 ADC channel value based on EKEV and gain/offset
                "PIX_ID": elut.Pixel.values.reshape((32,12)).T, # Pixel cell of detector, 0-11
                "DET_ID": elut.Detector.values.reshape((32,12)).T, # Detector ID 0-31
                }
    if ekev_actual:
        gain4096 = np.zeros((32,12,31))
        offset4096 = np.zeros((32,12,31))
        for i in range(31):
            gain4096[:,:,i] = gain/scl
            offset4096[:,:,i] = offset * scl
        ekev_act = (adc4096 - offset4096) * gain4096
        return gain, offset, adc4096_dict, ekev_act
    else:
        return gain, offset, adc4096_dict

def get_header_corrections(fits_path):
    """Returns distance from the Sun and time shift from primary header information"""
    primary_header =fits.open(fits_path)[0].header
    au = constants.au.value # Already in meters
    distance_sun_m = primary_header['DSUN_OBS']
    distance = distance_sun_m/au
    time_shift = primary_header['EAR_TDEL']
    return distance, time_shift
    
def open_spec_fits(filename):
    """Open a L1, L1A, or L4 FITS file and return the HDUs"""
    with fits.open(filename) as hdul:#when to close this?
        primary_header = hdul[0].header.copy()
        control = hdul[1].copy()
        data = hdul[2].copy()
        energy = hdul[3].copy() if hdul[3].name == 'ENERGIES' else hdul[4].copy()
    return primary_header, control, data, energy
    
def get_hstart_time(primary_header):
    """Return the observation start time in both string and datetime format"""
    try:
        hstart_str = primary_header['DATE_BEG']
    except KeyError:
        hstart_str = primary_header['DATE-BEG']
    hstart_time = dt.strptime(hstart_str,"%Y-%m-%dT%H:%M:%S.%f")
    return hstart_str, hstart_time
    
def get_use_detectors(det_ind = None):
    """Get a mask of detectors used in observation"""
    g10=np.array([3,20,22])-1
    g09=np.array([16,14,32])-1
    g08=np.array([21,26,4])-1
    g07=np.array([24,8,28])-1
    g06=np.array([15,27,31])-1
    g05=np.array([6,30,2])-1
    g04=np.array([25,5,23])-1
    g03=np.array([7,29,1])-1
    g02=np.array([12,19,17])-1
    g01=np.array([11,13,18])-1
    g01_10=np.concatenate([g01,g02,g03,g04,g05,g06,g07,g08,g09,g10]).tolist()
    g03_10=np.concatenate([g03,g04,g05,g06,g07,g08,g09,g10]).tolist()
    
    mask_use_detectors = np.zeros(32)
    if isinstance(det_ind, list):
        mask_use_detectors[det_ind] = 1
    else:
        mask_use_detectors[g03_10] = 1
    return mask_use_detectors
    
def get_use_pixels(pix_ind = None):
    """Get a mask of detector pixels used in observation"""
    if not pix_ind:
        return np.ones(12)
    elif isinstance(pix_ind, list):
        mask_use_pixels = np.zeros(12)
        mask_use_pixels[pix_ind] = 1
        return mask_use_pixels

def edge_products(edges):
    """Functions like https://hesperia.gsfc.nasa.gov/ssw/gen/idl/spectra/edge_products.pro . Froms a vector of contiguous channel boundaries and returns the commonly used quantities for plotting and scaling: mean, geometric mean, width, array of n+1 edges of contiguous channels, 2xn array of edges"""
    if edges.size == 1:
        return edges
    dims = edges.shape
    try:
        if dims[1] >= 2: # Already stacked... should be elow, ehigh
            edges_2 = edges
            edges_1 = edges[:,0]
            edges_1 = np.append(edges_1,edges[-1,1])
    except IndexError:
        n = dims[0]
        edges_2 = np.vstack([edges[:n-1], edges[1:]]).T
        edges_1 = edges
        
    out_mean = np.sum(edges_2, axis=1)/2.
    gmean = ((edges_2[:,0]*edges_2[:,1]))**0.5  # Geometric mean
    width = np.abs(edges_2[:,1] - edges_2[:,0]) # Width of bins
    if edges_2[0,0] == 0: #if first energy is 0
        width = width[1:]
    #width = width[~np.isinf(width)] #if there's an inf get rid of it
    return out_mean, gmean, width, edges_1, edges_2

def shift_one_timestep(arr_in, axis = 0, shift_step = -1):
    """Shift an array along a given axis a given number of steps. Primarily used to shift time axis by one step"""
    if shift_step == 0:
        return arr_in
    shifted_arr = np.copy(arr_in)
    shifted_arr = np.roll(arr_in, shift_step, axis = axis)
    if np.sign(shift_step) == -1:
        return shifted_arr[:shift_step]
    else:
        return shifted_arr[shift_step:]
    
def write_cropped_srm(srm,keep_channels,fitsfilename=None, request_id = None, energy_shift = None):
    """Write a SRM FITS file with only the channels relevant to the observation retained"""
    matrix_names = ['ENERG_LO','ENERG_HI','N_GRP','F_CHAN','N_CHAN','MATRIX']
    #print(f"original shapes: {srm[1].data.MATRIX.shape}")
    matrix = srm[1].data
    #print(len(keep_channels))
    
    #re-write primary header ENERGY_L and _H in case the energy changed
    new_nchan = np.zeros(matrix.F_CHAN.size) + len(keep_channels)
    print("NEW_NCHAN",new_nchan[0])
    new_matrix = matrix.MATRIX[:,keep_channels] #can't do this have to make new ones
    
    matrix_table = Table([matrix.ENERG_LO, matrix.ENERG_HI, matrix.N_GRP, matrix.F_CHAN, new_nchan.astype('>i4'), new_matrix.astype('>f4')], names = matrix_names)
    
    ebounds = srm[2].data
    ebounds_names = ['CHANNEL','E_MIN','E_MAX']
    new_channel = ebounds.CHANNEL[keep_channels]
    #print(new_channel)
    new_emin = ebounds.E_MIN[keep_channels]
    new_emax = ebounds.E_MAX[keep_channels]
    if energy_shift: #apply energy shift
        new_emin += energy_shift
        new_emax += energy_shift

    ebounds_table = Table([new_channel.astype('>i4'), new_emin.astype('>f4'), new_emax.astype('>f4')], names = ebounds_names)

    #see how it goes without updating the headers manually
    matrix_HDU = fits.BinTableHDU(data = matrix_table, header = srm[1].header)
    ebounds_HDU = fits.BinTableHDU(data = ebounds_table, header = srm[2].header)
    hdul = fits.HDUList([srm[0], matrix_HDU, ebounds_HDU, srm[3]])
    #print(f"final shapes: {srm[1].data.MATRIX.shape}")
    if not fitsfilename:
        fitsfilename = f"{srm[1].header['PHAFILE'][:-5]}_{len(keep_channels)}_chans.fits"
    if request_id:
        fitsfilename = f"{fitsfilename[:-5]}_{request_id}.fits"
    hdul.writeto(fitsfilename)
    return fitsfilename

