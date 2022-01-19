# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import argparse
import logging
import platform
import sys
import time

import tqdm


def parse_args_for_calibration():
    parser = argparse.ArgumentParser(
        description="RPi Camera Colony: Calibration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    return parser.parse_args()


def main():
    NotImplementedError


if __name__ == "__main__":
    main()
