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
fps=${2:-60}

find $target_path -type f -name "*.h264" -print0 |
  while IFS= read -r -d '' file; do
  converted_file=${file}.mp4

    if stat -t $converted_file >/dev/null 2>&1
    then
      :	# converted_file exists, do nothing
    else
      printf "\n ==>> Converting file: $f"
      MP4Box -fps $fps -add $file $converted_file
    fi
  done
