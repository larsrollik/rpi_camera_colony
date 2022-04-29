from pathlib import Path

from rpi_camera_colony.config import config_spec_path
from rpi_camera_colony.config.config import load_config


def test_load_config():
    config_files = sorted((Path.cwd() / "example_configs").glob("*.config"))

    for config in config_files:
        config = load_config(
            config_path=config,
            config_spec_path=config_spec_path,
            ignore_errors=False,
        )
        print(config)
