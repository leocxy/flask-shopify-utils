#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : utils.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 3:16 pm
"""
from re import match as re_match
from os import environ
from datetime import datetime
from dateutil.relativedelta import relativedelta
from time import sleep
from sgqlc.operation import Operation
from sgqlc.endpoint.http import HTTPEndpoint
from urllib.error import HTTPError, URLError
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Tuple, Union

VERSION_KEY = 'API_VERSION'


def get_version(version: str = None) -> str:
    """ Get Shopify API Version """
    # Get Latest version of GraphQL
    today = datetime.today()
    month = int(today.strftime('%m'))
    for v in [10, 7, 4, 1]:
        if month >= v:
            month = v
            break
    latest_date = int('{}{:02d}'.format(today.strftime('%Y'), month))
    earliest_date = int('{}{:02d}'.format((today - relativedelta(years=1)).strftime('%Y'), month))
    latest_version = '{}-{:02d}'.format(today.strftime('%Y'), month)

    # validate the version format: "xxxx-xx", all digits, first digit 1-9
    force = False
    if version:
        val = version
        force = True
    else:
        val = environ.get(VERSION_KEY, '2026-04')
    if not re_match(r'^[1-9]\d{3}-\d{2}$', val):
        raise ValueError('Invalid API version format: {}'.format(val))
    val_date = int(val.replace('-', ''))

    # Check if the version is within the valid range
    if val_date > latest_date or val_date < earliest_date:
        version = latest_version if force is False else val
    else:
        version = val

    # Set Environment variable
    environ[VERSION_KEY] = version
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
    def client(self) -> HTTPEndpoint:
        return self._client

    def fetch_data(self, query: Operation, timeout: int = None, attempts: int = 5) -> Tuple[bool, Union[str, dict]]:
        timeout = self.timeout if timeout is None else timeout
        try:
            result = self.client(query, timeout=timeout)
            if 'errors' in result.keys():
                errors = result['errors']
                if isinstance(errors, str) or result.get('status') == 401:
                    return False, result
                if errors[0]['message'] == 'Throttled':
                    if attempts <= 0:
                        return False, result
                    sleep(2)
                    attempts -= 1
                    return self.fetch_data(query, timeout, attempts)
                return False, result
            else:
                return True, result['data']
        except (HTTPError, URLError) as e:
            if attempts <= 0:
                return False, str(e)
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
