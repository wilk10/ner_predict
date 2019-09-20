import os
import requests
import urllib.parse


class Apis:
    URL_BY_API = {
        'eppo': 'https://data.eppo.int/api/rest/1.0/tools/search',
        'cat_life': 'http://webservice.catalogueoflife.org/col/webservice'}
    MSG = 'please add your EPPO API token to your virtual environment:\nexport EPPO_TOKEN=[your token]'

    def __init__(self):
        self.token = os.getenv('EPPO_TOKEN', '')
        assert self.token, self.MSG

    @staticmethod
    def check_eppo_response(response):
        if isinstance(response, list) and not response:
            result = None
        elif isinstance(response, list) and isinstance(response[0], dict):
            result = response
        elif isinstance(response, dict):
            result = None
        else:
            result = response
        return result

    def call(self, api, entity):
        assert api in self.URL_BY_API.keys()
        if api == 'eppo':
            params = {'authtoken': self.token, 'kw': entity, 'searchfor': 3, 'searchmode': 1, 'typeorg': 1}
        else:
            params = {'name': entity, 'format': 'json'}
        parsed_params = urllib.parse.urlencode(params)
        url = self.URL_BY_API[api]
        if len(entity) >= 3:
            response = requests.get(url, params=parsed_params, timeout=10).json()
            if api == 'eppo':
                response = self.check_eppo_response(response)
        else:
            response = None
        return response
