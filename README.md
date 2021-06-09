<!--
-*- coding: utf-8 -*-

 Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
 License: BSD 3-Clause
-->
<!-- Banners -->
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4916007.svg)](https://doi.org/10.5281/zenodo.4916007)
[![Website](https://img.shields.io/website?up_message=online&url=https%3A%2F%2Fgithub.com/larsrollik/rpi_camera_colony)](https://github.com/larsrollik/rpi_camera_colony)
[![PyPI](https://img.shields.io/pypi/v/rpi_camera_colony.svg)](https://pypi.org/project/rpi_camera_colony)
[![Wheel](https://img.shields.io/pypi/wheel/rpi_camera_colony.svg)](https://pypi.org/project/rpi_camera_colony)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

<!--
[![Development Status](https://img.shields.io/pypi/status/rpi_camera_colony.svg)](https://github.com/larsrollik/rpi_camera_colony)
[![Tests](https://img.shields.io/github/workflow/status/larsrollik/rpi_camera_colony/tests)](
    https://github.com/larsrollik/rpi_camera_colony/actions)

[![Python Version](https://img.shields.io/pypi/pyversions/rpi_camera_colony.svg)](https://pypi.org/project/rpi_camera_colony)
[![Downloads](https://pepy.tech/badge/rpi_camera_colony)](https://pepy.tech/project/rpi_camera_colony)
-->

# RPi Camera Colony
Central control for video acquisition with (many) Raspberry Pi cameras
---

Record videos in parallel with one or more remote-controlled Raspberry Pi (RPi) cameras. :movie_camera:

A single configuration file and a few lines of code allow specific and reproducible acquisition settings for groups of cameras.

**Example use with Python:**

```python
from rpi_camera_colony.control.conductor import Conductor

conductor = Conductor(settings_file="configuration_file")  # Manages remote RPi
conductor.start_acquisition()  # Starts recording on all remotes

...

conductor.stop_acquisition()  # Stops recording on all remotes

```
or on the commandline:
```shell
rcc_conductor  --config-data-file CONFIG_DATA_FILE  --acquisition-name ACQUISITION_NAME
```



## Features
#### A centralised control object
One central object handles all communication with the remote cameras and transmits the configuration settings to each.

#### A single configuration file to define reproducible multi-camera acquisition
Configuration parameters are centrally defined in an easy-to-read file format and then handed down to the cameras.

#### Flexible entrypoints
Multiple entrypoints for use in python scripts as well as in a single line on the commandline
Additionally, all levels are directly accessible: central Conductor, remote control handlers, and on the RPi the acquisition control (see below for details).



## Installation

### Python dependencies
- python `>= 3.6`
- pyzmq
- configobj
- tqdm

**On RPi only:**
- picamera
- RPi.GPIO

### Other useful packages
**For video conversion:**
- gpac  # contains MP4Box tool for video conversion



### Example hardware architecture

```text
  [outside world / internet]
              |
              |
      [central machine]
              |
              |
      [network switch]
      /   |     |    \
     |    |     |     | <- network connection
[rpi #1]  |     |     |     e.g. ethernet cables
          |     |     |
     [rpi #2]   |     |
                |     |
              [...]   |
                      |
                 [rpi #n]
```



#### Minimal hardware requirements
- Central machine, can be RPi itself (as it only holds the control object, but does no computation)
- Raspberry Pi
  1. Main RPi board + fast SD card (+ card reader if not available on another machine)
  2. RPi Camera (+lens?) (depends on your specific acquisition requirements)
  3. RPi power supply (RPi4 requires USB-C connector)
  4. Display cable (RPi4 requires mico-HDMI connector)
- Ethernet cables
- Network switch (if more than one RPi), e.g. any 1GB or faster



### Mapping between this package & hardware
**One** Conductor to instruct **all** RPi cameras via network communication between the RemoteAcquisitionControl and PiAcquisitionControl.
```text

    Hardware            <-->        Software


    [central machine]   <-->        Conductor
            |                           |
            |                       RemoteAcquisitionControl
            |                           |
           ...                         ...
            |                           |
       [rpi #n]         <-->        PiAcquisitionControl
                                        |
                                    Camera

```



### Raspberry Pi setup
0. Set up RPi hardware
    1. Install [Raspbian]
    2. Enable camera, GPIO interfaces, and ssh in `sudo raspi-config` options
    3. Connect hardware:
       1. Camera
       2. Network cable
       3. GPIO pin connection for TTL in/out (See [pinout.xyz] for **board mode** pins to use)

                Note: adjust pin numbers used in configuration file. Default are pin #8 for frame TTL outputs and #16 for inputs. Choose any free ground pins!

1. Install this package
    1. Set up python, e.g. with [miniconda]
    2. Clone this repository or use `distribute_code.sh` script (Replace hostnames for your RPi)
    3. Install with
        ```python
        pip install -e rpi_camera_colony[rpi]  # <- [rpi] argument install specific requirements!
        ```



### Central control machine setup
0. DHCP server on central computer. (Description only for Ubuntu)
    1. Set up static IP address on network interface that serves RPi colony via network switch, with e.g. `/etc/network/interfaces` or `netplan`
    2. Set up DHCP server with [isc-dhcp-server]

1. Set up python environment, e.g. with [miniconda]
2. Install this package
    1. Clone this repository
    2. Install with
        ```python
        pip install rpi_camera_colony
        ```



## Entrypoints & levels

### Easy access to central Conductor
```shell
rcc_conductor --help
```



### Use acquisition directly on RPi
```python
from rpi_camera_colony.acquisition.acquisition_control import PiAcquisitionControl
```
or
```shell
python rpi_camera_colony/acquisition --help
# or
python -m rpi_camera_colony.acquisition --help
# or
rcc_acquisition --help
```



### One-to-one mapping of local control to remote acquisition
```python
from rpi_camera_colony.acquisition.remote_control import RemoteAcquisitionControl
```
or
```bash
python rpi_camera_colony/acquisition --help
# or
python -m rpi_camera_colony.acquisition.remote_control --help
```



### Sandbox Conductor object in separate process (python multiprocessing)
See `rpi_camera_colony.control.process_sandbox` for example use of:
```python
from rpi_camera_colony.control.process_sandbox import ControlProcess
```



## Citation

> Rollik, Lars B. (2021). RPi Camera Colony: Central control for video acquisition with (many) Raspberry Pi cameras. doi: [10.5281/zenodo.4916007](https://doi.org/10.5281/zenodo.4916007).

**BibTeX**
```BibTeX
@misc{rollik2021rpi,
    author       = {Lars B. Rollik},
    title        = {{RPi Camera Colony: Central control for video acquisition with (many) Raspberry Pi cameras}},
    year         = {2021},
    month        = jun,
    publisher    = {Zenodo},
    url          = {https://doi.org/10.5281/zenodo.4916007},
    doi          = {10.5281/zenodo.4916007},
  }
```


## License
This software is released under the **[BSD 3-Clause License](https://github.com/larsrollik/rpi_camera_colony/blob/master/LICENSE)**



## Related projects with similar architectures
- [Arne Meyer's RPiCameraPlugin for the OpenEphys GUI][arne-plugin]

  Specific API for one-to-one control mappings between OpenEphys GUI plugin instances and remote RPi cameras. Inspiration for use of ØMQ communication and camera TTL integration in encoder class.


- [Deshmukh lab's PicameraPaper][deshmukh]

    Video acquisition with multiple RPi synchronised by a central TTL that is recorded with the camera timestamps.


- [Vidgear]

    General package for different types of video acquisition and streaming.



## Configuration file specification

        ! Note: additional picamera attributes can be used, but type has to be confirmed in config loading !

```python
[general]
    acquisition_name = string(default="default_acq_name_config")    # base name for recording
    remote_data_path = string(default="/home/pi/data/")             # where to store all recordings on RPi
    rpi_username = string(default="pi")
    remote_python_interpreter = string(default="/home/pi/miniconda3/envs/py36/bin/python")      # path to python
    remote_python_entrypoint = string(default="rpi_camera_colony.acquisition")      # path to __main__ entrypoint
    max_acquisition_time = integer(0, 7200, default=7200)           # seconds, shut down acquisition after expiration

[log]
    address = string(max=15, default="192.168.100.10")
    port = integer(default=55555)
    level = string(default="DEBUG")
    log_to_console = boolean(default=True)
    log_to_file = boolean(default=True)
    log_file = string(default="/tmp/rpi_camera_colony__logging")

[control]
    address = string(default="192.168.100.10")
    port = integer(default=54545)

[controllers]
    [[__many__]]
        description = string(default="")
        address = string(max=15, default="")
        ttl_channel_external = integer(default=-1)  # metadata info if recording output TTL on specific channel of other acquisition system
        ttl_in_pin = integer(default=16)
        ttl_out_pin = integer(default=8)
        ttl_out_duration = float(default=.001)

        # See for list of ALL parameters https://picamera.readthedocs.io/en/latest/api_camera.html
        framerate = integer(min=1, max=90, default=90)
        resolution = 640x480
        vflip = boolean(default=False)
        hflip = boolean(default=False)
        zoom = (0.0, 0.0, 1.0, 1.0)  # (x, y, w, h)

```



## Specific install hints

### Ip forwarding and routing on central machine

```bash
# IP forward
sysctl -w net.ipv4.ip_forward=1
# check with
cat /proc/sys/net/ipv4/ip_forward

# Package routing
# - outside interface (dhcp): enp7s0
# - inside interface (static): enp8s0
iptables -A FORWARD -i enp8s0 -o enp7s0 -j ACCEPT
iptables -A FORWARD -i enp7s0 -o enp8s0 -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -t nat -A POSTROUTING -o enp7s0 -j MASQUERADE

```

### Update time for ssl certificates
```bash
# Check with
timedatectl status

# force update with NTP
sudo service ntp stop
sudo ntpd -gq
sudo service ntp start

# enable permanent updates
sudo systemctl restart systemd-timesyncd

```


### Install miniconda on RPi
```bash
# Installing miniconda on RPi
wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-armv7l.sh
sudo md5sum Miniconda3-latest-Linux-armv7l.sh # (optional) check md5
sudo /bin/bash Miniconda3-latest-Linux-armv7l.sh # -> change default directory to /home/pi/miniconda3
sudo nano /home/pi/.bashrc # -> add: export PATH="/home/pi/miniconda3/bin:$PATH"
sudo reboot -h now

# Add RPi package channel
conda config --add channels rpi

sudo chown -R pi:pi /home/pi/miniconda3

conda install python=3.6

conda create -n py36 python=3.6 numpy
# next install this package
```



<!-- LINKS -->

[isc-dhcp-server]: https://ubuntu.com/server/docs/network-dhcp
[miniconda]: https://docs.conda.io/en/latest/miniconda.html
[pinout.xyz]: https://pinout.xyz
[Raspbian]: https://www.raspberrypi.org/documentation/installation/installing-images

[arne-plugin]: https://github.com/arnefmeyer/RPiCameraPlugin
[deshmukh]: https://github.com/DeshmukhLab/PicameraPaper
[Vidgear]: https://github.com/abhiTronix/vidgear
