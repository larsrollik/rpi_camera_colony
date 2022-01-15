#!/bin/bash
# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
#
# Use in commandline as:
#     distribute_code LOCAL_code_path REMOTE_code_path REMOTE_pip_path
# ! Change rpi host names for your setup

# Default arguments
code_dir=${1:-"$HOME/code/rpi_camera_colony"}
remote_code_dir=${2:-"/home/pi/code/"}
remote_pip=${3:-"/home/pi/miniconda3/envs/py36/bin/pip"}
remote_pip_command="$remote_pip install -e "
repo_name=$(basename $code_dir)

# Rsync
parallel -j 8 rsync -av $code_dir "{1}:$remote_code_dir" --exclude=".git" --exclude="__pycache__" --exclude=".idea" --exclude="tests" --exclude="*.egg-info" ::: testrpi

# (Re-)Install
parallel -j 8 ssh {1} sudo nohup "${remote_pip_command} ${remote_code_dir}/${repo_name}[rpi]" ::: testrpi
