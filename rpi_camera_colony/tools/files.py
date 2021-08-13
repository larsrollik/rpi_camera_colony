# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import logging
import os
import time
from datetime import datetime


def get_datestr():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_recording_file_names(
    path=None, package_id="rcc", ext_sep=".", video_ext="h264"
):
    # basepath, _ = os.path.splitext(str(path))
    basepath = str(path)
    dt = get_datestr()
    return {
        "video": ext_sep.join(
            [basepath, dt, package_id, "video", str(video_ext).replace(".", "")]
        ),
        "ttl_out": ext_sep.join(
            [basepath, dt, package_id, "timestamps_ttl_out", "csv"]
        ),
        "ttl_in": ext_sep.join([basepath, dt, package_id, "timestamps_ttl_in", "csv"]),
        "metadata": ext_sep.join([basepath, dt, package_id, "metadata", "json"]),
    }


def close_file_safe(file_handle):
    try:
        name = file_handle.name
    except BaseException:
        name = "not a file object"

    try:
        # Relevant actions
        file_handle.flush()
        os.fsync(file_handle.fileno())
        file_handle.close()
        file_handle = None
        # Report success
        logging.debug(f"Closed file:{name}")
    except BaseException:
        logging.debug(f"FAILED TO CLOSE FILE:{name}")


class DummyFileObject(object):
    def __init__(self, *args, **kwargs):
        pass

    def write(self):
        pass

    def flush(self):
        pass

    def open(self):
        pass

    def close(self):
        pass
