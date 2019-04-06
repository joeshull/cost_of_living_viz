import os

import pandas as pd 
import numpy as np 
import os
import requests
from colgeocoder import COLGeoUtil



class COLDataLoader():
    #A Class for loading data for the Cost of living calculator.
    #Instantiate with the path to the Zillow city csvs and Consumer Expenditure xlsx
    
    def __init__(self, zillow_path, ce_path, state_tax_path, do_geocode=False):
        self.gc= COLGeoUtil()
        self.zillow_path = zillow_path
        self.ce_path = ce_path
        self.state_tax_path = state_tax_path
        self.df_zil_own = None
        self.df_zil_rent = None
        self.df_ce = None
        self.ce_geocodes = None
        self.df_state_tax = None
        self.do_geocode = do_geocode
        
    def load(self):
        #Load Zillow
        self.df_zil_own = pd.read_pickle(os.path.join(self.zillow_path, 'df_zil_own_geocoded.pkl'))
        self.df_zil_rent = pd.read_pickle(os.path.join(self.zillow_path,'df_zil_rent_geocoded.pkl'))
        
        



        #Load CE
        file_list = self.get_file_list(self.ce_path)
        list_df = self.get_dataframes(file_list)
        self.df_ce = self.merge_dataframes(list_df)

        

        #Delete Summary Columns
        ce_cols = [False if 'All' in item else True for item in self.df_ce.columns.values]
        self.df_ce = self.df_ce.loc[:, ce_cols ]

        ## Get CE geocodes
        try:
            head, tail = os.path.split(self.ce_path)
            self.ce_geocodes = np.load(os.path.join(head,'ce_geocodes.npy'))

        except:
            self.ce_geocodes = self.gc.geocode_ce(self.df_ce)

        #Load State Tax
        self.get_state_tax()

        #Do geocode
        if self.do_geocode:
            
            with requests.Session() as session1, requests.Session() as session2:
                self.df_zil_own = self.gc.geocode_dataframe(self.df_zil_own, 'RegionName', 'State', session)
                self.df_zil_rent = self.gc.geocode_dataframe(self.df_zil_rent, 'RegionName', 'State', session)

            
            

        
    def remove_non_numeric(self,x):
        try:
            return float(x)
        except:
            return float(''.join([d for d in str(x) if d.isnumeric()]))
        
    def get_state_tax(self):
        path = os.path.join(self.state_tax_path, os.listdir(self.state_tax_path)[0])
        self.df_state_tax = pd.read_csv(path, na_values='None')
        #Make infinite range
        self.df_state_tax.loc[self.df_state_tax.incomeNotGreaterThan.isna(),'incomeNotGreaterThan'] = np.inf
        #Fill other rates with 0
        self.df_state_tax.iloc[:,-3:-1]= self.df_state_tax.iloc[:,-3:-1].fillna(0)
        #Remove Non-numeric characters from numeric columns
        self.df_state_tax.iloc[:,-3:] = self.df_state_tax.iloc[:,-3:].applymap(self.remove_non_numeric)
        
    
    def get_file_list(self, base_path):
        #Input: String - folder path to xlsx files
        #Output: List of Strings - paths to the files
        files = os.listdir(base_path)
        file_list = []
        for file in files:
            if not file.startswith('~'):
                file_path = os.path.join(base_path, file)
                file_list.append(file_path)
        return file_list

    def get_dataframes(self, file_list):
        #Input: List of Strings - paths to xlsx files
        #Output: List of pd dataframes
        list_df = []
        for file in file_list:
            df = pd.read_excel(file, header=2)
            df = df.loc[~df.iloc[
                
                
                :,0].isna(),:]
            df.set_index('Item', inplace=True)
            list_df.append(df)
        return list_df

    def merge_dataframes(self, list_df):
        #Input: list of pd dataframes:
        #Output: dataframe joined columnwise by index.
        return pd.concat(list_df, axis=1, ignore_index=False)



if __name__ == '__main__':
    base_ce_path = 'data/bls_ce/msa/'
    base_zil_path = 'data/zillow/city/'
    base_tax_path = 'data/state_tax/'
    data = COLDataLoader(base_zil_path, base_ce_path, base_tax_path)
    data.load()
