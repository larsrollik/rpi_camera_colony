#!/bin/bash
# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
#
# Use in commandline as:
#     convert_h264_to_mp4 LOCAL_path_to_video_folders video_framerate

# Default arguments
data_path_local=${1:-"$HOME/data/"}
fps=${2:-90}

find $data_path_local -name "*.h264" | parallel -j 8 MP4Box -fps $fps -add {1} {1}.mp4
