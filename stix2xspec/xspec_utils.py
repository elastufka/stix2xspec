import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

from datetime import datetime as dt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from IPython.display import Markdown
from astropy.io import fits
from astropy.time import Time
from astropy.table import Table

def spectrum_from_time_interval(original_fitsfile, start_time, end_time, out_fitsname=None):
    """Write average count rate over selected time interval to new FITS file for fitting with XSPEC.
    
    Args:
        original_fitsfile (str): Name of FITS file from which to get the spectrum.
        start_time (str, datetime, int, float): Start time in format readable by astropy.Time.
        end_time (str, datetime, int, float): End time in format readable by astropy.Time.
        out_fitsname (str): Name of output FITS file. Defaults to None."""
    reference_fits = fits.open(original_fitsfile)
    primary_HDU = reference_fits[0] #header = reference_fits[0].header.copy()
    rate_header = reference_fits[1].header.copy()
    #energy_header = reference_fits[2].header.copy()
    rate_data = reference_fits[1].data.copy()
    #energy_data = reference_fits[2].data.copy()
    energy_HDU = reference_fits[2]
    nchan = len(rate_data['CHANNEL'][0])

    #time axis
    duration_seconds = rate_data['TIMEDEL'] #seconds
    duration_day = duration_seconds/86400
    time_bin_center = rate_data['TIME']
    if Time(time_bin_center[0], format='mjd').datetime.year < 2020 or Time(time_bin_center[0], format='mjd').datetime.year > dt.now().year: #fix the time
        #compare time axis
        tt = Time([Time(rate_header['TIMEZERO']+rate_header['MJDREF'], format='mjd').datetime + td(seconds = t) for t in time_bin_center])
        time_bin_center = tt.mjd

    t_start = Time([bc - d/2. for bc,d in zip(time_bin_center, duration_day)], format='mjd')
    t_end = Time([bc + d/2. for bc,d in zip(time_bin_center, duration_day)], format='mjd')
    t_mean = Time(time_bin_center, format='mjd')
    
    #index times that fall within selected interval
    tstart = Time(start_time)
    tend = Time(end_time)
    tselect = np.where(np.logical_and(time_bin_center >= tstart.mjd,time_bin_center < tend.mjd)) #boolean mask
    #ttimes = time_bin_center[tselect] #actual times
    #print(f"tselect {tselect[0][0]} {tselect[0][-1]}")
    exposure =  np.sum(rate_data['TIMEDEL'][tselect[0]]*rate_data['LIVETIME'][tselect[0]])

    #rate data
    avg_counts = np.array([np.mean(rate_data['RATE'][tselect],axis=0)]).reshape((1,nchan)) #mean since it's already a rate
    #print(f"max counts: {np.max(total_counts)}")
    
    #average livetime data - same number for each channel
    avg_livetime = np.array([np.mean(rate_data['LIVETIME'][tselect]) for n in range(nchan)]).reshape((1,nchan)) #now sum #np.array([np.mean(rate_data['LIVETIME'][tselect])]).reshape((1,))
    
    #error...
    avg_err = np.mean(rate_data['STAT_ERR'][tselect],axis=0).reshape((1,nchan))
    avg_sys_err = np.mean(rate_data['SYS_ERR'][tselect],axis=0).reshape((1,nchan))
    
    # Update keywords that need updating
    #rate_header['DETCHANS'] = self.n_energies
    rate_header.set('NAXIS',1)
    rate_header.set('NAXIS1', 1)
    del rate_header['NAXIS2']
    
    #rate_header['EXPOSURE'] = exposure #does this make a difference?
    #rate_header['ONTIME'] = exposure
    #print(f"exposure: {exposure}")
    #update times in rate header
    rate_header['TSTARTI'] = int(np.modf(tstart.mjd)[1]) #Integer portion of start time rel to TIMESYS
    rate_header['TSTARTF'] = np.modf(tstart.mjd)[0] #Fractional portion of start time
    rate_header['TSTOPI'] = int(np.modf(tend.mjd)[1])
    rate_header['TSTOPF'] = np.modf(tend.mjd)[0]

    #update rate data
    #print(f"max count rate: {np.max(total_counts/exposure)}")
    rate_names = ['RATE', 'STAT_ERR', 'CHANNEL', 'SPEC_NUM', 'LIVETIME', 'TIME', 'TIMEDEL', 'SYS_ERR']
    rate_table = Table([avg_counts.astype('>f8'), avg_err.astype('>f8'), rate_data['CHANNEL'][0].reshape((1,nchan)), [0],avg_livetime.astype('>f8'), np.array([rate_data['TIME'][tselect[0][0]]]), np.array([np.sum(rate_data['TIMEDEL'][tselect])]), avg_sys_err], names = rate_names) #is spec.counts what we want?

    #primary_HDU = fits.PrimaryHDU(header = primary_header)
    rate_HDU = fits.BinTableHDU(header = rate_header, data = rate_table)
    #energy_HDU = fits.BinTableHDU(header = energy_header, data = energy_data)
    #print(energy_HDU.header)
    hdul = fits.HDUList([primary_HDU, rate_HDU, energy_HDU]) #, att_header, att_table])
    if not out_fitsname:
        out_fitsname=f"{original_fitsfile[:-5]}_{pd.to_datetime(start_time):%H%M%S}-{pd.to_datetime(end_time):%H%M%S}.fits"
    hdul.writeto(out_fitsname)
    
