#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : klaviyo.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 01/02/24 2:54 pm
"""
from os import getenv, path
from requests import Session
from typing import Tuple, Optional
from simplejson import dumps
from logging import Formatter, Logger
from logging.handlers import RotatingFileHandler
from time import sleep
# custom modules
from app import app
from app.utils.base import fn_debug


class KlaviyoHelper(object):
    def __init__(self, log_name: str = 'klaviyo_helper', api_token: str = None) -> None:
        # Klaviyo Token
        token = api_token if api_token else getenv('KLAVIYO_PRIVATE_KEY', None)
        if not token:
            raise Exception('Klaviyo Token is not set up yet!')
        self.logger = Logger('KlaviyoHelper')
        # Logger
        self.logger = Logger('BasicHelper')
        handler = RotatingFileHandler(
            path.join(app.config.get('TEMPORARY_PATH'), f'{log_name}.log'),
            maxBytes=5120000,
            backupCount=5
        )
        handler.setFormatter(Formatter('[%(asctime)s] %(threadName)s %(levelname)s:%(message)s'))
        if app.config.get('FLASK_DEBUG', '1') == '1':
            level = 'DEBUG'
            self.logger.addHandler(app.logger.handlers[0])
        else:
            level = 'INFO'
        handler.setLevel(level)
        self.logger.addHandler(handler)
        self._client = None
        # Custom variables
        self.token = token
        self.version = '2025-07-15'
        self.client = Session()
        self.client.headers.update({
            "Authorization": "Klaviyo-API-Key {}".format(token),
            "revision": self.version
        })
        self._url = 'https://a.klaviyo.com/api'

    @property
    def url(self) -> str:
        return self._url

    @fn_debug
    def create_event(self, data: dict, attempt: int = 5) -> bool:
        func = self.create_event.__name__
        res = self.client.post(f'{self._url}/events/', json=data)
        if res.status_code not in [200, 201, 202]:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.create_event(data, attempt - 1)
            return False
        return True

    @fn_debug
    def search_profile(self, email: str, attempt: int = 3) -> Tuple[bool, Optional[str]]:
        # https://developers.klaviyo.com/en/reference/get_profiles
        func = self.search_profile.__name__
        params = {'page[size]': 1, 'filter': f'equals(email,"{email}")'}
        res = self.client.get(f'{self._url}/profiles/', params=params)
        if res.status_code != 200:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.search_profile(email, attempt - 1)
            return False, 'Klaviyo Search Profile API Error'
        res = res.json()['data']
        if len(res) == 0:
            self.logger.debug('Func: {}. {} do not exists'.format(func, email))
            return True, None
        return True, res[0]['id']

    @fn_debug
    def update_profile(self, profile_id: str, params: dict, attempt: int = 5) -> bool:
        # https://developers.klaviyo.com/en/reference/update_profile
        func = self.update_profile.__name__
        res = self.client.patch(f'{self._url}/profiles/{profile_id}', json=params)
        if res.status_code != 200:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                sleep(1)
                return self.update_profile(profile_id, params, attempt - 1)
            return False
        return True

    @fn_debug
    def create_profile(self, params: dict, attempt: int = 3) -> Tuple[bool, Optional[str]]:
        # https://developers.klaviyo.com/en/reference/create_profile
        func = self.create_profile.__name__
        res = self.client.post(f'{self._url}/profiles', json=params)
        if res.status_code != 201:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.create_profile(params, attempt - 1)
            return False, res.text
        return True, res.json()

    @fn_debug
    def subscribe_profile(self, unique_id: str, list_id: str, email: str, attempt: int = 3) \
            -> Tuple[bool, Optional[str]]:
        # https://developers.klaviyo.com/en/reference/subscribe_profiles
        func = self.subscribe_profile.__name__
        params = dict(data=dict(
            type='profile-subscription-bulk-create-job',
            attributes=dict(
                list_id=list_id,
                custom_source="Marketing Event",
                subscriptions=[dict(
                    channels=dict(email=['MARKETING']),
                    profile_id=unique_id,
                    email=email
                )]
            )
        ))
        res = self.client.post(f'{self._url}/profile-subscription-bulk-create-jobs', json=params)
        if res.status_code != 202:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.subscribe_profile(unique_id, list_id, email, attempt - 1)
            return False, res.text
        return True, None

    @fn_debug
    def suppress_profile(self, email: str, attempt: int = 3) -> Tuple[bool, Optional[str]]:
        """ Not accept marketing email """
        # https://developers.klaviyo.com/en/reference/suppress_profiles
        func = self.suppress_profile.__name__
        params = dict(data=dict(
            type='profile-suppression-bulk-create-job',
            attributes=dict(
                profiles=dict(
                    data=[dict(
                        type='profile',
                        attributes=dict(email=email)
                    )]
                ),
            )
        ))
        self.logger.debug('Func: {}, Data: {}'.format(func, dumps(params)))
        res = self.client.post(f'{self._url}/profile-suppression-bulk-create-jobs', json=params)
        if res.status_code != 202:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.suppress_profile(email, attempt - 1)
            return False, res.text
        return True, None

    @fn_debug
    def unsuppress_profile(self, email: str, attempt: int = 3) -> Tuple[bool, Optional[str]]:
        """ Accept marketing email """
        # https://developers.klaviyo.com/en/reference/unsuppress_profiles
        func = self.unsuppress_profile.__name__
        params = dict(data=dict(
            type='profile-suppression-bulk-delete-job',
            attributes=dict(
                profiles=dict(
                    data=[dict(
                        type='profile',
                        attributes=dict(email=email)
                    )]
                ),
            )
        ))
        self.logger.debug('Func: {}, Data: {}'.format(func, dumps(params)))
        res = self.client.post(f'{self._url}/profile-suppression-bulk-delete-jobs', json=params)
        if res.status_code != 202:
            self.logger.warning('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.unsuppress_profile(email, attempt - 1)
            return False, res.text
        return True, None

    @fn_debug
    def add_profile_to_list(self, unique_id: str, list_id: str, attempt: int = 3) -> Tuple[bool, Optional[str]]:
        # https://developers.klaviyo.com/en/reference/create_list_relationships
        func = self.add_profile_to_list.__name__
        params = dict(data=[dict(
            type='profile',
            id=unique_id
        )])
        res = self.client.post(f'{self._url}/lists/{list_id}/relationships/profiles/', json=params)
        if res.status_code != 204:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.add_profile_to_list(unique_id, list_id, attempt - 1)
            return False, res.text
        return True, res.text

    @fn_debug
    def get_profile_lists(self, unique_id: str, attempt: int = 3) -> Tuple[bool, Optional[str]]:
        # https://developers.klaviyo.com/en/reference/get_profile_lists
        func = self.get_profile_lists.__name__
        res = self.client.get(f'{self._url}/profiles/{unique_id}/lists/')
        if res.status_code != 200:
            self.logger.error('Func: {}, Error: {}'.format(func, res.text))
            if attempt > 0:
                self.logger.warning('Func: {}, Retry: {}'.format(func, attempt))
                return self.get_profile_lists(unique_id, attempt - 1)
            return False, res.text
        return True, res.json()


__all__ = KlaviyoHelper
