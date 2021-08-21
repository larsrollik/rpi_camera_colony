# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import json
import logging
from pathlib import Path

from rpi_camera_colony.config.config import get_local_ip_address
from rpi_camera_colony.tools.comms import ListenerStream
from rpi_camera_colony.tools.comms import SocketCommunication
from rpi_camera_colony.tools.files import DummyFileObject
from rpi_camera_colony.tools.files import get_datestr
from rpi_camera_colony.tools.files import make_recording_file_names

try:
    from rpi_camera_colony.acquisition.camera import Camera
except ImportError:
    logging.warning(
        "Will exit on error during PiAcquisitionControl init due to missing Camera import."
    )
    raise ImportError("Failed to import picamera")


class PiAcquisitionControl(object):
    active = True

    camera = None
    resolution = (640, 480)
    framerate = 90

    control_stream = None
    control_stream_ip = None
    control_stream_port = None

    instance_name = get_local_ip_address()
    data_path = "/home/pi/data/"
    acquisition_name = "test_recording"
    acquisition_group = ""
    acquisition_time = get_datestr()
    acquisition_file_base = None
    acquisition_files = None
    acquisition_settings = {}
    video_quality = 23
    save_data = True

    def __init__(
        self,
        instance_name=None,
        data_path=None,
        acquisition_group=None,
        acquisition_name=None,
        control_stream_ip=None,
        control_stream_port=None,
        **kwargs,
    ):
        super(PiAcquisitionControl, self).__init__()

        self.instance_name = instance_name or self.instance_name
        self.data_path = data_path or self.data_path
        self.acquisition_group = acquisition_group or self.acquisition_group
        self.acquisition_name = acquisition_name or self.acquisition_name
        self.control_stream_ip = control_stream_ip or self.control_stream_ip
        self.control_stream_port = control_stream_port or self.control_stream_port

        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)
                logging.debug(f"Set {self}, attr {attr} to value {value}")

        self.camera = Camera(**kwargs)
        self.camera.preview_static()

        # Make command_socket to receive control commands & subscribe to own channel
        self.control_socket = SocketCommunication(
            address=self.control_stream_ip,
            port=self.control_stream_port,
            pattern="SUB",
            bind=False,
            subscribe_to=self.instance_name,
        )
        self.control_stream = ListenerStream(
            socket_dict={1: self.control_socket.socket},
            recv_callback_dict=self._received_command,
        )
        self.control_stream.start()
        logging.debug("PiAcquisitionControl instantiated.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.camera is not None:
            if self.camera.preview is not None:
                self.camera.stop_preview()
            if self.camera.recording:
                self.camera.stop_recording()
            del self.camera
            self.camera = None

        self.control_stream.stop()
        logging.debug("Exiting PiAcquisitionControl.")

    def shutdown(self):
        """For use within contextmanager while loop: while this_object.active"""
        self.active = False

    def _write_metadata_file(self):
        # Note: Requires all variables to be public !
        metadata = {
            k: v
            for k, v in vars(self).items()
            if not isinstance(v, SocketCommunication)
            and not isinstance(v, ListenerStream)
            and not isinstance(v, type(self.camera))
        }

        save_path = self.acquisition_files["metadata"]
        with open(save_path, "w") as f:
            json.dump(metadata, f, indent=4, sort_keys=True)

        if not Path(save_path).exists():
            logging.error(f"Could not write metadata file to {save_path}")

    def _make_acquisition_paths(self):
        # Paths
        file_base = ".".join([self.acquisition_name, self.instance_name])
        acquisition_file_base_path = (
            Path(self.data_path)
            / self.acquisition_group
            / self.acquisition_name
            / file_base
        )
        acquisition_file_base_path.parent.mkdir(parents=True, exist_ok=True)
        if not acquisition_file_base_path.parent.exists():
            err_msg = f"Tried to make dir {str(acquisition_file_base_path.parent)}, but not found on check."
            logging.error(err_msg)
            raise FileNotFoundError(err_msg)
        self.acquisition_file_base = str(acquisition_file_base_path)
        self.acquisition_files = make_recording_file_names(
            path=self.acquisition_file_base,
        )
        logging.debug(
            f"Files:\n{json.dumps(self.acquisition_files, sort_keys=True, indent=4)}"
        )

    def _received_command(self, command):
        command = [c.decode() for c in command]
        recipient, message_dict_str = command
        message = json.loads(message_dict_str, encoding="utf-8")

        ms = message.get("status", "")
        logging.info(f"Received: {message['type']} {'>' if ms else ''} {ms}")

        if message["type"] == "command":
            self._update_camera_status(new_status=message["status"])
        elif message["type"] == "config":
            self._update_settings(config_data=message)

    def _update_settings(self, config_data=None):
        self.acquisition_settings = config_data

        for setting_name, setting_value in config_data.items():
            # Camera config_data
            if hasattr(self.camera, setting_name):
                setattr(self.camera, setting_name, setting_value)
                logging.debug(f"setattr(self.camera, {setting_name}, {setting_value})")

            # PiAcquisitionControl config_data
            if hasattr(self, setting_name):
                setattr(self, setting_name, setting_value)
                logging.debug(f"setattr(self, {setting_name}, {setting_value})")

    def _update_camera_status(self, new_status="stop"):
        logging.debug(f"New status: {new_status} on {self.instance_name}")

        if new_status in ["preview", "reset"]:
            self.camera.preview_static()

        elif new_status in "start":

            if not self.save_data:
                logging.debug("Requested to run without saving data.")
                self.acquisition_files["video"] = DummyFileObject()
            else:
                self._make_acquisition_paths()
                self._write_metadata_file()

            self.camera.start_recording(
                output_files=self.acquisition_files,
                format="h264",
                quality=self.video_quality,
            )

        elif new_status in "stop":
            self.camera.stop_recording()

        elif new_status in "close":
            self.shutdown()
