#!/bin/bash
# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
#
# Use in commandline as:
#     sh upload_data.sh

data_dir=${1:-"$HOME/data/"}
remote_data_dir=${2:-"larsr@ssh.swc.ucl.ac.uk:/nfs/winstor/sjones/users/lars/ACQUISITION/setup_npx/"}


#source /home/lbr/code/rpi_camera_colony/rpi_camera_colony/scripts/convert_h264_to_mp4.sh

rsync -av --info=progress2 $data_dir $remote_data_dir
