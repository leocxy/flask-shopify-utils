#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : config.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 11/09/23 9:25 am
"""
from os import getenv
from os.path import dirname, join, abspath
from pytz import timezone
from dotenv import load_dotenv

ROOT_PATH = abspath(dirname(dirname(dirname(__file__))))
"""
ROOT_PATH should be the root path of your project
But it might be overwritten by uwsgi config
double check the path and remove the '/backend' from the path
"""
if ROOT_PATH.endswith('/backend'):
    ROOT_PATH = ROOT_PATH[:-8]
load_dotenv(dotenv_path=join(ROOT_PATH, '.env'))


class Config:
    DEBUG = False
    TESTING = False
    CSRF_ENABLE = True
    SECRET_KEY = getenv('SECRET_KEY', 'your-flask-application-secret-key')
    SERVER_NAME = getenv('SERVER_NAME')
    # Flask-Shopify-Utils
    ROOT_PATH = ROOT_PATH
    BACKEND_PATH = join(ROOT_PATH, 'backend')
    TEMPORARY_PATH = join(BACKEND_PATH, 'tmp')
    TIMEZONE = timezone(getenv('TIMEZONE', 'Pacific/Auckland'))
    BYPASS_VALIDATE = int(getenv('BYPASS_VALIDATE', 0))
    SHOPIFY_API_KEY = getenv('SHOPIFY_API_KEY')
    SHOPIFY_API_SECRET = getenv('SHOPIFY_API_SECRET')
    SCOPES = getenv('SCOPES')
    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = getenv('DATABASE_URL', 'sqlite:///' + join(BACKEND_PATH, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
