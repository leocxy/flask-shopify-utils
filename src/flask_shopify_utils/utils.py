#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : utils.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 3:16 pm
"""
from os import environ
from datetime import datetime
from time import sleep
from sgqlc.operation import Operation
from sgqlc.endpoint.http import HTTPEndpoint
from urllib.error import HTTPError, URLError
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def get_version(version: str = None) -> str:
    """ Get Shopify API Version """
    # Get Latest version of GraphQL
    today = datetime.today()
    month = int(today.strftime('%-m'))
    for v in [10, 7, 4, 1]:
        if month >= v:
            month = v
            break
    latest_version = int('{}{:02d}'.format(today.strftime('%Y'), month))
    version = environ.get('API_VERSION', '2023-04') if not version else version
    if version:
        version = int(version.replace('-', ''))
        # check version exists or not
        if version > latest_version:
            version = latest_version
        else:
            # Check deprecate
            if latest_version - 100 > version:
                version = latest_version
    else:
        version = latest_version
    version = str(version)
    version = '{}-{}'.format(version[:4], version[-2:])
    # Set Environment variable
    environ['API_VERSION'] = version
    return version


class GraphQLClient:
    def __init__(self, app_url: str, token: str, timeout: int = 15, cost_debug: bool = False):
        self.version = get_version()
        self.timeout = timeout
        self.url = f'https://{app_url}/admin/api/{self.version}/graphql.json'
        self.headers = {'X-Shopify-Access-Token': token}
        if cost_debug:
            self.headers['Shopify-GraphQL-Cost-Debug'] = 1
        self._client = HTTPEndpoint(self.url, self.headers, timeout)

    @property
    def client(self):
        return self._client

    def fetch_data(self, query: Operation, timeout: int = None, attempts: int = 5):
        try:
            result = self.client(query, timeout=timeout if timeout else self.timeout)
            if 'errors' in result.keys():
                if result['errors'][0]['message'] == 'Throttled':
                    if attempts <= 0:
                        raise Exception(result)
                    sleep(2)
                    attempts -= 1
                    return self.fetch_data(query, timeout, attempts)
                raise Exception(result)
            else:
                return result['data']
        except (HTTPError, URLError) as e:
            if attempts <= 0:
                raise e
            sleep(1)
            attempts -= 1
            return self.fetch_data(query, timeout, attempts)


def initial_restful_adapter() -> HTTPAdapter:
    """
    Initial RestfulAPI Adapter
    Usually used for Shopify RestfulAPI
    Have a better retry for concurrency requests
    """
    Retry.parse_retry_after = lambda self, retry_after: float(retry_after)
    return HTTPAdapter(max_retries=Retry(
        total=5,
        status_forcelist=[429],
        respect_retry_after_header=True
    ))
