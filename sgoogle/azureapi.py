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

class AzureAPI:
    # Setup the endpoints
    ENDPOINTS = {}
    ENDPOINTS['sentiment'] = '/sentiment'
    ENDPOINTS['keyphrases'] = '/keyPhrases'
    ENDPOINTS['languages'] = '/languages'

    # The base URL for all endpoints
    BASE_URL = 'https://westus.api.cognitive.microsoft.com/text/analytics/v2.0'

    s = requests.Session()

    def __init__(self, key):
        import sys
        if len(key) != 32:
            # Keys should be exactly 32 characters long
            print('It appears that the key in azure_api_key.txt is invalid. Please make sure the file only includes the API key, and it is the correct one.')
            sys.exit(0)
        else:
            # setup the key
            headers = {"Ocp-Apim-Subscription-Key":key, "Content-Type":"application/json", "Accept": "application/json"}
            self._req_args = {'headers':headers}

    def keyphrases(self, lang, data):
        """
        Extracts the KeyPhrases from text

        INPUT:
        data -> the data to analyze.
        options -> various parameters that can be used to adjust how the API works.

        OUTPUT:
        The response, already converted from JSON to a Python object. 
        """
        return self.__analyze(AzureAPI.ENDPOINTS['keyphrases'], lang, data)


    def __analyze(self, endpoint, lang, datas):
        """
        HTTP Request wrapper that is called by the endpoint functions. This function is not intended to be called through an external interface. 
        It makes the call, then converts the returned JSON string into a Python object. 

        INPUT:
        url -> the full URI encoded url

        OUTPUT:
        The response, already converted from JSON to a Python object. 
        """


        post_url = AzureAPI.BASE_URL + endpoint
        documents = []
        id = 1
        for data in datas:
            if data != '':
                document = {"language":lang, "id":id, "text":data}
                documents.append(document)
                id += 1
        post_data = {"documents":documents}
        json_data = json.dumps(post_data)
        try:
            results = self.s.post(url=post_url, data=json_data, **self._req_args)
        except Exception as e:
            print(e)
            return {'status': 'ERROR', 'statusInfo': 'network-error'}
        try:
            return results.json()
        except Exception as e:
            if results != "":
                print(results)
            print(e)
            return {'status': 'ERROR', 'statusInfo': 'parse-error'}
