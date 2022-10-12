import pandas as pd
import numpy as np
import os
from datetime import datetime as dt

class Triggergram:
    """This creates a class containing the triggergram data with its time and accumulator axes. Translation of *stx_triggergram.pro*"""
    def __init__(self, triggerdata, t_axis, adg_idx = None):
        """
        Args:
            triggerdata (np.array): 2D-data array containing triggers over time, either all 16 triggers by time or 1 trigger id by time
            t_axis (stix2xspec.stx_taxis): The time axis
            adg_idx (list or array, optional): Defaults to None. It is the adg_idx (1-16) of the single trigger accumulator data passed."""
        self.type = 'stx_triggergram'
        self.adg_idx = adg_idx
        self.t_axis = t_axis
        self.calc_triggerdata(triggerdata)
        
    def check_types(self, triggerdata):
        """Check that triggerdata is 16 x M or 1x M array and time axis is object."""
        if not isinstance(triggerdata, np.ndarray):
            raise TypeError("Parameter 'triggerdata' must be a 16 x M or 1 x M int array")
        if triggerdata.shape[0] not in [16,1]:
            raise ValueError("Parameter 'triggerdata' must be a 16 x M or 1 x M int array")
        if self.t_axis.type != 'stx_time_axis':
            raise TypeError("Parameter 't_axis' must be a stx_time_axis object")
        if len(triggerdata.shape) == 2 and triggerdata.shape[1] != len(self.t_axis.time_mean):
            raise ValueError("'t_axis' dimensions do not agree with 'triggerdata' dimensions")
            
    def calc_triggerdata(self, triggerdata):
        """Assign the attributes triggerdata and adg_idx (if previously unassigned)."""
        self.check_types(triggerdata)
        if triggerdata.shape[0] == 16:
            self.adg_idx = np.arange(16) + 1
        self.triggerdata = triggerdata.astype(np.uint64)
