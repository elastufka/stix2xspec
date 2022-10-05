import pandas as pd
import os
import numpy as np
from datetime import datetime as dt
import glob
#from .spectrogram_utils import *
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time
#from .spectrogram import Spectrogram
#from .spectrogram_axes import stx_energy_axis, stx_time_axis

def make_stix_header(spec, hdr = None, primary = False, respfile=None,extname=''):
    """make the primary headers"""
    if not hdr:
        hdu = fits.PrimaryHDU()
        hdr = hdu.header
    else:
        hdr.set("COMMENT",  "*** End of mandatory fields ***", after = "TFIELDS")
        #sort columns by formats then names, put at end (to do later)
    
    if primary:
        hdr.set('PARENT', spec.filename[spec.filename.rfind('/')+1:], "Parent Observation Data File") #don't include the path
        hdr.set('DATA_LEVEL', spec.data_level, "Observation Data Compression Level")
        hdr.set('REQUEST_ID', spec.request_id, "Unique Request ID for the Observation")
        hdr.set('SUN_DISTANCE', spec.distance, "Distance in AU to Sun")
        #hdr.set('GRID_FACTOR', fits_info_params.grid_factor, "Total Grid Transmission Factor", before='AUTHOR')
        elut_filename = spec.elut_filename
        if '/' in spec.elut_filename:
            elut_filename = spec.elut_filename[spec.elut_filename.rfind('/')+1:]
        hdr.set('ELUT_FILENAME', elut_filename, "Filename of ELUT")

    hdr.set('DATE', dt.strftime(dt.now(),"%Y-%m-%dT%H:%M:%S"), 'File creation date (YYYY-MM-DDThh:mm:ss UTC)')
    hdr.set('ORIGIN', 'STIX','Spectrometer Telescope for Imaging X-rays')
    try:
        observer = os.environ['USER']
    except KeyError:
        observer = 'Unknown'
    hdr.set('OBSERVER', observer,'Usually the name of the user who generated file')
    hdr.set('TELESCOP', 'Solar Orbiter', 'Name of the Telescope or Mission')
    hdr.set('INSTRUME', 'STIX', 'Name of the instrument')
    hdr.set('OBJECT', 'Sun', 'Object being observed')

    hdr.set('TIME_UNI', 1)
    hdr.set('ENERGY_L', spec.e_axis.low[0])
    hdr.set('ENERGY_H', spec.e_axis.high[-1])

    hdr.set('TIMESYS',  '1979-01-01T00:00:00', 'Reference time in YYYY MM DD hh:mm:ss')
    hdr.set('TIMEUNIT', 'd', 'Unit for TIMEZERO, TSTARTI and TSTOPI')
    hdr.set('TIME_SHIFT', spec.time_shift, 'Applied correction for Earth-SO light travel time')
    
    hdr.set('AUTHOR','WRITE_SPECTRUM2FITS')
    
    hdr.set('RA_NOM', 0.0, 'r.a. nominal pointing in degrees')
    hdr.set('DEC_NOM',0.0,'dec. nominal pointing in degrees')
    hdr.set('EQUINOX',2000.0,'Equinox of celestial coordinate system')
    hdr.set('RADECSYS','FK5','Coordinate frame used for equinox')
    
    if not primary:
        #hdr.set('GEOAREA', ratearea) #have to get ratearea from SRM
        hdr.set('DETUSED', 1)
        hdr.set('SUMFLAG', 0, 'no sum flag')
        hdr.set('SUMCOINC', 0, 'no sum coinc')
        hdr.set('COINCIDE', 0, 'no coinc')
        if respfile:
            hdr.set('RESPFILE',respfile)
        hdr.set('EXTNAME',extname,'Extension name')
        hdr.set('COMMENT', 'absTime[i] = mjd2any(MJDREF + TIMEZERO) + TIME[i]')
    
    else:
        hdr.set('TIMVERSN','OGIP/93-003','OGIP memo number where the convention used')
        hdr.set('VERSION',1.0,'File format version number')
    
    
    #hdr.set('EXTNAME', 'STIX Spectral Object Parameters', 'Extension name')
    return hdr

