
import geocoder
import os
import requests
import numpy as np

class COLGeoUtil():
    def __init__(self, API_KEY = os.environ['GMAP_API_KEY']):
        self.API_KEY = API_KEY
        
    def geocode_one(self, city_state, session1, session2):
        #Inputs:
        #city_state (array-like): contains str(city) and str(state abbreviation)
        #session (requests.Session()): an instantiated session from the requests,  modeule.
        x = city_state[0] + ', ' + city_state[1]
        
        print("getting place id for", x)
        #Fetch ID from Places API
        try:
            places_url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
            places_params = { 'input': x, 'key': self.API_KEY, 'types': 'geocode'}
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
            return np.array([lat, lng])
        except:
            return np.array([0, 0])
    
    def get_closest_index(self, lat_lng_series, ref_lat_lng):
        #returns index of closest value in lat_lng_series
        #Inputs:
        #lat_lng_series (pandas series): contains numpy arrays of lat,long points
        #ref_lat_lng (array): contains lat,long of reference city
        
        dist = np.linalg.norm(np.vstack(lat_lng_series.values) - ref_lat_lng, axis=1)
        return np.argmax(dist)
    
    def geocode_dataframe(self, df, city_col, state_col, session1, session2, lat_lng_col='lat_lng'):
        try:
            df.drop(columns=[lat_lng_col])
            df.insert(1,lat_lng_col, 0)
        except:
            df.insert(1,lat_lng_col, 0)
        df[lat_lng_col] = df.loc[:,[city_col, state_col]].apply(self.geocode_one, axis=1, args=(session1,session2,))
        return df
        

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
        