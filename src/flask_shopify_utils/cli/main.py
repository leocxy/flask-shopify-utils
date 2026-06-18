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


def _handle_item(source, dest, display_name):
    """
    Recursively handle a single file or directory copy with prompts.

    Rules:
    - File exists  -> ask "overwrite?" (Y/N).
    - Dir exists   -> ask "overwrite the whole directory?" (Y/N).
                      If N -> ask "walk into it and decide per child?" (Y/N).
                          If N -> skip the whole directory.
                          If Y -> recurse into each child.
    """
    source = Path(source)
    dest = Path(dest)

    # Destination does not exist -> copy straight through.
    if not dest.exists():
        if source.is_dir():
            copytree(source, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy2(source, dest)
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
        'Overwrite the whole directory?'
    ):
        rmtree(dest)
        copytree(source, dest)
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
    repo_name = repo.rstrip('/').split('/')[-1]
    zip_url = f'{repo}/archive/refs/heads/{branch}.zip'

    # Download the repository zip file
    response = get_request(zip_url, timeout=60)
    if response.status_code != 200:
        echo('Failed to download repository.')
        return

    extra_folder = f'{repo_name}-master'
    target_dir = Path.cwd() / directory

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Extract the zip file into an isolated temporary directory.
        with ZipFile(BytesIO(response.content)) as zip_file:
            zip_file.extractall(temp_path)

        # Construct the source and destination paths.
        source_root = temp_path / extra_folder / 'example' / 'example1'

        if not source_root.exists():
            echo(
                f'Source directory "{source_root}" does not exist '
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

