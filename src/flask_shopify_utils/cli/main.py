#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : __init__.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 25/03/2025 10:20:58
"""
from os import path, walk, makedirs, getcwd, listdir
from shutil import copy2, rmtree
from click import command, option, echo, confirm
from requests import get as get_request
from zipfile import ZipFile
from io import BytesIO


@command()
@option('--repo', default='https://github.com/leocxy/flask-shopify-utils', help='GitHub repository URL')
@option('-d', '--directory', default='.', help='Default is the current folder')
def copy_files(repo, directory):
    """
    Copy the specified directory from the given GitHub repository to the current folder.
    """
    repo_name = repo.rstrip('/').split('/')[-1]
    zip_url = f'{repo}/archive/refs/heads/master.zip'

    # Download the repository zip file
    response = get_request(zip_url)
    if response.status_code != 200:
        echo('Failed to download repository.')
        return

    # Extract the zip file
    with ZipFile(BytesIO(response.content)) as zip_file:
        zip_file.extractall()

    # Construct the source and destination paths
    extra_folder = f'{repo_name}-master'
    source_dir = f'{extra_folder}/example/example1'
    target_dir = path.join(getcwd(), directory)
    folders = [v for v in listdir(source_dir) if path.isdir(path.join(source_dir, v))]
    files = [v for v in listdir(source_dir) if not path.isdir(path.join(source_dir, v))]
    # get the folders
    dest_dirs = [path.normpath(path.join(target_dir, v)) for v in folders]
    source_dirs = [[path.normpath(path.join(source_dir, v)), v] for v in folders]

    # check if the destination file exists or not
    for file in files:
        source_file = path.normpath(path.join(source_dir, file))
        dest_file = path.normpath(path.join(target_dir, file))
        if path.exists(dest_file):
            if not confirm(f'The file "{dest_file}" already exists. Do you want to overwrite the file?'):
                echo(f'Not overwrite {dest_file}.')
                continue
        copy2(source_file, dest_file)

    # check if the destination directory exists or not
    for index, dest_dir in enumerate(dest_dirs):
        source_dir = source_dirs[index][0]
        dir_name = source_dirs[index][1]
        if path.exists(dest_dir):
            if not confirm(f'The directory "{dir_name}" already exists. Do you want to overwrite existing files?'):
                echo('Operation cancelled.')
                continue

        # Copy the directory
        if path.exists(source_dir):
            for root, dirs, files in walk(source_dir):
                relative_path = path.relpath(root, source_dir)
                dest_path = path.join(dest_dir, relative_path)
                if not path.exists(dest_path):
                    makedirs(dest_path)
                for file in files:
                    copy2(path.join(root, file), path.join(dest_path, file))
            echo(f'Successfully copied "{dir_name}" to the current folder.')
        else:
            echo(f'Directory "{dir_name}" does not exist in the repository.')

    # Remove the extracted folder
    rmtree(extra_folder)
    echo('Extract folder have been removed!')
