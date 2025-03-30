#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : mutation.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 28/11/2024 15:00:54
"""
from sgqlc.operation import Operation
# custom modules
from .shopify import shopify as shopify_schema


def update_meta(owner_id: str, value, namespace: str, key: str, value_type: str = 'json') -> Operation:
    op = Operation(shopify_schema.mutation_type, 'UpdateCodeMeta')
    mutation = op.metafields_set(metafields=[dict(
        owner_id=owner_id,
        namespace=namespace,
        key=key,
        type=value_type,
        value=value
    )])
    mutation.user_errors()
    mutation.metafields.id()
    return op


def update_multiple_meta(data: list) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'UpdateMultipleMeta')
    mutation = op.metafields_set(metafields=data)
    mutation.user_errors()
    mutation.metafields.id()
    return op


def create_discount_code(data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'CreateDiscountCode')
    mutation = op.discount_code_app_create(code_app_discount=data)
    mutation.code_app_discount.discount_id()
    mutation.user_errors()
    return op


def update_discount_code(owner_id: str, data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'UpdateCode')
    mutation = op.discount_code_app_update(
        code_app_discount=data,
        id=owner_id
    )
    mutation.user_errors()
    return op


def delete_discount_code(code_id: str) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'DeleteDiscountCode')
    mutation = op.discount_code_delete(id='gid://shopify/DiscountCodeNode/{}'.format(code_id))
    mutation.user_errors()
    return op


def create_auto_discount(data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'CreateAutoDiscount')
    mutation = op.discount_automatic_app_create(automatic_app_discount=data)
    mutation.user_errors()
    mutation.automatic_app_discount.discount_id()
    return op


def update_auto_discount(owner_id: str, data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'UpdateAutoDiscount')
    mutation = op.discount_automatic_app_update(
        automatic_app_discount=data,
        id=owner_id
    )
    mutation.user_errors()
    return op


def delete_auto_discount(code_id: str) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'DeleteAutoDiscount')
    mutation = op.discount_automatic_delete(id='gid://shopify/DiscountAutomaticNode/{}'.format(code_id))
    mutation.user_errors()
    return op


def revoke_webhooks(data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'RevokeWebhooks')
    for alias in data.keys():
        mutation = op.webhook_subscription_delete(id=data[alias]['id'], __alias__=alias)
        mutation.user_errors()
    return op


def create_webhooks(data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'CreateWebhooks')
    for topic in data.keys():
        mutation = op.webhook_subscription_create(topic=topic, webhook_subscription=data[topic], __alias__=topic)
        mutation.user_errors()
    return op


def create_delivery_customization(input_data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'CreateDeliveryCustomization')
    mutation = op.delivery_customization_create(
        delivery_customization=input_data
    )
    mutation.delivery_customization.id()
    mutation.user_errors()
    return op


def update_delivery_customization(gid: str, input_data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'UpdateDeliveryCustomization')
    mutation = op.delivery_customization_update(
        id=gid,
        delivery_customization=input_data
    )
    mutation.user_errors()
    return op


def delete_delivery_customization(gid: str) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'DeleteDeliveryCustomization')
    mutation = op.delivery_customization_delete(id=gid)
    mutation.user_errors()
    return op


def create_payment_customization(input_data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'CreatePaymentCustomization')
    mutation = op.payment_customization_create(
        payment_customization=input_data
    )
    mutation.payment_customization.id()
    mutation.user_errors()
    return op


def update_payment_customization(gid: str, input_data: dict) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'UpdatePaymentCustomization')
    mutation = op.payment_customization_update(
        id=gid,
        payment_customization=input_data
    )
    mutation.user_errors()
    return op


def delete_payment_customization(gid: str) -> Operation:
    op = Operation(shopify_schema.mutation_type, 'DeletePaymentCustomization')
    mutation = op.payment_customization_delete(id=gid)
    mutation.user_errors()
    return op
