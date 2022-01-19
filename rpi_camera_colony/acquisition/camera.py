# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import logging
import time

try:
    import RPi.GPIO as GPIO
    import picamera
    from picamera import mmal
except ImportError:
    raise ImportError(
        "Can only run camera module on Raspberry Pi with RPi.GPIO and picamera packages installed."
    )
from rpi_camera_colony.files import close_file_safe
from rpi_camera_colony.files import DummyFileObject

GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)


class VideoEncoder(picamera.PiVideoEncoder):
    """https://picamera.readthedocs.io/en/release-1.13/recipes2.html#custom-encoders"""

    frame_count = 0
    ttl_count = 0

    _ttl_out_pin = 8  # TODO: set to final value
    _ttl_out_duration = 0.001  # 1ms

    def __init__(self, *args, **kwargs):
        super(VideoEncoder, self).__init__(*args, **kwargs)

        for arg, val in kwargs.items():
            if hasattr(self, arg):
                setattr(self, arg, val)

    @property
    def ttl_out_pin(self):
        return self._ttl_out_pin

    @ttl_out_pin.setter
    def ttl_out_pin(self, value):
        logging.debug(f"Setting TTL out pin to {value}")
        self._ttl_out_pin = value
        if self.ttl_out_pin is not None:
            GPIO.setup(self.ttl_out_pin, GPIO.OUT, initial=GPIO.LOW)
            GPIO.output(self.ttl_out_pin, False)

    @property
    def ttl_out_duration(self):
        return self._ttl_out_duration

    @ttl_out_duration.setter
    def ttl_out_duration(self, value):
        logging.debug(f"Setting TTL out duration to {value}")
        self._ttl_out_duration = value

    def start(self, output, motion_output=None):
        super(VideoEncoder, self).start(output, motion_output)

    def close(self):
        super(VideoEncoder, self).close()

        if self.ttl_count != self.frame_count:
            logging.warning(
                f"Frame count ({self.frame_count}) and TTL count ({self.ttl_count}) do not match."
            )

    def _callback_write(self, buf, key=None):
        if (buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_FRAME_END) and not (
            buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_CONFIG
        ):
            if self.ttl_out_pin is not None:
                GPIO.output(self.ttl_out_pin, True)
                time.sleep(self.ttl_out_duration)
                GPIO.output(self.ttl_out_pin, False)

                self.ttl_count += 1

            self.parent._write_timestamps_frame_ttl_out(buf.pts, self.parent.timestamp)
            self.frame_count += 1

        return super(VideoEncoder, self)._callback_write(buf)


class Camera(picamera.PiCamera):
    _ttl_out_pin = 8
    _ttl_in_pin = 16
    _ttl_out_duration = 0.001

    file_timestamps_ttl_out = None
    file_timestamps_ttl_in = None

    clock_mode = "raw"

    def __init__(
        self,
        framerate=30,
        resolution=(1600, 1200),
        **kwargs,
    ):
        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)
                logging.debug(f"Set {self}, attr {attr} to value {value}")

        super(Camera, self).__init__(
            framerate=framerate,
            resolution=resolution,
            clock_mode=self.clock_mode,
        )

    @property
    def ttl_out_pin(self):
        return self._ttl_out_pin

    @ttl_out_pin.setter
    def ttl_out_pin(self, value):
        self._ttl_out_pin = value

    @property
    def ttl_out_duration(self):
        return self._ttl_out_duration

    @ttl_out_duration.setter
    def ttl_out_duration(self, value):
        self._ttl_out_duration = value

    @property
    def ttl_in_pin(self):
        return self._ttl_in_pin

    @ttl_in_pin.setter
    def ttl_in_pin(self, value):
        self._ttl_in_pin = value

    def _get_video_encoder(self, camera_port, output_port, format, resize, **options):
        video_encoder = VideoEncoder(
            self, camera_port, output_port, format, resize, **options
        )
        video_encoder.ttl_out_pin = self.ttl_out_pin
        video_encoder.ttl_out_duration = self.ttl_out_duration
        return video_encoder

    def __del__(self):
        GPIO.cleanup()
        del self

    def _write_timestamps_ttl_in(self, x=None):
        if self.file_timestamps_ttl_in is not None:
            self.file_timestamps_ttl_in.write(f"{self.timestamp}\n")
            logging.info(f"TTL-in detected at {self.timestamp}")

    def _write_timestamps_frame_ttl_out(self, cam_ts, frame_ts):
        if self.file_timestamps_ttl_out is not None:
            self.file_timestamps_ttl_out.write(f"{cam_ts},{frame_ts}\n")

    def start_recording(self, output_files=None, **kwargs):
        if isinstance(output_files["video"], DummyFileObject):
            logging.debug("Not allowed to write output files.")
            self.ttl_out_pin = None
            self.ttl_in_pin = None

        if self.ttl_out_pin is not None:
            # Open TTL file and write header
            self.file_timestamps_ttl_out = open(output_files["ttl.out"], "w")
            self.file_timestamps_ttl_out.write("# timestamp_frame, timestamp_ttl\n")

        if self.ttl_in_pin is not None:
            logging.debug(f"Setting TTL in pin to {self.ttl_in_pin}")
            # Add event detection callback
            GPIO.setup(self.ttl_in_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(
                self.ttl_in_pin, GPIO.RISING, self._write_timestamps_ttl_in
            )
            # Open TTL file and write header
            self.file_timestamps_ttl_in = open(output_files["ttl.in"], "w")
            self.file_timestamps_ttl_in.write("# timestamp_frame\n")

        super(Camera, self).start_recording(output=str(output_files["video"]), **kwargs)

    def stop_recording(self):
        if self.ttl_in_pin is not None:
            GPIO.remove_event_detect(self.ttl_in_pin)

        try:
            super(Camera, self).stop_recording()
        except BaseException:
            logging.error("CAMERA STOP EXCEPTION")

        # Close TTL files
        if self.file_timestamps_ttl_out is not None:
            close_file_safe(file_handle=self.file_timestamps_ttl_out)
        if self.file_timestamps_ttl_in is not None:
            close_file_safe(file_handle=self.file_timestamps_ttl_in)

    def preview_static(self, warmup_delay=3, alpha=255):
        if self.preview is not None:
            self.stop_preview()

        self.awb_mode = "auto"
        self.exposure_mode = "auto"

        self.start_preview(alpha=alpha)
        time.sleep(warmup_delay)

        awb_gains = self.awb_gains
        self.awb_mode = "off"
        self.awb_gains = awb_gains

        self.shutter_speed = self.exposure_speed
        self.exposure_mode = "off"

        logging.debug(
            f"Camera previewing & updated awb_gains={awb_gains}, shutter_speed={self.shutter_speed}"
        )
