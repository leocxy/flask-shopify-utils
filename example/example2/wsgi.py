#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : wsgi.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 19/07/23 2:20 pm
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
