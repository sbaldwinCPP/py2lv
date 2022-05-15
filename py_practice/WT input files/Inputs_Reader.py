# -*- coding: utf-8 -*-
"""
Created on Thu May  5 13:50:53 2022

@author: sbaldwin
"""
    
#%% fcal stuff
    # not incredibly important, systems already has a .vi to do this for the GRC
    # useful to confirm undertanding of how vdbiff picks settings and practice working between LV & python

def Read_Fcal(path):
    from pandas import read_excel
    import openpyxl # needed for read_excel
      
    fcal = read_excel(path, header=0)
    # sort by max setting, needed for downstream
    fcal = fcal.sort_values('Max')
    fcal = fcal.reset_index(drop=True)
    return fcal

def Calc_SetPt(cc, A, B):
    # may return pandas series object if not set to float here
    return float(A * cc**B)

def Calc_Flow(SetPt, A, B):
    return (SetPt/A)**(1/B)

def Lookup_Fcal(fcal, device):
    A = fcal[fcal['Device Name']==device]['A']
    B = fcal[fcal['Device Name']==device]['B']
    return A, B


def Get_Setup(inputs, fcal):
    cc = inputs[0]
    tracer = inputs[1]
    
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
            msg = 'N2 flow is below single device operating range'
            raise ValueError(msg)
        elif cc_N2 > sum(N2_opt.Max):
            msg = 'N2 flow is above total device operating range(s)'
            raise ValueError(msg)
        else: 
            # find first combination that works
            # try single device
            N2_opt = N2_opt[N2_opt.Min < cc_N2]
            N2_opt = N2_opt[N2_opt.Max > cc_N2]
            
            if not N2_opt.empty:
                N2_dev = N2_opt['Device Name'].iloc[0]
                A_N2, B_N2 = Lookup_Fcal(fcal, N2_dev)
                N2_set = Calc_SetPt(cc_N2, A_N2, B_N2)
                gas.append('N2')
                dev.append(N2_dev)
                setpt.append(N2_set)
                
            else:
                # try multiple devices
                # reset to full set
                N2_opt = fcal[fcal.Gas=='N2']
            
                csum = N2_opt.Max.cumsum()
                csum = csum[csum >= cc_N2]
                
                cc_total = csum.iloc[0]
                cc_index = csum.index[0]
                
                N2_opt = N2_opt[N2_opt.index<=cc_index]
                
                ratio = cc_N2 / cc_total
                
                cc_set = ratio * N2_opt.Max
                
                for i in cc_set.index:
                    N2_dev = N2_opt['Device Name'][i]
                    A_N2, B_N2 = Lookup_Fcal(fcal, N2_dev)
                    N2_set = Calc_SetPt(cc_set[i], A_N2, B_N2)
                    gas.append('N2')
                    dev.append(N2_dev)
                    setpt.append(N2_set)
            
            return gas, dev, setpt
  
        
       
    
    
#%% simple calls to use in labview    
def Calc_Fcal(inputs, path):
    fcal = Read_Fcal(path)
    global gas, dev, setpt
    gas, dev, setpt = Get_Setup(inputs, fcal)
    
def Get_Gas():
    return gas

def Get_Dev():
    return dev

def Get_SetPt():
    return setpt

    
#%% If local run
if __name__ == '__main__':
    # modules
    print('Importing modules...')
    try:
        # this duplicates module imports but allows for checking when running directly on a new install
        # imports are made at function call for efficinecy when running from labview
        # may remove this option when drivers are stable
        from pandas import read_excel
        import openpyxl # needed for read_excel
        from easygui import msgbox as mb
        print('All modules imported')

    except ModuleNotFoundError as err:
        input(str(err) +' \n Press enter to exit')
        
    # hardcoded path for testing
    path = 'D:\Repos\GitHub\py2lv\py_practice\WT input files\Fcal_alternate.xlsx'
    fcal = Read_Fcal(path)
    #gas, dev, setpt = Get_Setup(2500, 10, fcal)
    inputs = [2500, 10]
    settings = Get_Setup(inputs, fcal)
    print(settings)
    mb(settings)
      