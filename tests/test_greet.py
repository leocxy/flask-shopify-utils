#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_greet.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 26/05/23 1:44 pm
"""
from flask_shopify_utils import greet


def test_greet() -> None:
    assert greet('Leo') == 'Hello Leo'
