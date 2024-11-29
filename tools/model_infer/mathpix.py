#!/usr/bin/env python3

import os
import base64
import requests
import json
import ssl

#
# Common module for calling Mathpix OCR service from Python.
#
# N.B.: Set your credentials in environment variables APP_ID and APP_KEY,
# either once via setenv or on the command line as in
# APP_ID=my-id APP_KEY=my-key python3 simple.py 
#

env = os.environ

default_headers = {
    'app_id': env.get('APP_ID', 'trial'),
    'app_key': env.get('APP_KEY', 'xxx'),
    'Content-type': 'application/json'
}

service_latex = 'https://api.mathpix.com/v3/latex'
servive_text = 'https://api.mathpix.com/v3/text'
service_pdf = 'https://api.mathpix.com/v3/pdf'

#
# Return the base64 encoding of an image with the given filename.
#
def image_uri(filename):
    image_data = open(filename, "rb").read()
    return "data:image/jpg;base64," + base64.b64encode(image_data).decode()

#
# Call the Mathpix service with the given arguments, headers, and timeout.
#
def latex(args, headers=default_headers, timeout=30):
    r = requests.post(service_latex,
        data=json.dumps(args), headers=headers, timeout=timeout)
    return json.loads(r.text)

def text(args, headers=default_headers, timeout=30):
    r = requests.post(servive_text,
        data=json.dumps(args), headers=headers, timeout=timeout, verify=ssl.CERT_NONE)
    return json.loads(r.text)

def pdf(args, file, headers=default_headers, timeout=1000):
    r = requests.post(service_pdf, data={"options_json": json.dumps(args)},
                      files={"file": file}, headers=headers, timeout=timeout)
    return json.loads(r.text)

# def text(args, headers=default_headers, timeout=30):
#     r = requests.post(servive_text,
#         data=json.dumps(args), headers=headers, timeout=timeout)
#     return json.loads(r.text)