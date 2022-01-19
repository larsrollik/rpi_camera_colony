# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import json
import logging
import os
import socket
from pathlib import Path

from configobj import ConfigObj
from validate import Validator
from zmq.log.handlers import PUBHandler

from rpi_camera_colony.log import log_level_name_to_value


def load_config(config_path=None, config_spec_path=None):
    if not config_path:
        raise ValueError("Need to specify a path for config_path.")

    config_path = Path(os.path.expanduser(config_path))
    if not config_path.exists():
        raise FileNotFoundError(f"File {config_path} not found.")

    if not config_spec_path:
        config_spec_path = Path(__file__).parent / "spec.config"

    config_spec_path = Path(os.path.expanduser(config_spec_path))
    if not config_spec_path.exists():
        raise FileNotFoundError(f"File {config_spec_path} not found.")

    config = ConfigObj(
        infile=str(config_path),
        configspec=str(config_spec_path),
        unrepr=True,
        list_values=True,
    )

    validation_success = config.validate(Validator(), copy=True)
    if not validation_success:
        logging.info("Configuration file FAILED validation.")
    else:
        if log_level_name_to_value("DEBUG") >= log_level_name_to_value(
            config["log"]["level"]
        ):
            logging.debug(
                f"Config validation was successful for: \n {json.dumps(config.dict(), sort_keys=True, indent=4)}"
            )

    return config


def setup_logging_via_socket(
    level="DEBUG", address_or_socket=None, root_topic="logging_root_topic"
):
    logging_handler = PUBHandler(interface_or_socket=address_or_socket)
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(levelname)s"
        " - %(processName)s %(filename)s:%(lineno)s"
        " - %(message)s"
    )
    formatter.datefmt = "%Y-%m-%d %H:%M:%S"
    logging_handler.setFormatter(formatter)
    logging_handler.root_topic = str(
        root_topic
    )  # ARM pyzmq version doesn't have root_topic as init argument

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))
    logger.addHandler(logging_handler)
    logging.info(
        f"Logging initialised for {address_or_socket} with topic {root_topic} and level {level}."
    )


def get_local_ip_address():
    """https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def get_interface_mac_address(interface="eth0"):
    try:
        f = open(f"/sys/class/net/{interface}/address")
        mac = f.read().strip("\n")
    except BaseException:
        mac = "00:00:00:00:00:00"

    return mac
