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

import rpi_camera_colony
from rpi_camera_colony.config.config import get_local_ip_address
from rpi_camera_colony.config.config import setup_logging_via_socket
from rpi_camera_colony.files import get_datestr
from rpi_camera_colony.network_communication import SocketCommunication


def parse_args_for_piacquisitioncontrol():
    parser = argparse.ArgumentParser(
        description="RPi Camera Colony: Acquisition",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_general = parser.add_argument_group("General")
    parser_general.add_argument(
        "--print-interval",
        "-pi",
        default=0.500,
        type=float,
        help="Print interval [seconds, float]",
    )
    parser_general.add_argument(
        "--version", "-v", action="version", version=rpi_camera_colony.__version__
    )
    parser_acq_ctrl = parser.add_argument_group("PiAcquisitionControl")
    parser_acq_ctrl.add_argument(
        "--instance-name",
        "-id",
        default=get_local_ip_address(),
        type=str,
        help="Name of camera.",
    )
    parser_acq_ctrl.add_argument(
        "--data-path",
        "-p",
        default="/home/pi/data/",
        type=str,
        help="Path where to store all recordings.",
    )
    parser_acq_ctrl.add_argument(
        "--acquisition-name",
        "-n",
        default="_test_rcc_acquisition_parser__" + get_datestr(),
        type=str,
        help="Base name for recording folder and files.",
    )
    parser_acq_ctrl.add_argument(
        "--acquisition-group",
        "-g",
        default="_test_acq_group",
        type=str,
        help="Base name for recording group folders.",
    )
    parser_acq_ctrl.add_argument(
        "--max-acquisition-time",
        "-t",
        default=2 * 3600,
        type=int,
        help="Maximum recording time, seconds.",
    )
    parser_acq_ctrl.add_argument(
        "--log-ip",
        "-lip",
        default="192.168.100.10",
        type=str,
        help="IP address for logging.",
    )
    parser_acq_ctrl.add_argument(
        "--log-port", "-lport", default=55555, type=str, help="Port for logging."
    )
    parser_acq_ctrl.add_argument(
        "--log-level",
        "-ll",
        default="DEBUG",
        type=str,
        help="Logging level, e.g. INFO, DEBUG, etc.",
    )
    parser_acq_ctrl.add_argument(
        "--control-stream-ip",
        "-cip",
        default="192.168.100.10",
        type=str,
        help="IP address for control stream.",
    )
    parser_acq_ctrl.add_argument(
        "--control-stream-port",
        "-cport",
        default=54545,
        type=int,
        help="Port for control stream",
    )
    parser_acq_ctrl.add_argument(
        "--auto-start",
        "-a",
        default=False,
        action="store_true",
    )
    parser_acq_ctrl.add_argument(
        "-fps",
        "--framerate",
        default=30,
        type=int,
        help="Framerate",
    )
    parser_acq_ctrl.add_argument(
        "-res",
        "--resolution",
        nargs="+",
        default=(1600, 1200),
        type=int,
        help="Resolution",
    )
    return parser.parse_args()


def main():
    args = parse_args_for_piacquisitioncontrol()

    # Exit if not on RPi -- makes parser outline available on non-RPi machines
    if "arm" not in platform.machine().lower():
        print("Not on Raspberry Pi. Exiting.")
        sys.exit(0)

    from rpi_camera_colony.acquisition.acquisition_control import PiAcquisitionControl

    # Set up logging & vars
    socket_wrapper = SocketCommunication(
        address=args.log_ip,
        port=args.log_port,
        pattern="PUB",
        bind=False,
        auto_open=True,
    )

    setup_logging_via_socket(
        level=args.log_level,
        address_or_socket=socket_wrapper.socket,
        root_topic=args.instance_name,
    )

    max_time = args.max_acquisition_time
    print_interval = args.print_interval
    progress = tqdm.tqdm(
        total=max_time,
        desc="Recording progress",
        unit="seconds",
        bar_format="{desc}: {percentage:3.0f}%| | {n:.2f}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]",
    )

    # Run acquisition
    with PiAcquisitionControl(**vars(args)) as c:

        time.sleep(2)
        start_time = time.time()

        if args.auto_start:
            logging.debug("AUTO STARTING PiAcquisitionControl.")
            c._update_camera_status(new_status="reset")
            c._update_camera_status(new_status="start")

        while (time.time() - start_time) < max_time and c.active:
            try:
                time.sleep(print_interval)
                progress.update(n=print_interval)
            except KeyboardInterrupt:
                c.active = False
                break
            except BaseException:
                c.active = False

    progress.close()
    logging.info("Exiting main script.")


if __name__ == "__main__":
    main()
