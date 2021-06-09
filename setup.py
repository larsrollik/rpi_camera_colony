from os import path

from setuptools import find_packages
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(this_directory, "LICENSE"), encoding="utf-8") as f:
    license_text = f.read()


setup(
    name="rpi_camera_colony",
    version="0.1.2",
    description="RPi Camera Colony: Central control for video acquisition with (many) Raspberry Pi cameras",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    packages=find_packages() + ["rpi_camera_colony.tools"],
    url="https://github.com/larsrollik/rpi_camera_colony",
    author="Lars B. Rollik",
    author_email="L.B.Rollik@protonmail.com",
    license=license_text,
    install_requires=["pyzmq", "tornado", "tqdm", "configobj"],
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
        "rpi": ["picamera", "RPi.GPIO"],
    },
    zip_safe=False,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "rcc_conductor = rpi_camera_colony.control.main:main",
            "rcc_acquisition = rpi_camera_colony.acquisition.main:main",
        ],
    },
)
