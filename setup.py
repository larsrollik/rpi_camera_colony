import platform
from os import path

from setuptools import find_packages
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md")) as f:
    long_description = f.read()

with open(path.join(this_directory, "LICENSE")) as f:
    license_text = f.read()


install_requires = [
    "pyzmq",
    "tornado",
    "tqdm",
    "configobj",
    "numpy",
    "pandas",
    "rich",
]
rpi_requirements = ["picamera", "RPi.GPIO"]

if "arm" in platform.machine().lower():
    install_requires += rpi_requirements


setup(
    name="rpi_camera_colony",
    version="0.4.5.dev0",
    description="RPi Camera Colony: Central control for video acquisition with (many) Raspberry Pi cameras",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    packages=find_packages(),
    url="https://github.com/larsrollik/rpi_camera_colony",
    author="Lars B. Rollik",
    author_email="L.B.Rollik@protonmail.com",
    license=license_text,
    install_requires=install_requires,
    extras_require={
        "dev": [
            "black",
            "pytest-cov",
            "pytest",
            "gitpython",
            "coverage>=5.0.3",
            "bump2version",
            "pre-commit",
            "flake8",
        ],
        "rpi": rpi_requirements,
    },
    zip_safe=False,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "rcc_conductor = rpi_camera_colony.control.main:main",
            "rcc_acquisition = rpi_camera_colony.acquisition.__main__:main",
            "rcc_calibration = rpi_camera_colony.calibration.__main__:main",
        ],
    },
)
