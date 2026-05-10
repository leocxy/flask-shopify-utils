#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project  : flask-shopify-utils
# @File     : telemetry.py
# @Author   : Leo Chen<leo.cxy88@gmail.com>
# @Created  : 2026/05/11 09:32
# @Updated  : 2026/05/11 09:32

This is optional file.
If you want to use Azure Monitor (Application Insights).
And you want to track the exectpion from the Flask CLI, you need to this library

How to implement, instrument the cli blueprint from the app/scripts/__init__.py
```python
    if getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'):
        from app.utils.telemetry import instrument_cli_blueprint
        for bp in (webhook_cli):
            instrument_cli_blueprint(bp)
```
"""
from functools import wraps
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

_tracer = trace.get_tracer('app.cli')


def track_cli_exception(span_name):
    """Wrap a CLI callback so unhandled exceptions are recorded on an
    OpenTelemetry span (exported to Azure Monitor) and surfaced via
    app.logger.exception so the log exporter picks them up too."""
    from app import app

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with _tracer.start_as_current_span(span_name) as span:
                span.set_attribute('cli.command', span_name)
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    app.logger.exception('CLI fatal error in %s', span_name)
                    raise

        return wrapper

    return decorator


def instrument_cli_blueprint(blueprint):
    """Wrap every CLI command on the blueprint so unhandled errors flow into
    Application Insights as exceptions on a dedicated span."""
    group = getattr(blueprint, 'cli_group', None) or blueprint.name
    for name, cmd in blueprint.cli.commands.items():
        if cmd.callback is None or getattr(cmd.callback, '_cli_instrumented', False):
            continue
        wrapped = track_cli_exception(f'cli.{group}.{name}')(cmd.callback)
        wrapped._cli_instrumented = True
        cmd.callback = wrapped
