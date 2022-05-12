# -*- coding: utf-8 -*-
"""
Created on Thu May  5 13:50:53 2022

@author: sbaldwin
"""

# modules
# default packages
import os

# non-default packages
import pandas as pd
import openpyxl
from easygui import msgbox as mb
    
#%% fcal stuff
    # not incredibly important, systems already has a .vi to do this for the GRC
    # useful to confirm undertanding of how vdbiff picks settings 

def Read_Fcal():
    #hardcoded
    path = 'D:\Repos\GitHub\py2lv\py_practice\WT input files\Fcal_alternate.xlsx'   
    return pd.read_excel(path, header=0)

def Calc_SetPt(cc, A, B):
    # may return pandas series object if not set to float here
    return float(A * cc**B)

def Calc_Flow(SetPt, A, B):
    return (SetPt/A)**(1/B)

def Lookup_Fcal(fcal, device):
    A = fcal[fcal['Device Name']==device]['A']
    B = fcal[fcal['Device Name']==device]['B']
    return A, B

def Get_Setup(cc, tracer, fcal):
    # fcal=Read_Fcal()
    
    # split total flow into ethane & N2
    cc_eth = cc * tracer/100
    cc_N2 = cc - cc_eth
    
    # find Ethane MFC
    eth_opt = fcal[fcal.Gas=='Ethane']
    if cc_eth > max(eth_opt.Max):
        msg = 'Ethane flow is above device operating range(s)'
        raise ValueError(msg)
    elif cc_eth < min(eth_opt.Min):
        msg = 'Ethane flow is below device operating range(s)'
        raise ValueError(msg)
    else:
        eth_opt = eth_opt[eth_opt.Min < cc_eth]
        eth_opt = eth_opt[eth_opt.Max > cc_eth]
        eth_dev = eth_opt['Device Name'].iloc[0]
        
        # calculate set points
        A_eth, B_eth = Lookup_Fcal(fcal, eth_dev)
        eth_set = Calc_SetPt(cc_eth, A_eth, B_eth)
        
        #init outputs       
        gas = ['Ethane']
        dev = [eth_dev]
        setpt = [eth_set]

        # find N2 MFC
        N2_opt = fcal[fcal.Gas=='N2']
        if cc_N2 < min(N2_opt.Min):
            msg = 'N2 flow is below device operating range(s)'
            raise ValueError(msg)
        elif cc_N2 > max(N2_opt.Max):
            # try 2 devices 
            n = 2
            cc_N2 = cc_N2/2
            if cc_N2 > max(N2_opt.Max):
                msg = 'N2 flow is above device operating range(s) for 2 devices'
                raise ValueError(msg)
        else: n = 1
            
        N2_opt = N2_opt[N2_opt.Min < cc_N2]
        N2_opt = N2_opt[N2_opt.Max > cc_N2]
        
        for i in range(n):
            N2_dev = N2_opt['Device Name'].iloc[i]
            A_N2, B_N2 = Lookup_Fcal(fcal, N2_dev)
            N2_set = Calc_SetPt(cc_N2, A_N2, B_N2)
            gas.append('N2')
            dev.append(N2_dev)
            setpt.append(N2_set)    
        
        return gas, dev, setpt
    
def test():
    fcal = Read_Fcal()
    return Get_Setup(500, 1, fcal)
    
# =============================================================================
# def SumClusterIntegers(cluster):
#     "cluster[0] -> Integer, cluster[1] -> String, cluster[2] -> Integer"
#     return cluster[0] + cluster[2]
#     
# =============================================================================
    
#%% TEST
if __name__ == '__main__':
    fcal = Read_Fcal()
    gas, dev, setpt = Get_Setup(2500, 10, fcal)
    settings = [gas, dev, setpt]
    print(settings)
    mb(settings)
      