def fits_time_to_datetime(fitsfile, idx = None):
    """Return a datetime axis or single datetime given an OGIP-format FITS file.
    
    Args:
        fitsfile (str): Name of FITS file.
        idx (int, optional): Index at which to return datetime. Defaults to None.
        
    Returns:
        np.array: Array of datetimes, or single datetime if idx is not None."""
    with fits.open(fitsfile) as f:
        time_bin_center = f[1].data.TIME
        if Time(time_bin_center[0], format='mjd').datetime.year < 2020 or Time(time_bin_center[0], format='mjd').datetime.year > dt.now().year:
            tt = Time([Time(f[1].header['TIMEZERO']+f[1].header['MJDREF'], format='mjd').datetime + td(seconds = t) for t in time_bin_center])
        else:
            tt = Time(time_bin_center, format = 'mjd')
    if idx:
        return tt.datetime[idx]
    return tt.datetime

#def select_background_interval():

def fit_thermal_nonthermal(xspec, thmodel = 'apec', ntmodel = 'bknpower', lowErange = [2.0,10.0], highErange = [8.0,30.0], breakEstart = 15, breakEfrozen=False, minCounts=10, statMethod='chi',query='no',renorm=True,nIterations = 1000,renotice = True):
    '''Fit thermal and non-thermal components to spectrum via the following steps:
    
    1) fit thermal over low energy
    2) fit non-thermal over high-energy with initial break energy frozen (if non-thermal model is bknpow or thick2)
        2a) unfreeze break energy and fit non-thermal again
    3) fit thermal and non-thermal together over entire energy range
    
    Args:
        xspec
        thmodel (str, optional): Defaults to 'apec'. Thermal model to use.
        ntmodel (str, optional): Defaults to 'bknpower'. Non-thermal model to use. Can also be set to None, in which case only a thermal model will be fit to the data.
        lowErange (list or tuple, optional): Defaults to [2.0,10.0].
        highErange (list or tuple, optional): Defaults to [8.0,30.0]
        breakEstart (float, optional): Defaults to 15. Energy at which to
        breakEfrozen (bool, optional): Defaults to False. Freeze the break energy parameter or not.
        minCounts (int, optional): Defaults to 10. Not yet implemented.
        statMethod (str, optional): Defaults to 'chi'. Statistics to be used.
        query (str, optional): Defaults to 'no'. Whether to query the user for further iterations once max iterations are reached.
        renorm (bool, optional): Defaults to True. Whether to re-normalize the data or not.
        nIterations (int, optional): Defaults to 1000. Number of iterations before querying for more or stopping.
        renotice (bool, optional): Defaults to True. Whether to notice all the channels after the fit is complete (for plotting purposes mainly) or not.
        
    Returns:
        tuple: model, chisq
    '''
    breakE = True #assume there's a break energy
    xspec.Xset.abund="felc"
    if ntmodel != 'thick2':
        xspec.AllModels.clear() #for now...
    #settings for fit
    xspec.Fit.statMethod = statMethod #Valid names: 'chi' | 'cstat' | 'lstat' | 'pgstat' | 'pstat' | 'whittle'.
    xspec.Fit.query = query
    xspec.Fit.nIterations = nIterations
        
    #step 1
    m = xspec.Model(f'{thmodel}')
    xspec.AllData.ignore(f"0.-{lowErange[0]} {lowErange[1]}-**")
    
    xspec.Fit.renorm()
    xspec.Fit.perform()
    
    mtherm_params = get_xspec_model_params(getattr(m,thmodel), norm = True)
    
    if ntmodel is not None:
        #step2 - fit non-thermal
        xspec.AllModels.clear()
        m = xspec.Model(f'{thmodel}+{ntmodel}')
        m_th = getattr(m, thmodel)
        set_xspec_model_params(m, thmodel, mtherm_params, frozen = True)
            
        m_nt = getattr(m,ntmodel)
        try: #in thick2 it's eebrk not BreakE...
            breakEindex = getattr(m_nt, 'BreakE')._Parameter__index
            m.setPars({breakEindex:f"{breakEstart} -.5,,,{breakEstart+2}"})
            breakparname = 'BreakE'
            #p = getattr(m_nt,'BreakE')
        except AttributeError:
            try:
                breakEindex = getattr(m_nt, 'eebrk')._Parameter__index
                m.setPars({breakEindex:f"{breakEstart} -.5,,,{breakEstart+2}"})
                breakparname = 'eebrk'
                lowEindex = getattr(m_nt, 'eelow')._Parameter__index
                m.setPars({lowEindex:f"{breakEstart-5} -.5,,,{breakEstart-2}"})
                p = getattr(getattr(m,ntmodel),'eelow')
                p.frozen = False
            except AttributeError:
                breakE = False
     
        xspec.AllData.notice('all')
        #check that count rate at highErange is above minCounts, otherwise adjust highErange and warn
        #TBD
        #warn for negative count rate and zero errors while we're here
        #TBD
        xspec.AllData.ignore(f"0.-{highErange[0]} {highErange[1]}-**")
        
        xspec.Fit.renorm()
        xspec.Fit.perform()

        if breakE and not breakEfrozen: #fit again with unfrozen break E
            p = getattr(getattr(m,ntmodel),breakparname)
            p.frozen = False
            xspec.Fit.renorm()
            xspec.Fit.perform()
            
        #step 3 - fit together, all parameters free
        for param in ['kT','norm']:
            p = getattr(m_th, param)
            p.frozen = False
            
        xspec.AllData.notice('all')
        xspec.AllData.ignore(f"0.-{lowErange[0]} {highErange[1]}-**")
        
        xspec.Fit.renorm()
        xspec.Fit.perform()
    print(f"Fit statistic: {xspec.Fit.statMethod.capitalize()}   {xspec.Fit.statistic:.3f} \n Null hypothesis probability of {xspec.Fit.nullhyp:.2e} with {xspec.Fit.dof} degrees of freedom")
    fitstat = xspec.Fit.statistic
    if renotice:
        xspec.AllData.notice('all')
    return m,fitstat


