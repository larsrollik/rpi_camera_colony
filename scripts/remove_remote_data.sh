#!/bin/bash
# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
#
# Use as:
#     remove_remote_data REMOTE_data_path
# ! Change rpi host names for your setup

# Default arguments
data_path_remote=${1:-"/home/pi/data/"}

for remote_host in "rpi-red60" "rpi-yellow61" "rpi-blue62"  # .ssh/config host definitions
do
  printf "\n\n\n======================================= $remote_host \n"

  # REMOVE remote data
  remove_cmd="${remote_host} sudo nohup rm -rf ${data_path_remote}/*"
  printf $remove_cmd
  ssh $remove_cmd
done
