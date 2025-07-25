#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : wsgi.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 11/09/23 9:24 am
"""
from app import create_app
from os import getenv

app = create_app()

if __name__ == '__main__':
    # Run
    port = getenv('BACKEND_PORT')
    # generated from shopify cli
    host = getenv('HOST')
    if host and port and getenv('FLASK_ENV') == 'development':
        app.config['SERVER_NAME'] = host.replace('https://', '')
        app.run(port=int(port), host='127.0.0.1')
    else:
        app.run()