def get_xspec_model_params(model_component, norm=False):
    '''Returns tuple of current values of xspec model component parameters.
    Input: xspec Component object'''
    if not norm:
        return tuple([getattr(model_component,p).values[0] for p in model_component.parameterNames if p!='norm'])
    else:
        return tuple([getattr(model_component,p).values[0] for p in model_component.parameterNames])
        
def set_xspec_model_params(model, model_component, component_params, frozen = False):
    '''Sets current values of xspec model parameters.
    Input: xspec Model Component object, tuple of xspec model parameters'''
    mcomp = getattr(model, model_component)
    for param, pval in zip(mcomp.parameterNames, component_params):
        pidx =  getattr(mcomp, param)._Parameter__index
        model.setPars({pidx:f"{pval} -.1,,,{pval}"})
        if not frozen:
            p = getattr(mcomp, param)
            p.frozen = False
        
def get_xspec_model_sigmas(model_component):
    '''Returns tuple of current values of xspec model component parameter sigmas.
    Input: xspec Component object'''
    return tuple([getattr(model_component,p).sigma for p in model_component.parameterNames])
        
def show_model(model, df=False):
    '''Equivalant of pyxspec show() but in Markdown for Jupyter Notebooks, or easy copy-pasting. Return dataframe to display nicely in terminal or JupyterLab
    Input: xspec Model object'''
    mdtable="|Model par| Model comp | Component|  Parameter|  Unit |    Value| Sigma |\n |---|---|---|---|---|---| |\n"
    pdict={'Model par':[], 'Model comp':[], 'Component':[], 'Parameter': [], 'Unit': [], 'Value': [], 'Sigma':[]}
    for i,n in enumerate(model.componentNames):
        nprev=0
        if i>0:
            try:
                nprev=len(getattr(model,model.componentNames[i-1]).parameterNames)
            except IndexError:
                nprev=0
        for j,p in enumerate(getattr(model,n).parameterNames):
            param=getattr(getattr(model,n),p)
            val=getattr(param,'values')[0]
            fmt=".2e"
            if np.abs(np.log10(val)) < 2:
                fmt=".2f"
            if getattr(param,'frozen'):
                plusminus='frozen'
            else:
                plusminus= f"± {getattr(param,'sigma'):{fmt}}"
            mdtable+=f"|{j+1+nprev} |{i+1} | {n}|{p}| {getattr(param,'unit')}| {getattr(param,'values')[0]:{fmt}} | {plusminus}|\n"
            pdict['Model par'].append(j+1+nprev)
            pdict['Model comp'].append(i+1)
            pdict['Component'].append(n)
            pdict['Parameter'].append(p)
            pdict['Unit'].append(getattr(param,'unit'))
            pdict['Value'].append(f"{getattr(param,'values')[0]:{fmt}}")
            pdict['Sigma'].append(plusminus)
            
    if df: #jupyterlab doesn't work with Mardown for whatever reason, but it will display a dataframe nicely
        return pd.DataFrame(pdict)
    else:
        return Markdown(mdtable)
    
