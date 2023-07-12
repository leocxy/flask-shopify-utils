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
from functools import wraps
from hmac import new as hmac_new, compare_digest
from datetime import datetime, timedelta
from uuid import uuid4
from requests import post as post_request
from urllib.parse import urlencode
# Third-party Library
from flask import Flask, request, g, jsonify, Response, current_app, Blueprint, redirect, render_template, \
    make_response, url_for
from jinja2 import TemplateNotFound
from jwt import encode as jwt_encode, decode as jwt_decode, ExpiredSignatureError
from cerberus.validator import Validator
from flask_shopify_utils.utils import get_version, GraphQLClient

__version__ = '0.0.1'

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
        default_tz = 'Pacific/Auckland'

        config.setdefault('ROOT_PATH', getcwd())
        config.setdefault('TEMPORARY_PATH', path.join(config.get('ROOT_PATH'), 'tmp'))
        config.setdefault('API_VERSION', get_version())
        config.setdefault('RESTFUL_VERSION', get_version(restful=True))
        config.setdefault('TIMEZONE', default_tz)
        config.setdefault('SHOPIFY_API_SECRET', 'CUSTOM_APP_SECRET')
        config.setdefault('SHOPIFY_API_KEY', 'CUSTOM_APP_KEY')
        config.setdefault('BYPASS_VALIDATE', 0)
        config.setdefault('DEBUG', False)
        config.setdefault('SCOPES', 'read_products')

        # Set environment variable
        environ['TIMEZONE'] = config.get('TIMEZONE')

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
        secret = self.config.get('SHOPIFY_API_SECRET') if self.config else 'SHOPIFY_API_SECRET'
        return compare_digest(signature, hmac_new(secret.encode('utf-8'), data, sha256).hexdigest())

    def validate_jwt(self) -> Tuple[bool, JWT_DATA]:
        token = request.headers.get('Authorization', '')
        try:
            res = jwt_decode(token, self.config.get('SHOPIFY_API_SECRET', ''), algorithms='HS256')
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
            # check timestamp
            timestamp1 = int(request.args.get('timestamp', '0'))
            timestamp2 = int(time()) - 86400
            if timestamp1 < timestamp2:
                return jsonify(dict(message='The request has expired', status=401))
            params = request.args
            if len([x for x in params.keys() if x in ['session', 'hmac', 'host', 'timestamp']]) != 4:
                # Redirect to the Docs page
                return redirect(url_for('docs.index'))
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
            store = Store.query.filter_by(store_key=g.store_key).first()
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
            g.store_id = data['store_id']
            g.jwt_expire_time = data['expire_time']
            return func(*args, **kwargs)

        return decorator

    def create_admin_jwt_token(self) -> str:
        expire_time = datetime.utcnow() + timedelta(minutes=30)
        return jwt_encode(dict(
            store_id=g.store_id,
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

    def enroll_default_route(self) -> None:
        """
        Register default Shopify routes
        """
        from flask_shopify_utils.model import Store

        static_folder = path.join(path.dirname(self.config.get('ROOT_PATH')), 'dist', 'front')
        doc_routes = Blueprint(
            'docs',
            'docs_routes',
            url_prefix='/docs',
            static_folder=static_folder,
            template_folder=static_folder
        )

        @doc_routes.route('/', methods=['GET'])
        def docs_index() -> Response:
            """
            Show the docs for default message
            """
            try:
                return make_response(render_template('index.html'))
            except TemplateNotFound:
                return make_response('Please contact "dev@pocketsquare.co.nz" for more information.')

        static_folder = path.join(path.dirname(self.config.get('ROOT_PATH')), 'dist')
        default_routes = Blueprint(
            'shopify',
            'shopify_default_routes',
            static_folder=static_folder,
            template_folder=static_folder
        )

        # Register the `admin` route
        @default_routes.route('/', methods=['GET'], endpoint='index')
        @self.check_hmac
        def index() -> Response:
            """ Show Embedded App or Docs page """
            # check database
            bypass = self.config.get('BYPASS_VALIDATE', 0)
            if bypass != 0:
                g.store_id = bypass
            else:
                store = self.db.query(Store).filter_by(key=g.store_key).first()
                if not store:
                    msg = '{} not found in database! \n'.format(g.store_key)
                    msg += 'You can install the app via this URL: \n'
                    msg += url_for('shopify.install', shop=g.store_key, _external=True, _scheme='https')
                    resp = self.proxy_response(404, msg)
                    resp.status_code = 404
                    return resp
                g.store_id = store.id
            # Render the Embedded App Index Page
            try:
                code = render_template(
                    path.join('admin', 'index.html'),
                    apiKey=self.config.get('SHOPIFY_API_KEY'),
                    host=g.host,
                    jwtToken=self.create_admin_jwt_token()
                )
            except TemplateNotFound:
                return self.proxy_response(0, 'Oops... The `index.html` is gone!')
            return make_response(code)

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
            res = client.client(raw_query)
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
            record.scopes = ','.join(list(map(lambda x: x['handle'], scopes['accessScopes'])))
            # Register GDPR mandatory webhook @todo
            return redirect('https://{}.myshopify.com/admin/app/{}'.format(
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
                redirect_uri=url_for('shopify.callback', _scheme='https', _external=True),
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

        admin_routes = Blueprint('admin', 'default_admin_routes', url_prefix='/admin')

        @admin_routes.route('/test_jwt', methods=['GET'], endpoint='test_jwt')
        @self.check_jwt
        def test_jwt():
            return self.admin_response()

        @admin_routes.route('/check/<action>', methods=['GET'], endpoint='check_scopes')
        @self.check_jwt
        def check_scopes(action):
            """ Check the granted scopes is update to date or not """
            if action not in ['reinstall', 'status']:
                return self.admin_response()
            record = Store.query.filter_by(id=g.store_id).first()
            if not record:
                return self.admin_response(400, 'Store[{}] does not exist!'.format(g.store_id))
            if action == 'reinstall':
                return jsonify(data=url_for('shopify.install', shop=record.key, _external=True, _scheme='https'))
            current_scopes = record.scopes.lower().split(',')
            scopes = self.config.get('SCOPES').lower().split(',')
            removes = [v for v in current_scopes if v not in scopes]
            adds = [v for v in scopes if v not in current_scopes]
            return self.admin_response(data=dict(
                removes=removes,
                adds=adds,
                change=len(removes) != 0 or len(adds) != 0
            ))

        self.app.register_blueprint(admin_routes)

    def enrol_graphql_schema_cli(self):
        pass
