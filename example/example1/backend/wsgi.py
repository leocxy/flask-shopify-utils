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
    if port and getenv('FLASK_ENV') == 'development':
        app.run(port=int(port))
    else:
        app.run()

