# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import logging
import subprocess
import sys
import time
from multiprocessing import Process
from multiprocessing import Queue
from threading import Thread

import psutil
from PyQt5.QtCore import QThread

from rpi_camera_colony.control.conductor import Conductor
from rpi_camera_colony.control.conductor import parse_args_for_conductor
from rpi_camera_colony.tools.comms import execute_in_commandline


def _get_default_python_path():
    return (
        execute_in_commandline(["which", "python"], return_std=True)
        .stdout.read()
        .decode("utf-8")
        .strip("\n")
    )


class ConductorAsSubprocess(object):
    python_path = None
    conductor_args = None
    conductor_args_list = []
    command = None
    conductor_process = None

    def __init__(
        self,
        conductor_args=dict,
        python_path=None,
    ):
        super(ConductorAsSubprocess, self).__init__()

        self.conductor_args = conductor_args

        if python_path is None:
            self.python_path = _get_default_python_path()
        else:
            self.python_path = str(python_path)

        for k, v in self.conductor_args.items():
            arg = "--" + str(k).replace("_", "-")
            self.conductor_args_list.extend([arg, v])

        self.command = [
            self.python_path,
            "-m",
            "rpi_camera_colony.control.main",
        ] + self.conductor_args_list
        self.conductor_process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.debug(
            f"Launched subprocess for rcc Conductor with pid={self.conductor_process.pid}"
        )

    # def __enter__(self):
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.shutdown()

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        if self.conductor_process is not None:
            process_handle = psutil.Process(pid=self.conductor_process.pid)
            psutil.wait_procs(procs=process_handle.children(), timeout=1)
            process_handle.kill()


class ConductorAsProcess(Process):
    daemon = True
    kill_queue = None
    conductor = None

    def __init__(self, conductor_args=None, kill_queue=None):
        super(ConductorAsProcess, self).__init__()

        self.conductor_args = conductor_args
        self.kill_queue = kill_queue

        self.conductor = Conductor(**self.conductor_args)
        self.conductor.start_acquisition()

    def run(self) -> None:
        while self.kill_queue.empty():
            time.sleep(1)

        self.conductor.stop_acquisition()
        self.conductor.cleanup()
        sys.exit(0)

    def stop(self):
        if self.kill_queue is not None:
            self.kill_queue.put(True)

    def __del__(self):
        if self.conductor is not None:
            self.conductor.stop_acquisition()
            self.conductor.cleanup()
            del self.conductor


if __name__ == "__main__":
    # Minimal example for sandboxing Conductor in separate process
    args_for_conductor = parse_args_for_conductor()
    kill_queue = Queue()  # Send value into this queue to stop the Conductor

    conductor_process = ConductorAsProcess(
        conductor_args=args_for_conductor, kill_queue=kill_queue
    )
    conductor_process.run()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt. Cleaning up and exiting.")
            conductor_process.join()
            logging.info("Control processed joined and exiting. Good bye.")
