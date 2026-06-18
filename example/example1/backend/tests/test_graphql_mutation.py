#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_graphql_mutation.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:07:53
Each test builds an Operation and compares its rendered GraphQL against a golden
snapshot in tests/snapshots/<name>.graphql (see the `assert_gql` fixture in conftest.py).
Rendering inside assert_gql also validates that the Operation builds and serialises,
so the snapshot assertion replaces the old "doesn't raise" checks.

Generate / update the goldens with:  UPDATE_SNAPSHOTS=1 pytest
"""
from types import FunctionType
from app.schemas.mutation import update_meta, update_multiple_meta, create_discount_code, update_discount_code, \
    delete_discount_code, create_auto_discount, update_auto_discount, delete_auto_discount, create_webhooks, \
    revoke_webhooks, create_payment_customization, delete_payment_customization, update_payment_customization, \
    create_delivery_customization, delete_delivery_customization, update_delivery_customization
from app.schemas.shopify import DiscountCodeAppInput, DiscountAutomaticAppInput, PaymentCustomizationInput, \
    DeliveryCustomizationInput, MetafieldsSetInput, WebhookSubscriptionInput, DiscountCombinesWithInput
# custom


DISCOUNT_CODE_DATA = DiscountCodeAppInput(
    code='test_code',
    combines_with=DiscountCombinesWithInput(
        product_discounts=True,
        order_discounts=True,
        shipping_discounts=True
    ),
    applies_once_per_customer=True,
    title='test_title',
    usage_limit=10,
    function_handle='function_handle',
    starts_at='2000-01-01T00:00:00',
)

AUTO_DISCOUNT_DATA = DiscountAutomaticAppInput(
    applies_on_subscription=False,
    combines_with=DiscountCombinesWithInput(
        product_discounts=True,
        order_discounts=True,
        shipping_discounts=True
    ),
    starts_at='2000-01-01T00:00:00',
    function_handle='function_handle',
    metafields=[dict(
        namespace='namespace',
        key='key',
        type='single_line_text',
        value='test_value'
    )],
    title='test_title',
)


def test_update_meta(assert_gql):
    op = update_meta(
        'gid://shopify/Customer/123456',
        'test_value',
        'namespace',
        'key',
        'single_line_text'
    )
    assert_gql('update_meta', op)


def test_update_multiple_meta(assert_gql):
    op = update_multiple_meta([
        MetafieldsSetInput(
            owner_id='gid://shopify/Customer/123456',
            namespace='namespace',
            key='key',
            type='single_line_text',
            value='test_value'
        )
    ])
    assert_gql('update_multiple_meta', op)


def test_create_discount_code(assert_gql):
    op = create_discount_code(DISCOUNT_CODE_DATA)
    assert_gql('create_discount_code', op)


def test_update_discount_code(assert_gql):
    op = update_discount_code('gid://shopify/DiscountCodeNode/123456', DISCOUNT_CODE_DATA)
    assert_gql('update_discount_code', op)


def test_delete_discount_code(assert_gql):
    op = delete_discount_code('123456')
    assert_gql('delete_discount_code', op)


def test_create_auto_discount(assert_gql):
    op = create_auto_discount(AUTO_DISCOUNT_DATA)
    assert_gql('create_auto_discount', op)


def test_update_auto_discount(assert_gql):
    op = update_auto_discount('gid://shopify/DiscountCodeNode/123456', AUTO_DISCOUNT_DATA)
    assert_gql('update_auto_discount', op)


def test_delete_auto_discount(assert_gql):
    op = delete_auto_discount('123456')
    assert_gql('delete_auto_discount', op)


def test_create_webhooks(assert_gql):
    data = {'APP_UNINSTALLED': WebhookSubscriptionInput(uri='http://127.0.0.1:500')}
    op = create_webhooks(data)
    assert_gql('create_webhooks', op)


def test_revoke_webhooks(assert_gql):
    data = {'ALIAS_ID': dict(id='owner_id', topic='topic')}
    op = revoke_webhooks(data)
    assert_gql('revoke_webhooks', op)


def test_create_payment_customization(assert_gql) -> None:
    op = create_payment_customization(PaymentCustomizationInput(
        function_handle='function_handle',
        enabled=True,
        title='title',
        metafields=[]
    ))
    assert_gql('create_payment_customization', op)


def test_update_payment_customization(assert_gql) -> None:
    op = update_payment_customization('gid://shopify/PaymentCustomization/1234', PaymentCustomizationInput(
        enabled=False,
        title='title'
    ))
    assert_gql('update_payment_customization', op)


def test_delete_payment_customization(assert_gql) -> None:
    op = delete_payment_customization('gid://shopify/PaymentCustomization/1234')
    assert_gql('delete_payment_customization', op)


def test_create_delivery_customization(assert_gql) -> None:
    op = create_delivery_customization(DeliveryCustomizationInput(
        function_handle='function_handle',
        enabled=True,
        title='title',
        metafields=[]
    ))
    assert_gql('create_delivery_customization', op)


def test_update_delivery_customization(assert_gql) -> None:
    op = update_delivery_customization('gid://shopify/DeliveryCustomization/1234', DeliveryCustomizationInput(
        enabled=False,
        title='title'
    ))
    assert_gql('update_delivery_customization', op)


def test_delete_delivery_customization(assert_gql) -> None:
    op = delete_delivery_customization('gid://shopify/DeliveryCustomization/1234')
    assert_gql('delete_delivery_customization', op)


# custom functions


###
# Coverage check - make sure all functions are covered
###
COVERAGE_FUNCS = [name for name, obj in locals().items() if
                  isinstance(obj, FunctionType) and name.startswith('test_')]


def test_coverage_check() -> None:
    from app.schemas import mutation as mutation_schema
    funcs = []
    for item in dir(mutation_schema):
        # exclude methods
        if item in ['TypedDict']:
            continue
        if isinstance(getattr(mutation_schema, item), FunctionType):
            fn = 'test_{}'.format(item)
            if fn not in COVERAGE_FUNCS:
                funcs.append(item)

    if len(funcs) == 0:
        assert True, 'All functions are covered'
    else:
        assert False, 'Not covered functions: {}'.format(', '.join(funcs))
