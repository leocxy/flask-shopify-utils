#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : __init__.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 26/05/23 1:43 pm
"""
from os import path, getcwd, environ
from sys import exc_info
from typing import Optional, Callable, Tuple, TypeVar
from time import time
from hashlib import sha256
from functools import wraps, partial
from hmac import new as hmac_new, compare_digest
from datetime import datetime, timedelta
from uuid import uuid4
from requests import post as post_request
from urllib.parse import urlencode
from base64 import b64encode
from contextlib import contextmanager
# Third-party Library
from flask import Flask, request, g, jsonify, Response, current_app, Blueprint, redirect, render_template, \
    make_response, url_for
from jinja2 import TemplateNotFound
from jwt import encode as jwt_encode, decode as jwt_decode, ExpiredSignatureError
from cerberus.validator import Validator
from pytz import timezone
from flask_shopify_utils.utils import get_version, GraphQLClient

__version__ = '0.2.2'

JWT_DATA = TypeVar('JWT_DATA', dict, Response)
current_time_func = None
sqlalchemy_instance = None


class ShopifyUtil:
    """ Shopify Utils """

    def __init__(self, app: Optional[Flask] = None, config: dict = None) -> None:
        if not (config is None or isinstance(config, dict)):
            raise ValueError("`config` must be an instance of dict or None")
        self._config = config
        self._app = None
        self._db = None
        if app is not None:
            self.init_app(app, config)

    @property
    def config(self):
        return self._config

    @property
    def app(self):
        if self._app is None:
            return current_app
        return self._app

    @property
    def db(self):
        return self._db.session

    def init_app(self, app: Flask, config: dict = None) -> None:
        """ This is used to initialize your app object """
        if not (config is None or isinstance(config, dict)):
            raise ValueError("`config` must be an instance of dict or None")
        base_config = app.config.copy()
        if self.config:
            base_config.update(self.config)
        if config:
            base_config.update(config)

        config = base_config
        config.setdefault('ROOT_PATH', getcwd())
        config.setdefault('BACKEND_PATH', path.join(config.get('ROOT_PATH'), 'backend'))
        config.setdefault('TEMPORARY_PATH', path.join(config.get('BACKEND_PATH'), 'tmp'))
        config.setdefault('API_VERSION', get_version())
        config.setdefault('TIMEZONE', timezone('Pacific/Auckland'))
        config.setdefault('SHOPIFY_API_SECRET', 'CUSTOM_APP_SECRET')
        config.setdefault('SHOPIFY_API_KEY', 'CUSTOM_APP_KEY')
        config.setdefault('BYPASS_VALIDATE', 0)
        config.setdefault('DEBUG', False)
        config.setdefault('SCOPES', environ.get('SCOPES', 'read_products'))

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions.setdefault('shopify_utils', self)

        # Check SQLAlchemy is initialized
        self._db = app.extensions.get('sqlalchemy', None)
        if self._db is None:
            raise Exception('Please initialize SQLAlchemy before using ShopifyUtils.')
        global sqlalchemy_instance, current_time_func
        # Initial the global data
        sqlalchemy_instance = self._db if sqlalchemy_instance is None else sqlalchemy_instance
        current_time_func = self.current_time if current_time_func is None else current_time_func

        # Set internal variables
        self._config = config
        self._app = app

    def current_time(self):
        return datetime.now(self.config.get('TIMEZONE'))

    def validate_hmac(self, params: dict) -> str:
        def calculate(params: dict):
            def encode_pairs(params: dict):
                for k, v in params.items():
                    if k == 'hmac':
                        continue
                    k = str(k).replace('%', '%25').replace('=', '%3D')
                    v = str(v).replace('%', '%25')
                    yield '{}={}'.format(k, v).replace('&', '%26')

            return '&'.join(sorted(encode_pairs(params)))

        secret = self.config.get('SHOPIFY_API_SECRET') if self.config else 'SHOPIFY_API_SECRET'
        return hmac_new(secret.encode(), calculate(params).encode(), sha256).hexdigest()

    def validate_proxy(self) -> bool:
        signature = request.args.get('signature', '')
        params = dict((key, value) for key, value in request.args.items() if key != 'signature')
        query = ''
        for key in sorted(params):
            query += '{}={}'.format(key, params[key].join(',') if isinstance(params[key], list) else params[key])
        secret = self.config.get('SHOPIFY_API_SECRET') if self.config else 'SHOPIFY_API_SECRET'
        return compare_digest(signature, hmac_new(secret.encode('utf-8'), query.encode('utf-8'), sha256).hexdigest())

    def validate_webhook(self) -> bool:
        signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
        data = request.get_data()
        secret = self.config.get('SHOPIFY_API_SECRET', 'SHOPIFY_API_SECRET')
        value = b64encode(hmac_new(secret.encode('utf-8'), data, sha256).digest())
        return compare_digest(signature.encode('utf-8'), value)

    def validate_jwt(self) -> Tuple[bool, JWT_DATA]:
        token = request.headers.get('Authorization', '')
        try:
            res = jwt_decode(token[7:], self.config.get('SHOPIFY_API_SECRET', ''), algorithms='HS256')
        except ExpiredSignatureError:
            return False, jsonify(dict(status=401, message='Session token expired. Please refresh the page!'))
        except Exception as e:
            exc_type, exc_obj, exc_tb = exc_info()
            print(exc_type, exc_obj, exc_tb)
            return False, jsonify(dict(status=500, message=e.__str__()))
        return True, res

    def bypass_validate(self, func, args, kwargs):
        bypass = self.config.get('BYPASS_VALIDATE', 0)
        if bypass == 0:
            return False, None
        g.store_id = bypass
        g.store_key = 'local-dev-bypass.myshopify.com'
        g.jwt_expire_time = 0
        return True, func(*args, **kwargs)

    def check_callback(self, func):
        """
        Verify the callback request once the user press the `install`
        button on Admin Panel.

        :param func:
        :return: none or json
        for single endpoint use only, for example

        ```python
            from flask import Blueprint, current_app
            from flask_shopify_utils import ShopifyUtil

            utils = ShopifyUtil(current_app)

            proxy_bp = Blueprint('shopify', __init__)

            @proxy_bp.route('/callback', methods=['POST'])
            @utils.check_callback
            def callback():
                pass
        ```
        """

        @wraps(func)
        def decorator(*args, **kwargs):
            # check cookie
            state = request.cookies.get('state', None)
            if state is None or state != request.args.get('state'):
                return jsonify(dict(status=403, message='Request origin cannot be verified'))
            # check time
            if int(request.args.get('timestamp', 0)) < (time() - 86400):
                return jsonify(dict(message='The request has expired', status=401))
            if not compare_digest(
                    self.validate_hmac(request.args),
                    request.args.get('hmac', '')
            ):
                resp = jsonify(dict(message='Hmac validation failed!', status=401))
                resp.status_code = 401
                return resp
            # grab `shop` and `code` from parameters
            g.store_key = request.args.get('shop', None)
            g.code = request.args.get('code', None)
            return func(*args, *kwargs)

        return decorator

    def check_hmac(self, func):
        """
        Verify the hmac when the user trying to open the Embedded App

        :param func:
        :return: none or Response
        for single endpoint use only, for example

        ```python
            from flask import Blueprint, current_app
            from flask_shopify_utils import ShopifyUtil

            utils = ShopifyUtil(current_app)

            proxy_bp = Blueprint('shopify', __init__)

            @proxy_bp.route('/callback', methods=['POST'])
            @utils.check_hmac
            def index():
                pass
        """

        @wraps(func)
        def decorator(*args, **kwargs):
            params = request.args
            if len([x for x in params.keys() if x in ['shop', 'hmac', 'host', 'timestamp', 'session']]) < 4:
                # Redirect to the Docs page
                return redirect(url_for('docs_default.index'))
            # Check timestamp
            timestamp1 = int(request.args.get('timestamp', '0'))
            timestamp2 = int(time()) - 86400
            if timestamp1 < timestamp2:
                resp = self.proxy_response(401, 'The request has expired')
                resp.status_code = 401
                return resp
            # Check Hmac
            if not compare_digest(
                    self.validate_hmac(params),
                    request.args.get('hmac', '')
            ):
                resp = self.proxy_response(401, 'Invalid HMAC')
                resp.status_code = 401
                return resp
            g.store_key = params['shop']
            g.host = params['host']
            return func(*args, **kwargs)

        return decorator

    def check_proxy(self, func) -> Callable:
        """

        :param func:
        :return: none or json
        for single endpoint use only, for example

        ```python
            from flask import Blueprint, current_app
            from flask_shopify_utils import ShopifyUtil

            utils = ShopifyUtil(current_app)

            proxy_bp = Blueprint('proxy_bp', __init__, url_prefix='proxy')

            @proxy_bp.route('/', methods=['POST'])
            @utils.check_proxy
            def proxy_function():
                pass
        ```
        """

        @wraps(func)
        def decorator(*args, **kwargs):
            # bypass validation
            bypass, resp = self.bypass_validate(func, args, kwargs)
            if bypass:
                return resp
            if not self.validate_proxy():
                resp = jsonify(dict(
                    message='Proxy validation failed!',
                    headers=dict(request.headers),
                    params=request.args,
                    status=401,
                ))
                resp.status_code = 401
                return resp

            # grab `shop` from parameters
            g.store_key = request.args.get('shop', None)
            from flask_shopify_utils.model import Store
            store = Store.query.filter_by(key=g.store_key).first()
            if store is None:
                resp = self.proxy_response(401, 'Store[{}] does not exists!'.format(g.store_key))
                resp.status_code = 401
                return resp
            g.store_id = store.id
            return func(*args, **kwargs)

        return decorator

    def check_webhook(self, func):
        """
        :param func:
        :return: none or json
        For single endpoint use only, for example

        ```python
            from flask import Blueprint, current_app
            from flask_shopify_utils import ShopifyUtil

            utils = ShopifyUtil(current_app)

            webhook_bp = Blueprint('webhook_bp', __init__, url_prefix='webhook')

            @webhook_bp.route('/', methods=['POST'])
            @utils.check_webhook
            def webhook_function():
                pass
        ```
        """

        @wraps(func)
        def decorator(*args, **kwargs):
            # bypass validation
            bypass, resp = self.bypass_validate(func, args, kwargs)
            if bypass:
                return resp
            if not self.validate_webhook():
                resp = jsonify(dict(message='Hmac validation failed!', status=401))
                resp.status_code = 401
                return resp
            # grab `shop` from header
            g.store_key = request.headers.get('X-Shopify-Shop-Domain', None)
            return func(*args, **kwargs)

        return decorator

    def check_jwt(self, func):
        """
        All HTTPS requests from Shopify Admin UI need to be verify
        :param func:
        :return: none or json
        For single endpoint use only, for example

        ```python
            from flask import Blueprint, current_app
            from flask_shopify_utils import ShopifyUtil

            utils = ShopifyUtil(current_app)

            webhook_bp = Blueprint('admin_bp', __init__, url_prefix='admin')

            @webhook_bp.route('/', methods=['GET'])
            @utils.check_jwt
            def get_request():
                pass
        """

        @wraps(func)
        def decorator(*args, **kwargs):
            bypass, resp = self.bypass_validate(func, args, kwargs)
            if bypass:
                return resp
            rs, data = self.validate_jwt()
            if not rs:
                return data
            g.store_id = data.get('store_id')
            g.store_key = data.get('store_key')
            g.jwt_expire_time = data.get('expire_time')
            return func(*args, **kwargs)

        return decorator

    def create_admin_jwt_token(self) -> str:
        expire_time = datetime.utcnow() + timedelta(minutes=30)
        return jwt_encode(dict(
            store_id=g.store_id,
            store_key=g.store_key,
            expire_time=int(expire_time.timestamp()),
            exp=expire_time,
        ), self.config.get('SHOPIFY_API_SECRET'), algorithm='HS256')

    def admin_response(self, status: int = 0, message: str = 'success', data: dict = None) -> Response:
        """
        For Admin APIs response use only

        :param status:
        :param message:
        :param data:
        :return:
        """
        data = data if data else []
        result = dict(status=status, message=message, data=data)
        expire_time = int(datetime.utcnow().timestamp()) + 600
        if g.jwt_expire_time and expire_time >= g.jwt_expire_time:
            result['jwtToken'] = self.create_admin_jwt_token()
        return jsonify(result)

    @classmethod
    def proxy_response(cls, status: int = 0, message: str = 'success', data: dict = None) -> Response:
        """
        For proxy APIs response use only

        :param status:
        :param message:
        :param data:
        :return:
        """
        data = [] if data is None else data
        return jsonify(status=status, message=message, data=data)

    def paginate_response(self, paginate, is_admin: bool = True):
        from_num = 1 if paginate.page == 1 else (paginate.page - 1) * paginate.per_page + 1
        to_num = paginate.per_page if paginate.page == 1 else paginate.page * paginate.per_page
        data = {
            'total': paginate.total,
            'per_page': paginate.per_page,
            'current_page': paginate.page,
            'last_page': paginate.pages,
            'next_page_url': '',
            'prev_page_url': '',
            'from': from_num,
            'to': to_num,
            'data': list(map(lambda x: x.to_dict(), paginate.items))
        }
        func = self.admin_response if is_admin else self.proxy_response
        return func(data=data)

    def form_validate(self, data: dict = None, schema: dict = None, is_admin: bool = False):
        func = getattr(self, 'proxy_response' if not is_admin else 'admin_response')
        if not data or not schema:
            return False, func(400, 'Invalid JSON data')
        validator = Validator(schema)
        if not validator.validate(data):
            keys = []
            key = list(validator.errors.keys())[0]
            first_error = validator.errors[key][0]
            keys.append(str(key))
            while type(first_error) == dict:
                key = list(first_error.keys())[0]
                first_error = first_error[key][0]
                keys.append(str(key))
            first_error = '{}: {}'.format('.'.join(keys), first_error)
            status = 400
            message = first_error
            return False, func(status=status, message=message, data=validator.errors)
        return True, None

    @contextmanager
    def prevent_concurrency(self, key: str = 'main'):
        """
        Prevent concurrency request
        :param key:
        :return:
        """
        from os import getpid, remove
        from psutil import pid_exists, Process
        file_path = path.join(self.config.get('BACKEND_PATH'), 'tmp', 'worker-{}.lock'.format(key))
        try:
            if path.isfile(file_path):
                with open(file_path, 'r') as f:
                    pid = int(f.read())
                    if pid_exists(pid):
                        proc = Process(pid)
                        run_time = int(datetime.now().timestamp()) - int(proc.create_time())
                        if proc.status() == 'zombie' or run_time >= (3600 * 6):
                            proc.kill()
                        else:
                            raise RuntimeError('{}[{}] is running'.format(key, pid))
            with open(file_path, 'w+') as f:
                f.write(str(getpid()))
            yield
            remove(file_path)
        except TypeError as e:
            exc_type, exc_obj, exc_tb = exc_info()
            print(exc_type, exc_obj, exc_tb)
            raise e
        except ValueError as e:
            exc_type, exc_obj, exc_tb = exc_info()
            print(exc_type, exc_obj, exc_tb)
            raise e
        except RuntimeError as e:
            raise e
        except Exception as e:
            exc_type, exc_obj, exc_tb = exc_info()
            print(exc_type, exc_obj, exc_tb)
            raise e

    @classmethod
    def get_hash_time_format(cls, val: str):
        types = dict(monthly='%Y%m%d%H%M%SM', daily='%Y%m%d%H%M%SD', hourly='%Y%m%d%H%M%SH')
        return types.get(val, '%Y%m%d%H%M%SH')

    @classmethod
    def format_api_scopes(cls, data: list) -> str:
        scopes = {}
        xxx = 'xxx'
        for v in data:
            if 'read_' in v:
                name = v.replace('read_', xxx)
                if name not in scopes:
                    scopes[name] = 'read'
            else:
                name = v.replace('write_', xxx)
                scopes[name] = 'write'
        data = []
        for name, permission in scopes.items():
            data.append(name.replace(xxx, f'{permission}_'))
        return ','.join(data)

    def generate_internal_hash(self, value, expired_time: str = 'daily') -> str:
        """
        Generate internal hash for proxy APIs or something internal use
        :param value:
        :param expired_time: daily, hourly, monthly
        :return:
        """
        value = str(value)
        time_format = self.get_hash_time_format(expired_time)
        dynamic_value = datetime.utcnow().strftime(time_format)
        return hmac_new(
            self.config.get('SHOPIFY_API_SECRET').encode('utf-8'),
            '{}{}'.format(value, dynamic_value).encode('utf-8'),
            sha256
        ).hexdigest() + dynamic_value

    def validate_internal_hash(self, func=None, key_name: str = 'customer_id', expired_time: str = 'daily'):
        if func is None:
            return partial(self.validate_internal_hash, key_name=key_name, expired_time=expired_time)

        @wraps(func)
        def decorator(*args, **kwargs):
            token = request.args.get('hash', None)
            if not token:
                for header_name in ['Custom-Token', 'Authorization']:
                    token = request.headers.get(header_name, None)
                    if token:
                        break
            if not token:
                resp = self.proxy_response(401, '`Custom-Token` is missing from Header')
                return resp
            token = token.strip()
            if token.startswith('Bearer '):
                token = token[7:]
            value = str(kwargs.get(key_name, ''))
            dynamic_value = token[-15:]
            signature1 = token[:-15]
            signature2 = hmac_new(
                self.config.get('SHOPIFY_API_SECRET').encode('utf-8'),
                '{}{}'.format(value, dynamic_value).encode('utf-8'),
                sha256
            ).hexdigest()
            if not compare_digest(signature1, signature2):
                return self.proxy_response(401, 'Invalid `Custom-Token`')
            # check the expired time
            time_format = self.get_hash_time_format(expired_time)
            expired_type = time_format[-1:]
            created_time = datetime.strptime(dynamic_value[:-1], time_format[:-1])
            current_time = datetime.utcnow()
            duration = current_time - created_time
            # M, D, H
            if expired_type == 'M':
                if 0 < duration.days <= 30:
                    return func(*args, **kwargs)
            if expired_type == 'D':
                if 0 < duration.total_seconds() <= 86400:
                    return func(*args, **kwargs)
            if expired_type == 'H':
                if 0 < duration.total_seconds() < 3600:
                    return func(*args, **kwargs)
            return self.proxy_response(401, '`Custom-Token` is expired!')

        return decorator

    def enroll_default_route(self) -> None:
        """
        Register default Shopify routes
        """
        from flask_shopify_utils.model import Store

        static_folder = path.join(self.config.get('ROOT_PATH'), 'dist')
        doc_routes = Blueprint(
            'docs_default',
            'docs_routes',
            template_folder=static_folder,
            static_folder=path.join(static_folder, 'docs'),
        )

        @doc_routes.route('/docs', methods=['GET'])
        def index() -> Response:
            """
            Show the docs for default message
            """
            try:
                return make_response(render_template('docs/index.html'))
            except TemplateNotFound:
                return make_response('Please contact "dev@pocketsquare.co.nz" for more information.')

        default_routes = Blueprint(
            'shopify_default',
            'shopify_default_routes',
            template_folder=static_folder,
            static_folder=path.join(static_folder, 'admin'),
        )

        @self.app.errorhandler(404)
        def missing(e) -> Response:
            params = request.args
            if len([x for x in params.keys() if x in ['shop', 'hmac', 'host', 'timestamp', 'session']]) >= 4:
                # check hmac, if pass, show render the index.html
                error_redirect = redirect(url_for('shopify_default.admin', **params))
                # Check timestamp
                timestamp1 = int(request.args.get('timestamp', '0'))
                timestamp2 = int(time()) - 86400
                if timestamp1 < timestamp2:
                    return error_redirect
                # Check Hmac
                if not compare_digest(self.validate_hmac(params), request.args.get('hmac', '')):
                    return error_redirect
                g.store_key = params.get('shop', '')
                store = self.db.query(Store).filter_by(key=g.store_key).first()
                if not store:
                    return error_redirect
                g.store_id = store.id
                return make_response(render_template(
                    'admin/index.html',
                    jwtToken=self.create_admin_jwt_token()
                ))
            # redirect to the docs page
            return redirect(url_for('docs_default.index'))

        @default_routes.route('/admin', methods=['GET'], endpoint='admin')
        @self.check_hmac
        def admin() -> Response:
            # check database
            bypass = self.config.get('BYPASS_VALIDATE', 0)
            if bypass != 0:
                g.store_id = bypass
            else:
                store = self.db.query(Store).filter_by(key=g.store_key).first()
                g.store_id = store.id if store else 0
            # Render the Embedded App Index Page
            try:
                code = render_template(
                    'admin/index.html',
                    jwtToken=self.create_admin_jwt_token(),
                )
            except TemplateNotFound:
                return self.proxy_response(0, 'Oops... The `index.html` is gone!')
            return make_response(code)

        # Index Route -> redirect to Docs or Admin
        @default_routes.route('/', methods=['GET'], endpoint='index')
        def index() -> Response:
            """ Show Embedded App or Docs page """
            from flask_shopify_utils.model import Store

            params = request.args
            if len([x for x in params.keys() if x in ['shop', 'hmac', 'host', 'timestamp', 'session']]) < 4:
                # Redirect to the Docs page
                return redirect(url_for('docs_default.index'))
            # check store record from database
            if _ := Store.query.filter_by(key=params.get('shop')).first():
                return redirect(url_for('shopify_default.admin', **params))

            # redirect to install path
            return redirect(url_for('shopify_default.install', shop=params.get('shop')))

        # Register the `callback` route
        @default_routes.route('/callback', methods=['GET'], endpoint='callback')
        @self.check_callback
        def callback():
            url = 'https://{}/admin/oauth/access_token'.format(g.store_key)
            res = post_request(url, json=dict(
                client_id=self.config.get('SHOPIFY_API_KEY'),
                client_secret=self.config.get('SHOPIFY_API_SECRET'),
                code=g.code
            ))
            if res.status_code != 200:
                resp = self.proxy_response(500, 'Something went wrong while doing the OAuth!')
                resp.status_code = 500
                return resp
            data = res.json()
            token = data.get('access_token', '')
            # Query the shop domain and save the data
            client = GraphQLClient(g.store_key, token)
            raw_query = '{ shop { name, url } appInstallation { accessScopes { handle }} }'
            res = client.client(raw_query)['data']
            shop = res.get('shop', False)
            if not shop:
                resp = self.proxy_response(500, 'Something went wrong while fetching shop data!')
                resp.status_code = 500
                return resp
            cond = dict(key=g.store_key)
            record = Store.create_or_update(cond, domain=shop['url'].split('/')[-1], token=token, **cond)
            scopes = res.get('appInstallation', None)
            if not scopes:
                resp = self.proxy_response(500, 'Something went wrong while fetching installation data!')
                resp.status_code = 500
                return resp
            record.scopes = self.format_api_scopes(list(map(lambda x: x['handle'], scopes['accessScopes'])))
            self.db.commit()
            # Register GDPR mandatory webhook @todo
            # https://shopify.dev/docs/apps/auth/get-access-tokens/authorization-code-grant/getting-started
            return redirect('https://{}/admin/apps/{}'.format(
                g.store_key,
                self.config.get('SHOPIFY_API_KEY'))
            )

        # Register the `install` route
        @default_routes.route('/install', methods=['GET'], endpoint='install')
        def install():
            shop = request.args.get('shop', '')
            rs, resp = self.form_validate(
                dict(shop=shop),
                dict(shop=dict(type='string', required=True, regex=r'^(.*).myshopify.com$')),
            )
            if not rs:
                return resp
            # Redirect back to the Store Admin Panel for OAuth
            state = uuid4().hex
            params = dict(
                redirect_uri=url_for('shopify_default.callback', _scheme='https', _external=True),
                client_id=self.config.get('SHOPIFY_API_KEY'),
                scope=self.config.get('SCOPES'),
                state=state
            )
            resp = redirect('https://{}/admin/oauth/authorize?{}'.format(shop, urlencode(params)))
            resp.set_cookie('state', state)
            return resp

        # Register the Blueprint to routes
        self.app.register_blueprint(doc_routes)
        self.app.register_blueprint(default_routes)

    def enroll_gdpr_route(self):
        gdpr_routes = Blueprint('shopify_gdpr', 'shopify_gdpr_routes')

        # Register the webhook auth function before request
        @gdpr_routes.before_request
        def webhook_auth():
            """
            Check the webhook is valid or not
            :return None or Response
            """
            if not self.validate_webhook():
                resp = jsonify(dict(message='Hmac validation failed!', status=401))
                resp.status_code = 401
                return resp
            g.store_key = request.headers.get('X-Shopify-Shop-Domain', None)

        @gdpr_routes.route('/webhook/shop/redact', methods=['POST'], endpoint='shop_redact')
        def shop_redact():
            """
            You should erase the store information from your database
            get the store key from g.store_key
            """
            data = request.get_json(silent=True)
            print('shop_redact', data, g.store_key)
            return 'success'

        @gdpr_routes.route('/webhook/customers/redact', methods=['POST'], endpoint='customer_redact')
        def customer_redact():
            """
            You should erase the customer information from your database
            get the store key from g.store_key
            """
            data = request.get_json(silent=True)
            print('customer_redact', data, g.store_key)
            return 'success'

        @gdpr_routes.route('/webhook/customers/data_request', methods=['POST'], endpoint='customer_data_request')
        def customer_data():
            """
            If your app has been granted access to customers or orders, then you receive a data request webhook
            with the resource IDs of the data that you need to provide to the store owner.
            It's your responsibility to provide this data to the store owner directly.
            In some cases, a customer record contains only the customer's email address.
            get the store key from g.store_key
            """
            data = request.get_json(silent=True)
            print('customer_data_request', data, g.store_key)
            return 'success'

        self.app.register_blueprint(gdpr_routes)

    def enroll_admin_route(self):
        from flask_shopify_utils.model import Store

        admin_routes = Blueprint('admin_default', 'default_admin_routes', url_prefix='/admin')

        @admin_routes.route('/test_jwt', methods=['POST', 'GET'], endpoint='test_jwt')
        @self.check_jwt
        def test_jwt():
            if request.method == 'GET':
                return self.admin_response()
            data = request.get_json(silent=True)
            rs, resp = self.form_validate(data, dict(
                data=dict(type='dict', required=True, allow_unknown=True, schema=dict(
                    hmac=dict(type='string', required=True),
                    host=dict(type='string', required=True),
                    shop=dict(type='string', required=True),
                    timestamp=dict(type='string', required=True),
                ))), False)
            if not rs:
                return resp
            # check database
            bypass = self.config.get('BYPASS_VALIDATE', 0)
            if bypass != 0:
                g.store_id = bypass
            else:
                store = self.db.query(Store).filter_by(key=g.store_key).first()
                g.store_id = store.id if store else 0
            return self.admin_response(data=dict(
                apiKey=self.config.get('SHOPIFY_API_KEY'),
                jwtToken=self.create_admin_jwt_token()
            ))

        @admin_routes.route('/check/<action>', methods=['GET'], endpoint='check_scopes')
        @self.check_jwt
        def check_scopes(action):
            """ Check the granted scopes is update to date or not """
            if action not in ['reinstall', 'status']:
                return self.admin_response(400, 'Action[{}] is not supported!'.format(action))
            # check record
            record = Store.query.filter_by(id=g.store_id).first()
            if record:
                try:
                    obj = GraphQLClient(record.key, record.token)
                    raw_query = '{ app { availableAccessScopes { handle } } }'
                    _ = obj.fetch_data(raw_query)
                except Exception as e:
                    if 'HTTPError 401' in e.__str__():
                        record = None
            if not record or action == 'reinstall':
                shop = record.key if record else g.store_key
                if not shop:
                    return self.admin_response(400, 'Shop is missing from request!')
                return self.admin_response(
                    data=url_for('shopify_default.install', shop=shop, _external=True, _scheme='https')
                )
            current_scopes = self.format_api_scopes(record.scopes.lower().split(',')).split(',')
            expected_scopes = self.format_api_scopes(self.config.get('SCOPES').lower().split(',')).split(',')
            removes = [v for v in current_scopes if v not in expected_scopes]
            adds = [v for v in expected_scopes if v not in current_scopes]
            return self.admin_response(data=dict(
                removes=removes,
                adds=adds,
                change=len(removes) != 0 or len(adds) != 0
            ))

        self.app.register_blueprint(admin_routes)

    def enroll_graphql_schema_cli(self):
        from os import remove, getcwd, path
        from json import dump
        from click import option, echo, ClickException
        from sgqlc.endpoint.http import HTTPEndpoint
        from sgqlc.introspection import query, variables
        from sgqlc.codegen import get_arg_parse
        from flask_shopify_utils.utils import get_version
        from flask_shopify_utils.model import Store

        cli_bp = Blueprint('graphql_cli', 'graphql_cli', cli_group=None)

        @cli_bp.cli.command('generate_schema')
        @option('-s', '--store_id', default=1, help='Store ID')
        @option('-v', '--version', default=None, help='Schema version: 20xx-01 or 20xx-04 ...')
        @option('-d', '--with-deprecated', default=True, help='Include deprecated fields, default is True')
        def generate_schema(store_id, version, with_deprecated):
            """ Generate Shopify GraphQL schema """
            version = get_version(version)
            try:
                store = self.db.query(Store).filter_by(id=store_id).first()
                if not store:
                    raise ClickException('Store[{}} does not exists!'.format(store_id))
            except Exception as e:
                print(e)
                raise ClickException('Can`t fetch Store data from database!')
            url = 'https://{}/admin/api/{}/graphql'.format(store.key, version)
            endpoint = HTTPEndpoint(url, {'X-Shopify-Access-Token': store.token})
            data = endpoint(query, variables(
                include_description=False,
                include_deprecated=with_deprecated,
            ))
            json_file = 'schema.json'
            with open(json_file, 'w') as f:
                dump(data, f, indent=4, sort_keys=True, default=str)
            # check file path
            target_path = path.join(getcwd(), 'app', 'schemas')
            filename = 'shopify.py'
            if not path.exists(target_path):
                target_path = filename
            else:
                target_path = path.join(target_path, filename)
            ap = get_arg_parse()
            args = ap.parse_args(['schema', json_file, target_path])
            args.func(args)
            # remove the json file
            remove(json_file)
            # append version to the header of the file
            with open(target_path, 'r') as f:
                text = f.read()
            with open(target_path, 'w') as f:
                f.write('# API Version: {}\n'.format(version))
                f.write('# With deprecated: {}\n'.format(with_deprecated))
                f.write('# Generated At: {}\n'.format(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')))
                f.write(text)
            msg = 'GraphQL Schema for "{}" has been generated! \n'.format(version)
            msg += 'Please check the file: {}'.format(target_path)
            echo(msg)

        self.app.register_blueprint(cli_bp)
