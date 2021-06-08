#!/bin/bash
# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
#
# Use in commandline as:
#     collect_data_from_remotes LOCAL_path REMOTE_path
# ! Change rpi host names for your setup

# Default arguments
data_path_local=${1:-"$HOME/data/"}
data_path_remote=${2:-"/home/pi/data/"}

for remote_host in "rpi-red60" "rpi-yellow61" "rpi-blue62"  # ! CHANGE names, e.g. to .ssh/config host definitions
do
  printf "\n\n\n======================================= $remote_host \n"

  local_data_for_this_remote="${data_path_local}/video/${remote_host}/"
  printf $local_data_for_this_remote
  mkdir -p "$local_data_for_this_remote"

  # COPY: remote -> local
  rsync -av --info=progress2 "${remote_host}:${data_path_remote}" $local_data_for_this_remote

done
