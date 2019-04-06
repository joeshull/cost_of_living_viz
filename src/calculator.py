import pandas as pd 
import numpy as np
from dataloader import COLDataLoader
from colgeocoder import COLGeoUtil

class COLCalculator():
    #Cost of Living Calculator
    #Instantiate with the path to the Zillow city csvs and Consumer Expenditure xlsxs
    def __init__(self, zillow_path, ce_path, state_tax_path):
        self.data = COLDataLoader(zillow_path, ce_path, state_tax_path)
        self.data.load()
        self.gc = COLGeoUtil()
        
    def calculate(self, gross_income=100000, city="San Francisco", state ="CA", married=False, mrtg_int=0.0459):
        #Calculation function: returns a dict (or json) with the following values
        #income_taxes (Tuple): (Float: Approx amount of taxes paid, Float: Approx. Effective Tax Rate, Float: Net Income)
        #ratios (dict) : Spending items with 1. Float: Annual dollars spent according to CE, 2. Float: Ratio of gross income spent on category
        #according to CE
        #housing_rent (Tuple): (Int: sqft affordable at the housing % ratio, Int: Max # people in house)
        #housing_own (Tuple): (Int: sqft affordable at the housing % ratio, Int: Max # people in house
        geocode = self.gc.geocode_one([city,state])
        tax_amount, tax_rate, net_income = self._get_taxes(gross_income, city, state, married)
        ratio_dict = self._get_ratios(gross_income, geocode)
        housing_own, housing_rent = self._get_housing(gross_income, ratio_dict, geocode, mrtg_int)

        return {
                "input": {
                        "gross_income" : gross_income, "city": city, "state" : state, "married" : married, "mortgage_rate": mrtg_int
                },
            
                
                "result":{
                    "taxes": {"tax_amount":tax_amount, "tax_rate":tax_rate, "net_income": net_income}, "geocode" : tuple((float(geocode[0]), float(geocode[1]))),
                    "ratios": ratio_dict, "housing_own": housing_own, "housing_rent" : housing_rent 
                                    }
                }
    
    # Tax Calculation  - Federal and State
    def _get_taxes(self, gross_income, city, state, married):
        #returns tax amount, tax %, and net income
        fed_tax, fed_rate = self._calc_fed_tax(gross_income, married)
        state_tax, state_rate = self._calc_state_tax(gross_income, state, married)
        total_tax = round(fed_tax + state_tax, 2)
        net_income = round(gross_income - total_tax, 2)
        effective_tax = round(total_tax/gross_income, 5)

        return float(total_tax), float(effective_tax), float(net_income)


    
    def _calc_fed_tax(self, gross_income, married):
        #tax withholding from https://www.irs.gov/pub/irs-pdf/n1036.pdf
        #Returns Tax Amount and rate used to calculate withholding
        single_rate = np.array([[3800, 0, .1],
                                [13500, 970,  .12],
                                [43275, 4543,  .22],
                                [88000, 14382, .24],
                                [164525, 32748,  .32],
                                [207900, 46628, .35],
                                [514100, 153799, .37]]
                                )

        single_rate = np.hstack((single_rate, 
                                np.append(single_rate[1:,0],np.inf).reshape(-1,1)
                                ))

        married_rate = np.array([[11800, 0, .1],
                                 [31200, 1940, .12],
                                 [90750, 9086, .22],
                                 [180200, 28765, .24],
                                 [333250, 65497, .32],
                                 [420000, 93257, .35],
                                 [624150, 164710, .37]
                                ])

        married_rate = np.hstack((married_rate, 
                                np.append(married_rate[1:,0],np.inf).reshape(-1,1)
                                ))
        rate = single_rate
        if married:
            rate = married_rate

        mask = np.logical_and(rate[:,0]<=gross_income, rate[:,-1]>gross_income)

        mask = np.logical_and(rate[:,0]<=gross_income, rate[:,-1]>gross_income)
        if mask.any():
            threshold, base_tax, rate = rate[mask][0][0], rate[mask][0][1], rate[mask][0][2]
            return ((base_tax + (gross_income-threshold)*rate), rate)
        else:
            return (0, 0)

        
    def _calc_state_tax(self,gross_income, state, married):
        #Returns State Tax Amount and Rate used to calculate the amount
        income = gross_income - 12000
        if married:
            income = gross_income - 24000
        tax_rates = self.data.df_state_tax.loc[self.data.df_state_tax.stateAbbr == state]
        mask = np.logical_and(tax_rates.iloc[:,-2].values<gross_income, tax_rates.iloc[:,-1].values>=gross_income)
        rate = tax_rates.loc[mask,"incomeTaxRate"].values[0]
        return (income*rate, rate)
    
    def _get_ratios(self, gross_income, geocode):
        #get closest city
        ce_idx = self.gc.get_closest_index(self.data.ce_geocodes, geocode)
        df = self.data.df_ce.iloc[:,ce_idx]
        df.dropna(axis=0)
        
        #Make % ratio of gross income spent on living items
        ratios = df / df["Income before taxes"]
        
        #Hard-code list of spending items (in order of importance) that should total 100%
        items_expenditure = ["Housing", "Food", "Transportation", "Healthcare",
                             "Apparel and services", "Entertainment", "Personal care products and services",
                             "Reading", "Education", "Tobacco products and smoking supplies", "Miscellaneous",
                             "Cash contributions", "Personal insurance and pensions"]
        quality_of_life = ["Apparel and services", "Entertainment", "Personal care products and services",
                             "Reading", "Education", "Tobacco products and smoking supplies", "Miscellaneous",
                             "Cash contributions", "Personal insurance and pensions"]
        
        out_dict = {}
        for key in items_expenditure:
            ratio = ratios[key]
            value = ratio*gross_income
            out_dict[key] = {"dollar_budget": float(round(value,2)), "ratio_of_income": float(round(ratio,3))}
        return out_dict
    
    def _get_housing(self, gross_income, ratio_dict, geocode, mrtg_int):
        #Returns two tuples
        #housing_own (Tuple): (Int: sqft affordable at the housing % ratio, Float: $/sqft, max # people)
        #Mortgage Calculator makes an unrealistic assumption for simplicity: No down payment. 
        #housing_rent (Tuple): (Int: sqft affordable at the housing % ratio, Float: $/sqft, max # people)
        
        #Get idx of closest city 
        city_own_idx = self.gc.get_closest_index(self.data.df_zil_own.lat_lng.values, geocode)
        city_rent_idx = self.gc.get_closest_index(self.data.df_zil_rent.lat_lng.values, geocode)
        
        #Get costs for closest city
        own_cost_per_sqft = self.data.df_zil_own.iloc[city_own_idx, -1]
        rent_cost_per_sqft = self.data.df_zil_rent.iloc[city_rent_idx, -1]
        
        #Calc Mortgage and housing size
        own_budget = self._calc_mrtg(ratio_dict["Housing"]["dollar_budget"], mrtg_int)
        own_sqft = own_budget/own_cost_per_sqft
        housing_own = {"own_sqft": int(own_sqft), "own_person_capacity": float(own_sqft//300)}
        
        #Calc rent sqft
        rent_budget = ratio_dict["Housing"]["dollar_budget"]/12
        rent_sqft = rent_budget/rent_cost_per_sqft
        housing_rent = {"rent_sqft": int(rent_sqft), "rent_person_capacity": float(rent_sqft//300)}
        return housing_own, housing_rent
        
    def _calc_mrtg(self, annual_housing_budget, mrtg_int):
        pmt = annual_housing_budget/12
        return np.pv(mrtg_int/12, 360, -pmt)
        
        

if __name__ == "__main__":
    base_ce_path = "data/bls_ce/msa"
    base_zil_path = "data/zillow/city"
    base_tax_path = "data/state_tax"

    calculator = COLCalculator(base_zil_path,base_ce_path,base_tax_path)

    calculator.calculate(100000, "San Francisco", "CA")

