# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import argparse
import logging
import time
from pathlib import Path

import zmq

from rpi_camera_colony.acquisition.remote_control import RemoteAcquisitionControl
from rpi_camera_colony.config.config import load_config
from rpi_camera_colony.tools.comms import find_available_port
from rpi_camera_colony.tools.comms import ListenerStream
from rpi_camera_colony.tools.comms import SocketCommunication
from rpi_camera_colony.tools.files import close_file_safe
from rpi_camera_colony.tools.files import get_datestr
from rpi_camera_colony.tools.log import log_level_name_to_value


def parse_args_for_conductor():
    parser = argparse.ArgumentParser(
        description="Input arguments",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config-file",
        "-c",
        type=str,
        default=Path(__file__).parent.parent / "config/example.config",
        help="Settings file",
    )
    parser.add_argument(
        "--acquisition-name",
        "-n",
        type=str,
        default="_test_rcc_conductor_parser__" + get_datestr(),
        help="Acquisition name [only name; path on Conductor should be defined in config]",
    )
    return parser.parse_args()


class Conductor(object):
    active = True

    config_data = None
    config_file = None
    acquisition_group = ""
    acquisition_name = None
    acquisition_time = None

    _acquisition_controllers = {}
    acquiring = False

    auto_init = False
    auto_init_remote = True

    _logging_socket = None
    _logging_stream_callback = None
    _log_level = "INFO"
    _log_to_console = True
    _log_to_file = False
    _log_file = None

    _control_socket = None
    _comms_stream = None

    __cleaned_up = False

    def __init__(
        self,
        config_file=None,
        acquisition_group="",
        acquisition_name=None,
        acquisition_time=None,
        logging_stream_callback=None,
        auto_init=False,
        auto_init_remote=True,
        delay_for_networking=4,
        delay_for_remote_instance=6,
    ):
        """Create new Acquisition Conductor."""
        super(Conductor, self).__init__()

        self.config_file = config_file
        self._load_config()

        self._log_level = self.config_data["log"]["level"]
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, self._log_level))

        self.acquisition_group = acquisition_group or self.acquisition_group
        self.acquisition_name = acquisition_name or self.acquisition_name
        self.acquisition_time = acquisition_time or self.acquisition_time
        self._logging_stream_callback = (
            logging_stream_callback or self._callback_receiver
        )
        self.auto_init = auto_init
        self.auto_init_remote = auto_init_remote

        # Process arguments
        if not self.acquisition_name:
            self.acquisition_name = self.config_data["general"].get(
                "acquisition_name", "default_acq_name_get"
            )

        acq_name_parts = self.acquisition_name.split("__")
        if not self.acquisition_group:
            self.acquisition_group = acq_name_parts[0]

        self.acquisition_time = (
            acq_name_parts[1] if len(acq_name_parts) > 1 else get_datestr()
        )

        self.config_data["general"]["acquisition_group"] = self.acquisition_group
        self.config_data["general"]["acquisition_name"] = self.acquisition_name
        self.config_data["general"]["acquisition_time"] = self.acquisition_time

        for c in self.config_data["controllers"].keys():
            self.config_data["controllers"][c][
                "acquisition_time"
            ] = self.acquisition_time
            self.config_data["controllers"][c][
                "acquisition_group"
            ] = self.acquisition_group

        self._log_to_file = self.config_data["log"].get("log_to_file")
        self._log_to_console = self.config_data["log"].get("log_to_console")

        # Execute main components
        self._open_network_comms()
        logging.info(f"Waiting {delay_for_networking}s for networking to come up..")
        time.sleep(delay_for_networking)

        self._make_acquisition_controllers(auto_init=auto_init_remote)
        logging.info(
            f"Waiting {delay_for_remote_instance}s for remote instance to listen.."
        )
        time.sleep(delay_for_remote_instance)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __del__(self):
        self.cleanup()

    def _load_config(self):
        self.config_data = load_config(config_path=self.config_file)

    def _open_network_comms(self):
        # Find available socket ports
        start_port = int(self.config_data["log"].get("port"))
        address = self.config_data["log"].get("address")
        available_port_logging = find_available_port(
            start_port=start_port, ip_address=address
        )
        start_port = int(self.config_data["control"].get("port"))
        address = self.config_data["control"].get("address")
        available_port_control = find_available_port(
            start_port=start_port, ip_address=address
        )

        assert available_port_logging is not None and available_port_control is not None
        self.config_data["log"]["port"] = available_port_logging
        self.config_data["control"]["port"] = available_port_control

        # Logging
        self._logging_socket = SocketCommunication(
            address=self.config_data["log"].get("address"),
            port=self.config_data["log"].get("port"),
            pattern="SUB",
            bind=True,
            auto_open=True,
        )
        # Control
        self._control_socket = SocketCommunication(
            address=self.config_data["control"].get("address"),
            port=self.config_data["control"].get("port"),
            pattern="PUB",
            bind=True,
            auto_open=True,
        )
        # Stream ioloop
        self._comms_stream = ListenerStream(
            socket_dict={
                "logging": self._logging_socket.socket,
                "control": self._control_socket.socket,
            },
            recv_callback_dict=self._callback_receiver,
        )
        self._comms_stream.start()

        if self._log_to_file is not None and self._log_to_file:
            log_file = ".".join(
                [self.config_data["log"].get("log_file"), get_datestr(), "log"]
            )
            self._log_file = open(log_file, "w")
            self._write_to_log(f"# Log for: {self.acquisition_name}\n")
            logging.info(f"Logging remote messages to: {self._log_file.name}")

    def _callback_receiver(self, message=None):
        topic, message = [m.decode() for m in message]
        instance_name, log_level_on_remote = topic.split(".")
        remote_dt, remote_level, remote_position, remote_message = message.split(" - ")
        out_string = (
            f"REMOTE: {instance_name} - {remote_position} - {remote_message}".strip(
                "\n"
            )
        )

        message_level = log_level_name_to_value(name=log_level_on_remote)
        target_level = log_level_name_to_value(name=self._log_level)
        if self._log_to_console and message_level >= target_level:
            logging.info(out_string)

        if (
            self._log_to_file is not None
            and self._log_to_file
            and self._log_file is not None
        ):
            self._write_to_log(out_string)

    def _write_to_log(self, out_string):
        if not self._log_file.closed:
            self._log_file.write(f"{out_string}\n")
            self._log_file.flush()

    def _make_acquisition_controllers(self, auto_init=True):
        """Make local objects to handle interaction with remote acquisition controller."""
        for instance_name, _ in self.config_data["controllers"].items():
            self._acquisition_controllers[instance_name] = RemoteAcquisitionControl(
                instance_name=instance_name,
                config_data=self.config_data,
                control_socket_wrapper=self._control_socket,
                auto_init=auto_init,
            )

    def initialise_acquisition_conductors(self):
        """Start up remote acquisition & transmit config_data in preparation for acquisition."""
        for _, acq in self._acquisition_controllers.items():
            acq.initialise()

    def start_acquisition(self):
        """Start acquisition."""
        for _, acq in self._acquisition_controllers.items():
            acq.start_acquisition()

        self.acquiring = True

    def stop_acquisition(self):
        """Stop acquisition."""

        if not self.acquiring:
            logging.info("Acquisition was not running.")

        if not bool(self._acquisition_controllers):
            logging.info("")
            return

        for _, acq in self._acquisition_controllers.items():
            acq.stop_acquisition()

        self.acquiring = False

    def cleanup(self):
        """Post-acquisition tasks before exiting."""
        if self.__cleaned_up:
            return

        if (
            self._log_to_file is not None
            and self._log_to_file
            and self._log_file is not None
        ):
            close_file_safe(self._log_file)

        if self.acquiring:
            self.stop_acquisition()

        for _, acq in self._acquisition_controllers.items():
            acq.cleanup()

        self._acquisition_controllers = []
        if self._comms_stream is not None:
            self._comms_stream.stop()
            time.sleep(0.5)
            self._comms_stream = None

        self._logging_socket.close()
        self._control_socket.close()

        self.__cleaned_up = True
        self.active = False

        logging.info("Exiting RCC Conductor.")
