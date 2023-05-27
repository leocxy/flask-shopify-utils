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
from shopify import ApiVersion


def get_version(version: str = None, restful: bool = False) -> str:
    """ Get Shopify API Version """
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
