# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import logging

level = "DEBUG"
logger = logging.getLogger()
logger.setLevel(getattr(logging, level))

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s"
    " - %(processName)s %(filename)s:%(lineno)s"
    " - %(message)s"
)
formatter.datefmt = "%Y-%m-%d %H:%M:%S %p"

stream_handler = logging.StreamHandler()
stream_handler.setLevel(getattr(logging, level))
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

__version__ = "0.3.1.dev0"
__author__ = "Lars B. Rollik"