def show_error(model):
    '''Show parameters and errors, if errors have been calculated. Input: xspec Model object'''
    
    tclout_errs={0:"new minimum found",1:"non-monotonicity detected",2:"minimization may have run into problem",3:"hit hard lower limit",4:"hit hard upper limit",5:"    parameter was frozen",6:"search failed in -ve direction",7:"search failed in +ve direction",8:"reduced chi-squared too high"}

    mdtable="|Model par| Model comp | Component|  Parameter|  Unit | Value| Lower Bound | Upper Bound | Calculation Error |\n |---|---|---|---|---|---|---|---|---|\n"
    for i,n in enumerate(model.componentNames):
        nprev=0
        if i>0:
            try:
                nprev=len(getattr(model,model.componentNames[i-1]).parameterNames)
            except IndexError:
                nprev=0
        for j,p in enumerate(getattr(model,n).parameterNames):
            param=getattr(getattr(model,n),p)
            err= getattr(param,'error')
            fmt=".2e"
            if np.abs(np.log10(getattr(param,'values')[0])) < 2:
                fmt=".2f"
            errcodes="<br>".join([tclout_errs[i] for i,e in enumerate(err[2]) if e=='T' ])
            upper=err[1]
            lower=err[0]
            mdtable+=f"|{j+1+nprev} |{i+1} | {n}|{p}| {getattr(param,'unit')}| {getattr(param,'values')[0]:{fmt}} | {lower:{fmt}}| {upper:{fmt}} | {errcodes}\n"
    return Markdown(mdtable)
    
