# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Mai Xuan Trang
#   

from __future__ import print_function

import requests

try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
    from urllib.parse import urlencode
except ImportError:
    from urlparse import urlparse
    from urllib2 import urlopen
    from urllib import urlencode

try:
    import json
except ImportError:
    # Older versions of Python (i.e. 2.4) require simplejson instead of json
    import simplejson as json

class YahooAPI:
    # Setup the endpoints
    ENDPOINTS = {}
    ENDPOINTS['dependency'] = '/DAService/V1/parse'
    ENDPOINTS['keyphrases'] = '/KeyphraseService/V1/extract'

    # The base URL for all endpoints
    BASE_URL = 'http://jlp.yahooapis.jp'

    s = requests.Session()
    
    def __init__(self, key):
        import sys
        if len(key) != 56:
            # Key should be exactly 56 characters long
            print('It appears that the key in azure_api_key.txt is invalid. Please make sure the file only includes the API key, and it is the correct one.')
            sys.exit(0)
        else:
            # setup the key
            self.apikey = key

    def keyphrases(self, data):
        """
        Extracts the KeyPhrases from text

        INPUT:
        data -> the data to analyze.
        options -> various parameters that can be used to adjust how the API works.

        OUTPUT:
        The response, already converted from JSON to a Python object. 
        """
        return self.__analyze(YahooAPI.ENDPOINTS['keyphrases'], data)


    def __analyze(self, endpoint, data):
        """
        HTTP Request wrapper that is called by the endpoint functions. This function is not intended to be called through an external interface. 
        It makes the call, then converts the returned JSON string into a Python object. 

        INPUT:
        url -> the full URI encoded url

        OUTPUT:
        The response, already converted from JSON to a Python object. 
        """


        url = YahooAPI.BASE_URL + endpoint
        params = urlencode({'appid':self.apikey, 'output':'json'})
        post_url = url + '?' + params
        post_data = {'sentence':data}
        json_date = json.dumps(post_data)
        try:
            result = self.s.post(url=post_url, data=post_data)
        except Exception as e:
            print(e)
            return {'status': 'ERROR', 'statusInfo': e} 
        try:
            return result.json()
        except Exception as e:
            print(e)
            return {'status': 'ERROR', 'message': e}
