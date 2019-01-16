import pandas as pd 
import numpy as np 
from dataloader import COLDataLoader

class COLCalculator():
    #Cost of Living Calculator
    #Instantiate with the path to the Zillow city csvs and Consumer Expenditure xlsxs
    def __init__(self, zillow_path, ce_path):
        self.data = COLDataLoader(zillow_path, ce_path)
        data.load()
        
    def calculate(self, gross_income, city, state, married=False):
        #Calculation function: returns a dict (or json) with the following values
        #income_taxes (Tuple): (Float: Approx amount of taxes paid, Float: Approx. Effective Tax Rate)
        #housing_rent (Tuple): (Int: sqft affordable at the housing % ratio, Float: Ratio of housing/income)
        #housing_own (Tuple): (Int: sqft affordable at the housing % ratio, Float: Ratio of housing/income)
        tax_amount, tax_rate, net_income = self._get_taxes(gross_income, city, state, married)
        housing_rent, housing_own = self._get_housing(gross_income, city, state)
    
    # Tax Calculation  - Federal and State
    def _get_taxes(self, gross_income, city, state, married):
        #returns tax amount, tax %, and net income
        fed_tax, fed_rate = self._calc_fed_tax(gross_income, married)
        state_tax, state_rate = self._calc_state_tax(gross_income, state, married)

        total_tax = fed_tax + fed_rate
        net_income = gross_income - total_tax
        effective_tax = total_tax/gross_income

        return total_tax, effective_tax, net_income


    
    def _calc_fed_tax(self, gross_income, married):
        #tax withholding from https://www.irs.gov/pub/irs-pdf/n1036.pdf
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

        if mask.any():
            threshold, base_tax, rate = rate[mask][0][0], rate[mask][0][1], rate[mask][0][2]
            return ((base_tax + (gross_income-threshold)*rate), rate)
        else:
            return 0
        
    def _calc_state_tax(self, gross_income, state, married):
        #Tax rates from https://github.com/TaxFoundation/facts-and-figures


        pass 
    
    def _get_housing(self, gross_income, city):
        #Returns two tuples
        #housing_rent (Tuple): (Int: sqft affordable at the housing % ratio, Float: Ratio of housing/income)
        #housing_own (Tuple): (Int: sqft affordable at the housing % ratio, Float: Ratio of housing/income)
        pass
    
    def _get_transporation(self, gross_income, city):
        #Returns amount of transportation ?
        pass
    
    def _get_lifestyle(self, gross_income, city):
        pass
    
    def _get_savings(self, gross_income, city):
        pass
        

if __name__ == '__main__':
    calculator = COLCalculator(base_zil_path, base_ce_path):
    print(calculator.calculate(100000, 'San Francisco', 'CA'))