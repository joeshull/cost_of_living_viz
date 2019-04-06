import os
import numpy as np
import pdb
import json


from flask import Flask, redirect, url_for, request, jsonify

from calculator import COLCalculator
from dataloader import COLDataLoader
from colgeocoder import COLGeoUtil


#define app
app = Flask(__name__)


base_ce_path = 'data/bls_ce/msa'
base_zil_path = 'data/zillow/city'
base_tax_path = 'data/state_tax'
calculator = COLCalculator(base_zil_path, base_ce_path, base_tax_path)



def get_predictions(request_dict):
	return calculator.calculate(**request_dict)



@app.route('/', methods=['POST'])
def upload():
    # Get the file from post request
    file = request.data


    request_dict = json.loads(file)
    # Process your result for human
    res_dict = get_predictions(request_dict)
    return jsonify(json.dumps(res_dict))

if __name__ == '__main__':
    app.run(host= "0.0.0.0",port=8080, debug=True)