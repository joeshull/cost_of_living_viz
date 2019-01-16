
import pandas as pd 
import numpy as np 



class COLDataLoader():
    #A Class for loading data for the Cost of living calculator.
    #Instantiate with the path to the Zillow city csvs and Consumer Expenditure xlsx
    
    def __init__(self, zillow_path, ce_path):
        self.zillow_path = zillow_path
        self.ce_path = ce_path
        self.df_zil_own = None
        self.df_zil_rent = None
        self.df_ce = None
        
    def load(self):
        #Load Zillow
        self.df_zil_own = pd.read_csv(os.path.join(self.zillow_path, 'City_MedianValuePerSqft_AllHomes.csv'), header=0)
        self.df_zil_rent = pd.read_csv(os.path.join(self.zillow_path,'City_MedianRentalPricePerSqft_AllHomes.csv'))
        
        #Load CE
        file_list = self.get_file_list(self.ce_path)
        list_df = self.get_dataframes(file_list)
        self.df_ce = self.merge_dataframes(list_df)
        
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
            df = df.loc[~df.iloc[:,0].isna(),:]
            df.set_index('Item', inplace=True)
            list_df.append(df)
        return list_df

    def merge_dataframes(self, list_df):
        #Input: list of pd dataframes
        #Output: dataframe joined columnwise by index.
        return pd.concat(list_df, axis=1, ignore_index=False)




if __name__ == '__main__':
	base_ce_path = '../data/bls_ce/msa/'
	base_zil_path = '../data/zillow/city/'
	data = COLDataLoader(base_zil_path, base_ce_path)
	data.load()
