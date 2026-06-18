#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : main.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 25/03/2025 10:20:58
"""
from pathlib import Path
from shutil import copy2, copytree, rmtree
from tempfile import TemporaryDirectory
from click import command, option, echo, confirm
from requests import get as get_request
from zipfile import ZipFile
from io import BytesIO


def _copy_item(source, dest):
    """
    Copy source to dest, overwriting same-name paths while preserving
    destination-only files inside existing directories.
    """
    source = Path(source)
    dest = Path(dest)

    if source.is_dir():
        if dest.exists() and not dest.is_dir():
            dest.unlink()
            copytree(source, dest)
            return

        dest.mkdir(parents=True, exist_ok=True)
        for child in sorted(source.iterdir()):
            _copy_item(child, dest / child.name)
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.is_dir():
        rmtree(dest)
    copy2(source, dest)


def _handle_item(source, dest, display_name):
    """
    Recursively handle a single file or directory copy with prompts.

    Rules:
    - File exists  -> ask "overwrite?" (Y/N).
    - Dir exists   -> ask "overwrite files with the same names?" (Y/N).
                      If Y -> merge-copy the directory, preserving dest-only files.
                      If N -> ask "walk into it and decide per child?" (Y/N).
                          If N -> skip the whole directory.
                          If Y -> recurse into each child.
    """
    source = Path(source)
    dest = Path(dest)

    # Destination does not exist -> copy straight through.
    if not dest.exists():
        _copy_item(source, dest)
        echo(f'Copied "{display_name}".')
        return

    # File conflict.
    if source.is_file():
        if confirm(f'The file "{display_name}" already exists. Overwrite?'):
            copy2(source, dest)
            echo(f'Overwrote "{display_name}".')
        else:
            echo(f'Skipped "{display_name}".')
        return

    # Directory conflict.
    if confirm(
        f'The directory "{display_name}" already exists. '
        'Overwrite files with the same names?'
    ):
        _copy_item(source, dest)
        echo(f'Overwrote directory "{display_name}".')
        return

    if not confirm(
        f'Walk into "{display_name}" and decide for each file/sub-directory?'
    ):
        echo(f'Skipped directory "{display_name}".')
        return

    # Recurse: ask per child.
    for child in sorted(source.iterdir()):
        _handle_item(
            child,
            dest / child.name,
            str(Path(display_name) / child.name),
        )


@command()
@option(
    '--repo',
    default='https://github.com/leocxy/flask-shopify-utils',
    help='GitHub repository URL',
)
@option('-d', '--directory', default='.', help='Default is the current folder')
@option('-b', '--branch', default='master', help='Git branch to download')
def copy_files(repo, directory, branch):
    """
    Copy the specified directory from the given GitHub repository to the current folder.
    """
    zip_url = f'{repo}/archive/refs/heads/{branch}.zip'

    # Download the repository zip file
    response = get_request(zip_url, timeout=60)
    if response.status_code != 200:
        echo('Failed to download repository.')
        return

    target_dir = Path.cwd() / directory

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Extract the zip file into an isolated temporary directory.
        with ZipFile(BytesIO(response.content)) as zip_file:
            zip_file.extractall(temp_path)

        # Construct the source and destination paths.
        source_root = None
        for extracted_root in sorted(temp_path.iterdir()):
            candidate = extracted_root / 'example' / 'example1'
            if candidate.exists():
                source_root = candidate
                break

        if source_root is None:
            echo(
                'Source directory "example/example1" does not exist '
                'in the repository.'
            )
            return

        target_dir.mkdir(parents=True, exist_ok=True)

        for source_item in sorted(source_root.iterdir()):
            _handle_item(
                source_item,
                target_dir / source_item.name,
                source_item.name,
            )

    echo('Temporary extract folder has been removed!')

