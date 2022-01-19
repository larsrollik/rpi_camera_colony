# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import argparse
import logging
import platform
import sys
import time

from tqdm import tqdm

from rpi_camera_colony.control.conductor import Conductor
from rpi_camera_colony.log import setup_logging_control


def parse_args_for_calibration():
    parser = argparse.ArgumentParser(
        description="RPi Camera Colony: Calibration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    return parser.parse_args()


def main():
    args = parse_args_for_calibration()
    setup_logging_control()

    progress = tqdm(
        total=7200,
        desc="Recording progress",
        unit="seconds",
        bar_format="{desc}: {percentage:3.0f}%| | {n:.2f}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]",
    )

    conductor = Conductor(
        config_file=args.config_file,
        acquisition_name=args.acquisition_name,
        auto_init=False,
        run_for_calibration=True,
    )

    conductor.start_acquisition()

    while conductor.active:
        try:
            time.sleep(1)
            progress.update(n=1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt. Cleaning up and exiting.\n")
            conductor.stop_acquisition()
            conductor.cleanup()

    progress.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