def make_rate_header(rate_header,spec,respfile=None):
    """stx_rate_header.pro"""
    hdr = make_stix_header(spec, hdr=rate_header, respfile=respfile, extname='RATE')

    hdr.set('TIMEREF','LOCAL','Reference frame for the times')
    hdr.set('MJDREF',43874.0,'TIMESYS in MJD (d)')
    
    timezeri, tstartf, tstopi, tstopf = spec.t_axis.RHESSI_format_times()
    hdr.set('TIMEZERO', timezeri - hdr['MJDREF'], 'Start day of the first bin rel to TIMESYS')
    hdr.set('TSTARTI', timezeri - hdr['MJDREF'],'Integer portion of start time rel to TIMESYS') #timezeri - long(rate_struct.mjdref)
    hdr.set('TSTARTF',tstartf,'Fractional portion of start time')
    hdr.set('TSTOPI',tstopi - hdr['MJDREF'],'Integer portion of stop time rel to TIMESYS')
    hdr.set('TSTOPF',tstopf,'Fractional portion of stop time')
    hdr.set('TELAPSE',0.,'Elapsed time in seconds')
    hdr.set('TASSIGN','SATELLITE','Place of time assignment')
    hdr.set('TIERRELA',0.0,'Relative time error')
    hdr.set('TIERABSO',0.0,'Absolute time error')
    hdr.set('ONTIME', spec.exposure, 'Exposure time in seconds')
    hdr.set('TELAPSE',0.0, 'Elapsed time in seconds')
    hdr.set('CLOCKCOR', 1, 'Clock Correction to UT') #should it be 1
    hdr.set('POISSERR',0,'Poission Error') #sholud it be 0?
    
    hdr.set('VERSION',1.0,'File format version number')
    hdr.set('HDUCLASS','OGIP','File conforms to OGIP/GSFC convention')
    hdr.set('HDUCLAS1','SPECTRUM','File contains spectrum')
    hdr.set('HDUCLAS2','TOTAL','Extension contains a spectrum')
    hdr.set('HDUCALS3', 'TYPE:II ', 'Multiple PHA files contained')
    hdr.set('HDUCLAS4', 'RATE', 'Extension contains rates')
    hdr.set('HDUVERS ', 1.2,'File conforms to this version of OGIP')
    hdr.set('TIMVERSN','OGIP/93-003','OGIP memo number where the convention used')
    hdr.set('ANCRFILE','','Name of the corresponding ancillary response file') #for XSPEC
    hdr.set('AREASCAL',1.0, 'Area scaling factor')
    hdr.set('BACKFILE', '', 'Name of the corresponding background file')
    hdr.set('BACKSCAL',1.0, 'Background scaling factor')
    hdr.set('CORRFILE','','Name of the corresponding correction file')
    hdr.set('CORRSCAL',1.0, 'Correction scaling factor')
    hdr.set('EXPOSURE',spec.exposure,'Integration time, corrected for deadtime and d')
    hdr.set('GROUPING',0, 'No grouping of data has been defined')
    hdr.set('QUALITY',0, 'No quality information is specified')
    hdr.set('DETCHANS',spec.n_energies,'Total number of detector channels available')
    hdr.set('CHANTYPE','PI','Channels assigned by detector electronics')
    #VIGNET  =        0.00000000000 /
    #DETNAM  = '        '           /  Detector name
    #NPIXSOU =        0.00000000000 /
    #BACKAPP = '        '           /  Flag to indicate whether correction was applie
    #DEADAPP = '        '           /  Flag to indicate whether correction was applie
    #VIGNAPP = '        '           /  Flag to indicate whether correction was applie
    
#    rate_struct.backapp = backapp
#    rate_struct.backfile = backfile

    return hdr

def ogip_time_calcs(spec):
#    ;calculate time parameters to be passed into the fits file
#    specnum = indgen( n_elements( ut[0,*] ) ) + 1
#    channel = rebin( lindgen( nchan ), nchan, n_elements( ut[0,*] ) )
#    timedel = float( reform( ut[1,*] - ut[0,*] ) )
#    timecen = double( reform( ut[0,*] + timedel/2.0 ) )
#    exposure = total( timedel*livetime )
    #use datetimes in t_axis...(will this write to FITS correctly?)
    timecen = np.array(spec.t_axis.time_mean) #datetimes

    factor = 1
    #units for L1 are centiseconds
    if spec.primary_header['LEVEL'].strip() == 'L1':
        factor = 100

    #calculate time parameters to be passed into the fits file
    specnum = np.arange(len(timecen)) +1
    channel = np.tile(np.arange(spec.n_energies), spec.n_times).reshape(spec.n_times,spec.n_energies) # array of n_times x n_channels
    #timecen =  tmjd + spec.data['timedel']/2.0 #doesn't actually do anything
    exposure = np.sum((spec.data['timedel']/factor)*spec.eff_livetime_fraction)

    return {"specnum": specnum, "channel": channel, "timedel": spec.data['timedel']/factor, "timecen": timecen, "exposure": exposure}