def show_statistic(fit):
    '''input xspec.Fit'''
    return Markdown(f"Fit statistic: {fit.statMethod.capitalize()}   {fit.statistic:.3f} \n Null hypothesis probability of {fit.nullhyp:.2e} with {fit.dof} degrees of freedom")

def plot_data(xspec,fitrange=False, dataGroup=1,erange=False,yrange=False, counts=False, title = None):
    '''Plot spectrum data in PlotLy, as either count rate (default) or counts. Input: xspec global object '''

    xspec.Plot.xAxis = "keV"
    #xspec.Plot('ufspec')
    #model = xspec.Plot.model()
    if not counts: #plot count rate
        xspec.Plot('data')
        ytitle='Counts/s'
        if not yrange:
            yrange=[-2,4.5]
    else:
        xspec.Plot('counts')
        ytitle='Counts'
        if not yrange:
            yrange=[1,1e6]
    xx = xspec.Plot.x()
    yy = xspec.Plot.y()
    if not erange:
        erange=[xx[0],xx[-1]]
    xl=np.where(np.array(xx) > erange[0])[0][0]
    try:
        xg=np.where(np.array(xx) >= erange[1])[0][0]
    except IndexError:
        xg=len(xx)-1
    yrange=[np.floor(np.log10(yy[xl:xg])).min(),np.ceil(np.log10(yy[xl:xg])).max()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xx,y=yy,line_shape= 'hvh',name='data',error_y=dict(type='data',array=xspec.Plot.yErr())))
    fig.update_yaxes(title=ytitle,range=yrange,type='log',showexponent = 'all',exponentformat = 'e') #type='log'
    fig.update_xaxes(title='Energy (keV)',range = erange)
    fig.update_layout(title = title)
    return fig

