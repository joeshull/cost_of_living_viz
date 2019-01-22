
import geocoder
import os
import requests
import numpy as np

class COLGeoUtil():
    def __init__(self, API_KEY = os.environ['GMAP_API_KEY']):
        self.API_KEY = API_KEY
        
    def geocode_one(self, city_state, session1=None, session2=None):
        #Inputs:
        #city_state (array-like): contains str(city) and str(state abbreviation)
        #session (requests.Session()): an instantiated session from the requests,  modeule.
        if isinstance(city_state, (list, tuple, np.ndarray)):
            x = city_state[0] + ', ' + city_state[1]
        else: 
            x = city_state
            
        if session1 is None:
            session1 = session2 = requests
        
        print("getting place id for", x)
        #Fetch ID from Places API
        try:
            places_url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
            places_params = { 'input': x, 'key': self.API_KEY, 'types': '(cities)'}
            r = session1.get(places_url, params=places_params)
            results = r.json()
            place_id = results['predictions'][0]['place_id']

            print ("getting geocode for", place_id)
            #Get Lat Lng from Geocoding API
            gc_url = 'https://maps.googleapis.com/maps/api/geocode/json'
            gc_params = {'place_id' : place_id, 'key' : self.API_KEY}
            g = session2.get(gc_url, params=gc_params)
            point = g.json()['results'][0]['geometry']['location']
            lat, lng = point['lat'], point['lng']
            return np.array([lat, lng]).astype('float32')
        except:
            return np.array([0, 0]).astype('float32')
    
    def get_closest_index(self, lat_lng_series, ref_lat_lng):
        #returns index of closest value in lat_lng_series
        #Inputs:
        #lat_lng_series (np.array): contains  lat,long points
        #ref_lat_lng (array): contains lat,long of reference city
        
        dist = np.linalg.norm(np.vstack(lat_lng_series).astype('float32') - ref_lat_lng, axis=1)
        return np.argmin(dist)
    
    def geocode_dataframe(self, df, city_col, state_col, session1, session2, lat_lng_col='lat_lng'):
        try:
            df.drop(columns=[lat_lng_col])
            df.insert(1,lat_lng_col, 0)
        except:
            df.insert(1,lat_lng_col, 0)
        df[lat_lng_col] = df.loc[:,[city_col, state_col]].apply(self.geocode_one, axis=1, args=(session1,session2,))
        return df
    
    def copy_zil_geocode(self,df_left, df_right, key_cols=['RegionName', 'State'], lat_lng_col='lat_lng'):
        #Prepare to merge only lat,lng
        merge_cols = key_cols
        merge_cols.append(lat_lng_col)
        new_df =  pd.merge(df_left, df_right.loc[:,merge_cols], how='left', on=key_cols)
        #Move lat.lng col to index 3
        feature_cols = list(new_df.columns.values)
        feature_cols.pop(-1)
        feature_cols.insert(lat_lng_col,3)
        
        return new_df.loc[:, feature_cols]
    
    def geocode_ce(self, df):
        cities = df.columns.values
        geocodes = [self.geocode_one(x) for x in cities]
#         df.loc['lat_lng'] = geocodes
        return geocodes
        
        

if __name__ == '__main__':
    base_ce_path = '../data/bls_ce/msa/'
    base_zil_path = '../data/zillow/city/'
    base_tax_path = '../data/state_tax/'
    data = COLDataLoader(base_zil_path, base_ce_path, base_tax_path)
    data.load()
    test_df = data.df_zil_own.iloc[:5,:6]

    gc = COLGeoUtil()

    with requests.Session() as session:
        test_df = gc.geocode_dataframe(test_df, 'RegionName', 'State', session)
        