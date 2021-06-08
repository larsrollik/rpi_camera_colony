# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import logging
import sys
import time
from multiprocessing import Process
from multiprocessing import Queue

from rpi_camera_colony.control.conductor import Conductor
from rpi_camera_colony.control.conductor import parse_args_for_conductor


class ConductorAsProcess(Process):
    interrupt_queue = None
    conductor = None

    def __init__(self, controller_args=None, interrupt_queue=None):
        super(ConductorAsProcess, self).__init__()

        self.controller_args = controller_args
        self.interrupt_queue = interrupt_queue

        self.conductor = Conductor(**self.controller_args)

    def run(self) -> None:
        self.conductor.start_acquisition()

        while self.interrupt_queue.empty():
            time.sleep(1)

        self.conductor.stop_acquisition()
        self.conductor.cleanup()
        sys.exit(0)


if __name__ == "__main__":
    # Minimal example for sandboxing Conductor in separate process
    args_for_conductor = parse_args_for_conductor()
    interrupt_queue = Queue()  # Send value into this queue to stop the Conductor

    conductor_process = ConductorAsProcess(
        controller_args=args_for_conductor, interrupt_queue=interrupt_queue
    )
    conductor_process.run()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt. Cleaning up and exiting.")
            conductor_process.join()
            logging.info("Control processed joined and exiting. Good bye.")
