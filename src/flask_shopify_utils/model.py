#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : models.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 6/06/23 4:02 pm
"""
from flask_sqlalchemy import SQLAlchemy
from json import loads
from . import current_time_func as current_time, sqlalchemy_instance as db

if db is None or not isinstance(db, SQLAlchemy):
    raise RuntimeError('Please initialize the SQLAlchemy instance first.')


class BasicMethod:

    @classmethod
    def create_or_update(cls, cond: dict, **kwargs) -> db.Model:
        record = cls.query.filter_by(**cond).first()
        if not record:
            record = cls()
            db.session.add(record)
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        return record

    @classmethod
    def create(cls, **kwargs) -> db.Model:
        record = cls()
        db.session.add(record)
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        return record

    @staticmethod
    def get_status(name: str):
        names = dict(wait=0, done=1, error=2, ignore=3, unknown=9)
        return names.get(name, 9)


class Store(db.Model, BasicMethod):
    __tablename__ = 'stores'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), index=True)
    domain = db.Column(db.String(255))
    scopes = db.Column(db.String(2048), nullable=False)
    token = db.Column(db.String(128), nullable=False)
    extra = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=current_time)
    updated_at = db.Column(db.DateTime, default=current_time, onupdate=current_time)

    def get_extra(self) -> dict:
        return loads(self.extra) if self.extra else {}

    def set_extra(self, data: dict) -> None:
        extra = self.get_extra()
        extra.update(data)


class Webhook(db.Model, BasicMethod):
    __tablename__ = 'webhooks'
    __table_args__ = (
        db.PrimaryKeyConstraint('id'),
        db.Index('store_webhook', 'store_id', 'webhook_id')
    )
    id = db.Column(db.Integer)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    webhook_id = db.Column(db.BigInteger, comment="Webhook ID")
    target = db.Column(db.String(24), comment='Action Target')
    action = db.Column(db.String(24), comment='Action')
    data = db.Column(db.Text(64000), comment='JSON string -> 64kb medium text for MYSQL/MariaDB')
    remark = db.Column(db.Text)
    status = db.Column(db.SmallInteger, default=0)
    created_at = db.Column(db.DateTime, default=current_time)
    updated_at = db.Column(db.DateTime, default=current_time, onupdate=current_time)


__all__ = (Store, Webhook, BasicMethod)
