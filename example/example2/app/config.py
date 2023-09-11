#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : config.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 19/07/23 2:21 pm
"""
from os import environ
from os.path import dirname, join, abspath
from pytz import timezone
from dotenv import load_dotenv

ROOT_PATH = abspath(dirname(dirname(__file__)))
load_dotenv(dotenv_path=join(ROOT_PATH, '.env'))


class Config:
    # Flask
    DEBUG = False
    TESTING = False
    CSRF_ENABLE = True
    SECRET_KEY = environ.get('SECRET_KEY', 'your-flask-application-secret-key')
    SERVER_NAME = environ.get('SERVER_NAME')
    # Flask-Shopify-Utils
    ROOT_PATH = ROOT_PATH
    TEMPORARY_PATH = join(ROOT_PATH, 'tmp')
    TIMEZONE = timezone('Pacific/Auckland')
    BYPASS_VALIDATE = 0
    SHOPIFY_API_KEY = environ.get('SHOPIFY_API_KEY')
    SHOPIFY_API_SECRET = environ.get('SHOPIFY_API_SECRET')
    SCOPES = environ.get('SCOPES')
    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL', 'sqlite:///' + join(ROOT_PATH, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False