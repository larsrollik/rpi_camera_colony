# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import argparse
import logging
import subprocess
import time

import rpi_camera_colony
from rpi_camera_colony.config.config import load_config


def execute_in_commandline(cmd=None, return_std=False, **kwargs):
    if return_std:
        output_location = subprocess.PIPE
    else:
        output_location = subprocess.DEVNULL

    kwargs.update(
        {
            "stdout": output_location,
            "stderr": subprocess.PIPE,
        }
    )
    return subprocess.Popen(
        cmd,
        **kwargs,
    )


class RemoteAcquisitionControl(object):
    """Manager to communicate with remote RPi. Instantiates PiAcquisitionControl on RPi."""

    instance_name = None
    control_socket_wrapper = None
    auto_init = None

    _connected = False
    _settings = None

    remote_python_interpreter = None
    remote_python_entrypoint = None

    def __init__(
        self,
        instance_name=None,
        config_data=None,
        control_socket_wrapper=None,
        auto_init=False,
        **kwargs,
    ):
        super(RemoteAcquisitionControl, self).__init__()

        if config_data is None and "config_file" not in kwargs:
            raise ValueError("Require either config_data object or config_file path.")

        self.instance_name = instance_name
        self.config_data = config_data or load_config(
            config_path=kwargs.get("config_file")
        )
        self.control_socket_wrapper = control_socket_wrapper

        self.remote_python_interpreter = self.config_data["general"].get(
            "remote_python_interpreter"
        )
        self.remote_python_entrypoint = self.config_data["general"].get(
            "remote_python_entrypoint"
        )
        self.remote_address = self.config_data["controllers"][self.instance_name].get(
            "address"
        )

        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)
                logging.debug(f"Setting attribute {attr} to {value}")

        if auto_init:
            self.initialise()

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        self._connected = value

        if self.connected:
            self.transmit_settings()
        else:
            self.pkill_remote()

    @property
    def config_data(self):
        return self._settings

    @config_data.setter
    def config_data(self, value=None):
        self._settings = value if hasattr(value, "keys") else None
        self.transmit_settings()

    def send_command(self, cmd_type="config", message_dict=None):
        message = {"type": cmd_type}
        message.update(message_dict)
        self.control_socket_wrapper.send_multipart_json(
            recipient=self.instance_name, message=message
        )

    def transmit_settings(self):
        if not self._settings:
            # logging.warning("Tried to transmit config_data, but cannot find any.")
            return

        if not self._connected:
            # logging.debug("Remote is closed.")
            return

        settings_for_this_instance = self.config_data["controllers"].get(
            self.instance_name
        )

        # Patch general overwrite into controller settings
        general_setting_has_priority = self.config_data["general"][
            "general_setting_has_priority"
        ]
        general_settings_to_patch_into_controller = self.config_data["general"][
            "general_settings_to_patch_into_controller"
        ]
        if general_setting_has_priority:
            for key in general_settings_to_patch_into_controller:
                overwrite_value = self.config_data["general"].get(key)
                settings_for_this_instance.update({key: overwrite_value})

        # Send
        self.send_command(
            cmd_type="config",
            message_dict=settings_for_this_instance,
        )

    def _make_pi_command_base_list(self):
        username = self.config_data["general"].get("rpi_username", "pi")
        return [
            "ssh",
            username + "@" + self.remote_address,
            "sudo",
            "nohup",
        ]

    def initialise(self):
        if self.connected:
            logging.debug("Already initialised the remote acquisition.")
            return

        self.pkill_remote()
        time.sleep(1)
        cmd = self._make_pi_command_base_list() + [
            self.remote_python_interpreter,
            "-m",
            "rpi_camera_colony.acquisition",
            "--instance-name",
            self.instance_name,
            "--acquisition-name",
            self.config_data["general"]["acquisition_name"],
            "--acquisition-group",
            self.config_data["general"]["acquisition_group"],
            "--data-path",
            self.config_data["general"]["remote_data_path"],
            "--max-acquisition-time",
            self.config_data["general"]["max_acquisition_time"],
            "--log-ip",
            self.config_data["log"]["address"],
            "--log-port",
            self.config_data["log"]["port"],
            "--log-level",
            self.config_data["log"]["level"],
            "--control-stream-ip",
            self.config_data["control"]["address"],
            "--control-stream-port",
            self.config_data["control"]["port"],
            # "--framerate",
            # self.config_data["controllers"][self.instance_name]["framerate"],
            # "--resolution",
            # self.config_data["controllers"][self.instance_name]["resolution"],
        ]
        cmd = [str(c) for c in cmd]  # assert string
        execute_in_commandline(cmd=cmd)

        logging.debug(
            f"Initialised remote acquisition controller for: {self.remote_address} known as: {self.instance_name}."
        )

        self.connected = True

    def pkill_remote(self):
        cmd = self._make_pi_command_base_list() + ["pkill", "python"]
        execute_in_commandline(cmd=cmd, return_std=False)
        time.sleep(0.1)

    def start_acquisition(self):
        self.send_command(cmd_type="command", message_dict={"status": "reset"})
        self.send_command(cmd_type="command", message_dict={"status": "start"})

    def stop_acquisition(self):
        self.send_command(cmd_type="command", message_dict={"status": "stop"})
        time.sleep(0.5)

    def cleanup(self):
        try:
            self.send_command(cmd_type="command", message_dict={"status": "close"})
            time.sleep(0.5)
            self.connected = False
        except BaseException:
            print("FAILED TO CLEAN UP REMOTE CONTROLLER")

    def __del__(self):
        self.cleanup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()  # FIXME: check that not have to call connected=False before


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser_general = parser.add_argument_group("General")
    parser_general.add_argument(
        "--version", "-v", action="version", version=rpi_camera_colony.__version__
    )
    parser_ctrl = parser.add_argument_group("RemoteAcquisitionControl")
    parser_ctrl.add_argument(
        "--config_data-file",
        "-f",
        default="",
        type=str,
        help="Path to config_data file.",
    )
    parser_ctrl.add_argument(
        "--instance-name",
        "-id",
        default="test_camera",
        type=str,
        help="Remote instance name to pick relevant section from config_data.",
    )
    parser_ctrl.add_argument(
        "--remote-python-interpreter",
        "-py",
        default="/home/pi/miniconda3/envs/py36/bin/python",
        type=str,
        help="Path to remote python interpreter. Can be simply 'python' for the default one.",
    )
    parser_ctrl.add_argument(
        "--command-socket",
        "-s",
        default=None,
        type=str,
        help="Socket address for command stream. "
        "Required on command line, but if object used in script, can also take zmq command_socket.",
    )
    parser_ctrl.add_argument(
        "--auto-init",
        "-i",
        default=False,
        type=bool,
        help="Automatically initialised the remote instance and communication channels.",
    )
    args = parser.parse_args()

    remote_acq_ctrl = RemoteAcquisitionControl(**vars(args))

    remote_acq_ctrl.initialise()
    remote_acq_ctrl.start_acquisition()
    time.sleep(10)
    remote_acq_ctrl.stop_acquisition()
    remote_acq_ctrl.cleanup()

    print("Exiting Remote Acq Ctrl.")