def plot_fit(xspec, model, fitrange=False, dataGroup=1,erange=False,yrange = [-3, 4], res_range=[-5,5],title=False,annotation=False, plotdata_dict = False, width = 500, height = 700):
    '''Plot data, fit, residuals in PlotLy. Plot from dictionary of plot parameters if xspec = None, model = plotadata
    
    Input:
        xspec: xspec global object or dict
            Inputs to plot
        
        model: xspec Model object or None
            Model data or None, if a previously-generated plotdata_dict is used as the input variable _xspec_
    
    Returns:
    plotdata_dict: dict
        The PlotLy plot data in a dictionary, to make tweaking the plot via update_layout, update_traces, update_axes, etc. later possible, since the Model object will overwrite itself eventually and be unable to plot via repeated calls to this function.
     '''
    
    if xspec is not None:
        xspec.Plot.xAxis = "keV"
        cnames = model.componentNames
        full_model_name = '+'.join(cnames)
        ncomponents = len(cnames)
        xspec.Plot.add=True
        xspec.Plot('data')
        xx = xspec.Plot.x()
        yy = xspec.Plot.y()
        yErr = xspec.Plot.yErr()
        if ncomponents == 1:
            model_comps = [xspec.Plot.model()]
        else:
            model_comps = []
            for comp in range(ncomponents):
                model_comps.append(xspec.Plot.addComp(comp+1))
            model_comps.append(xspec.Plot.model()) #total
            cnames.append(full_model_name)
        xspec.Plot('delchi')
        res = xspec.Plot.y()
    else:
        xx = model['Energy']
        yy = model['CountRate']
        yErr = model['CountErr']
        cnames = list(model['Fit'].keys())[1:] #first is fitdata
        full_model_name = cnames[-1]
        model_comps = [model['Fit'][c] for c in cnames]
        fitrange = model['Fit']['fitrange']
        res = model['Residuals']
    
    if not fitrange:
        fitrange=[xx[0],xx[-1]]
    if not erange:
        erange=[xx[0],xx[-1]]
    if not title:
        title=f"Fit with {full_model_name}"
    xl=np.where(np.array(xx) > erange[0])[0][0]
    try:
        xg=np.where(np.array(xx) >= erange[1])[0][0]
    except IndexError:
        xg=len(xx)-1

    if not yrange:
        yrange=[np.floor(np.log10(yy[xl:xg])).min(),np.ceil(np.log10(yy[xl:xg])).max()]
    
    fig = make_subplots(rows=2, cols=1, start_cell="top-left",shared_xaxes=True,row_heights=[.6,.3],vertical_spacing=.05)
    fig.add_trace(go.Scatter(x=xx,y=yy,mode='markers',name='data',error_y=dict(type='data',array=yErr)),row=1,col=1)
    for m, model_name in zip(model_comps,cnames):
        if '+' in model_name: #match color to residuals
            fig.add_trace(go.Scatter(x=xx,y=m,name=model_name, line_color = 'black', line_shape = 'hvh'),row=1,col=1)
        else:
            fig.add_trace(go.Scatter(x=xx,y=m,name=model_name, line_shape = 'hvh'),row=1,col=1)

    #plot residuals
    fig.update_yaxes(type='log',row=1,col=1,showexponent = 'all',exponentformat = 'e',range=yrange, title = 'Count Rate')
    fig.add_trace(go.Scatter(x=xx,y=res,mode = 'lines+markers',marker_color='black',name='residuals',line_shape = 'hvh'),row=2,col=1)
    fig.add_vrect(x0=fitrange[0],x1=fitrange[1],annotation_text='fit range',fillcolor='lightgreen',opacity=.25,line_width=0,row=1,col=1)
    fig.add_vrect(x0=fitrange[0],x1=fitrange[1],fillcolor='lightgreen',opacity=.25,line_width=0,row=2,col=1)
    if annotation:
        fig.add_annotation(x=1.25,y=.5,text=annotation,align='left',xref='x domain',yref='paper')
    fig.update_yaxes(title='Residuals',range=res_range,row=2,col=1)
    fig.update_xaxes(type='log',showexponent = 'all',exponentformat = 'e', title='Energy (keV)',range=[0,2],row=2,col=1)
    fig.update_xaxes(type='log',showexponent = 'all',exponentformat = 'e', title='Energy (keV)',range=[0,2],row=1,col=1)
    fig.update_layout(width=width,height=height,title=title)
    
    if plotdata_dict: #return plot data in a dictionary
        fitdata = {'fitrange':fitrange}
        for c,m in zip(cnames,model_comps):
            fitdata[c] = m
        plotdata = {'Energy': xx, 'CountRate': yy, 'CountErr': yErr, 'Fit': fitdata, 'Residuals': xspec.Plot.y()}
        return fig, plotdata
    return fig
    
def annotate_plot(model, chisq=None, last_component=False, exclude_parameters = ['norm'], error = False, MK = False):
    '''annotations for plot - parameters and confidence intervals if they can be calculated
    Input: xspec Model object
    Output: HTML-formatted string'''
    fittext = "" if not chisq else f"Chisq: {chisq:.2f}<br>"

    if not last_component:
        cnames = model.componentNames[:-1]
    for comp in cnames:
        mc = getattr(model,comp)
        for par in getattr(mc,"parameterNames"):
            if par not in exclude_parameters:
                p = getattr(mc,par)
                val = p.values[0]
                unit = p.unit
                sigma = p.sigma
                if comp in ['apec','vth'] and par == 'kT' and MK: #convert from keV
                    val /= 0.08617 # eV/K -> keV/MK
                    unit = 'MK'
                    sigma /= 0.08617
                fmt = ".2e"
                if np.abs(np.log10(val)) < 2:
                    fmt = ".2f"
                if p.error[2] == "FFFFFFFFF" and error: #error calculated sucessfully
                    errs = f"({p.error[0]:{fmt}}-{p.error[1]:{fmt}})"
                else:
                 errs = f"±{sigma:{fmt}}"#""
                fittext += f"{par}: {val:{fmt}} {errs} {unit}<br>"
    if fittext.endswith("<br>"):
        fittext = fittext[:-4].strip()
    return fittext
