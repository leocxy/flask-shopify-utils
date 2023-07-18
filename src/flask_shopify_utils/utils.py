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


def get_version(version: str = None, restful: bool = False) -> str:
    """ Get Shopify API Version """
    from shopify import ApiVersion
    # Get Latest version of GraphQL
    today = datetime.today()
    month = int(today.strftime('%-m'))
    for v in [10, 7, 4, 1]:
        if month >= v:
            month = v
            break
    latest_version = int('{}{:02d}'.format(today.strftime('%Y'), month))
    if not version:
        version = environ.get('API_VERSION', '2023-04')
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
    if restful:
        versions = list(ApiVersion.versions.keys())
        # unstable version
        if version not in versions:
            version = versions[0]
    return version


class GraphQLClient:
    def __init__(self, app_url: str, token: str, timeout: int = 15):
        self.version = get_version()
        self.timeout = timeout
        self.url = f'https://{app_url}/admin/api/{self.version}/graphql.json'
        self.headers = {'X-Shopify-Access-Token': token}
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


def patch_shopify_with_limits() -> None:
    """
    Patch Shopify API with limits thresholds
    :return:
    """
    from shopify.base import ShopifyConnection
    from pyactiveresource.connection import ClientError
    func = ShopifyConnection._open

    def patched_open(self, *args, **kwargs):
        while True:
            try:
                return func(self, *args, **kwargs)
            except ClientError as e:
                if e.response.code == 429:
                    retry_after = float(e.response.headers.get('Retry-After', 4))
                    print('Service exceeds Shopify API call limit, '
                          'will retry to send request in %s seconds' % retry_after)
                    sleep(retry_after)
                else:
                    raise e

    ShopifyConnection._open = patched_open
