#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_cli_main.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 18/06/2026 12:00:00
"""
from io import BytesIO
from pathlib import Path
from typing import cast
from zipfile import ZipFile

from click import Command
from click.testing import CliRunner

from flask_shopify_utils.cli import main as cli_main

COPY_FILES_COMMAND = cast(Command, cli_main.copy_files)


class MockResponse:
    def __init__(self, status_code=200, content=b''):
        self.status_code = status_code
        self.content = content


def build_repo_zip(files, root_dir='flask-shopify-utils-master'):
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as zip_file:
        for name, content in files.items():
            zip_file.writestr(
                f'{root_dir}/example/example1/{name}',
                content,
            )
    return buffer.getvalue()


def test_handle_item_copies_missing_file(tmp_path, capsys):
    source = tmp_path / 'source.txt'
    dest = tmp_path / 'dest.txt'
    source.write_text('new file', encoding='utf-8')

    cli_main._handle_item(source, dest, 'dest.txt')

    output = capsys.readouterr().out

    assert dest.read_text(encoding='utf-8') == 'new file'
    assert 'Copied "dest.txt".' in output


def test_handle_item_overwrites_existing_file(tmp_path, monkeypatch, capsys):
    source = tmp_path / 'source.txt'
    dest = tmp_path / 'dest.txt'
    source.write_text('new file', encoding='utf-8')
    dest.write_text('old file', encoding='utf-8')
    monkeypatch.setattr(cli_main, 'confirm', lambda message: True)

    cli_main._handle_item(source, dest, 'dest.txt')
    output = capsys.readouterr().out

    assert dest.read_text(encoding='utf-8') == 'new file'
    assert 'Overwrote "dest.txt".' in output


def test_handle_item_skips_existing_file(tmp_path, monkeypatch, capsys):
    source = tmp_path / 'source.txt'
    dest = tmp_path / 'dest.txt'
    source.write_text('new file', encoding='utf-8')
    dest.write_text('old file', encoding='utf-8')
    monkeypatch.setattr(cli_main, 'confirm', lambda message: False)

    cli_main._handle_item(source, dest, 'dest.txt')
    output = capsys.readouterr().out

    assert dest.read_text(encoding='utf-8') == 'old file'
    assert 'Skipped "dest.txt".' in output


def test_handle_item_overwrites_existing_directory(tmp_path, monkeypatch, capsys):
    source = tmp_path / 'source_dir'
    dest = tmp_path / 'dest_dir'
    source.mkdir()
    dest.mkdir()
    (source / 'source.txt').write_text('new file', encoding='utf-8')
    (source / 'same.txt').write_text('new same file', encoding='utf-8')
    (dest / 'old.txt').write_text('old file', encoding='utf-8')
    (dest / 'same.txt').write_text('old same file', encoding='utf-8')
    monkeypatch.setattr(cli_main, 'confirm', lambda message: True)

    cli_main._handle_item(source, dest, 'dest_dir')
    output = capsys.readouterr().out

    assert (dest / 'source.txt').read_text(encoding='utf-8') == 'new file'
    assert (dest / 'same.txt').read_text(encoding='utf-8') == 'new same file'
    assert (dest / 'old.txt').read_text(encoding='utf-8') == 'old file'
    assert 'Overwrote directory "dest_dir".' in output


def test_handle_item_skips_existing_directory(tmp_path, monkeypatch, capsys):
    source = tmp_path / 'source_dir'
    dest = tmp_path / 'dest_dir'
    source.mkdir()
    dest.mkdir()
    (source / 'source.txt').write_text('new file', encoding='utf-8')
    (dest / 'old.txt').write_text('old file', encoding='utf-8')
    answers = iter([False, False])
    monkeypatch.setattr(cli_main, 'confirm', lambda message: next(answers))

    cli_main._handle_item(source, dest, 'dest_dir')
    output = capsys.readouterr().out

    assert not (dest / 'source.txt').exists()
    assert (dest / 'old.txt').read_text(encoding='utf-8') == 'old file'
    assert 'Skipped directory "dest_dir".' in output


def test_handle_item_recurses_into_existing_directory(
        tmp_path,
        monkeypatch,
        capsys,
):
    source = tmp_path / 'source_dir'
    dest = tmp_path / 'dest_dir'
    source.mkdir()
    dest.mkdir()
    (source / 'existing.txt').write_text('new file', encoding='utf-8')
    (source / 'new.txt').write_text('another file', encoding='utf-8')
    (dest / 'existing.txt').write_text('old file', encoding='utf-8')
    answers = iter([False, True, False])
    monkeypatch.setattr(cli_main, 'confirm', lambda message: next(answers))

    cli_main._handle_item(source, dest, 'dest_dir')
    output = capsys.readouterr().out

    assert (dest / 'existing.txt').read_text(encoding='utf-8') == 'old file'
    assert (dest / 'new.txt').read_text(encoding='utf-8') == 'another file'
    assert 'Skipped "dest_dir/existing.txt".' in output
    assert 'Copied "dest_dir/new.txt".' in output


def test_copy_files_reports_download_failure(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        'get_request',
        lambda url, timeout: MockResponse(status_code=404),
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(COPY_FILES_COMMAND)

    assert result.exit_code == 0
    assert 'Failed to download repository.' in result.output


def test_copy_files_reports_missing_source_directory(monkeypatch):
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as zip_file:
        zip_file.writestr('flask-shopify-utils-master/README.md', '# Project')
    monkeypatch.setattr(
        cli_main,
        'get_request',
        lambda url, timeout: MockResponse(content=buffer.getvalue()),
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(COPY_FILES_COMMAND)

    assert result.exit_code == 0
    assert 'does not exist in the repository.' in result.output


def test_copy_files_copies_example_scaffold(monkeypatch):
    content = build_repo_zip({
        'README.md': '# Example',
        'backend/app.py': 'print("hello")',
        'frontend/package.json': '{"scripts": {}}',
    })
    monkeypatch.setattr(
        cli_main,
        'get_request',
        lambda url, timeout: MockResponse(content=content),
    )
    runner = CliRunner()

    with runner.isolated_filesystem() as isolated_dir:
        result = runner.invoke(
            COPY_FILES_COMMAND,
            ['--directory', 'shopify-app'],
        )
        target_dir = Path(isolated_dir) / 'shopify-app'

        assert result.exit_code == 0
        assert 'Copied "README.md".' in result.output
        assert 'Copied "backend".' in result.output
        assert 'Copied "frontend".' in result.output
        assert 'Temporary extract folder has been removed!' in result.output
        assert (target_dir / 'README.md').read_text(encoding='utf-8') == '# Example'
        assert (target_dir / 'backend' / 'app.py').read_text(
            encoding='utf-8',
        ) == 'print("hello")'


def test_copy_files_copies_example_scaffold_from_branch(monkeypatch):
    content = build_repo_zip(
        {'README.md': '# Feature branch example'},
        root_dir='flask-shopify-utils-feature-branch',
    )
    requested_urls = []

    def mock_get_request(url, timeout):
        requested_urls.append(url)
        return MockResponse(content=content)

    monkeypatch.setattr(cli_main, 'get_request', mock_get_request)
    runner = CliRunner()

    with runner.isolated_filesystem() as isolated_dir:
        result = runner.invoke(
            COPY_FILES_COMMAND,
            ['--branch', 'feature-branch'],
        )
        target_dir = Path(isolated_dir)

        assert result.exit_code == 0
        assert requested_urls == [
            'https://github.com/leocxy/flask-shopify-utils'
            '/archive/refs/heads/feature-branch.zip',
        ]
        assert 'Copied "README.md".' in result.output
        assert (target_dir / 'README.md').read_text(
            encoding='utf-8',
        ) == '# Feature branch example'

