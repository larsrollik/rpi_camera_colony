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
code_dir=${1:-"/home/lbr/code/rpi_camera_colony"}
remote_code_dir=${2:-"/home/pi/code/"}
remote_pip=${3:-"/home/pi/miniconda3/envs/py36/bin/pip"}
remote_pip_command="$remote_pip install -e "

for remote_host in "rpi-red60" "rpi-yellow61" "rpi-blue62"  # .ssh/config host definitions
do
  printf "\n\n\n======================================= $remote_host \n"

  repo_name=$(basename $code_dir)
  printf $code_dir $remote_code_dir $repo_name

  rsync -av $code_dir "$remote_host:$remote_code_dir" \
    --exclude=".git" \
    --exclude="__pycache__" \
    --exclude=".idea" \
    --exclude="tests" \
    --exclude="*.egg-info"


  ssh_command="$remote_host sudo nohup ${remote_pip_command} ${remote_code_dir}/${repo_name}[rpi]"
  printf $ssh_command

  ssh $ssh_command

done
