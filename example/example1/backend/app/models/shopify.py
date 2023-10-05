#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : shopify.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 6/10/23 12:06 pm

Here is an example how to inject function to Store model, since python 3.12, we should do this in another way
"""
from flask_shopify_utils.model import Store
from json import loads, dumps


def set_extra(self, data: dict) -> None:
    extra = self.get_extra()
    extra.update(data)
    self.extra = dumps(extra)


Store.get_extra = lambda self: loads(self.extra) if self.extra else {}
Store.set_extra = set_extra
