if __name__ == "__main__":
    from rpi_camera_colony.control.main import main
    import sys
    import rpi_camera_colony
    from pathlib import Path

    config_path = (
        Path(rpi_camera_colony.__path__[0]).parent
        / "example_configs"
        / "example.config"
    )
    sys.argv += ["-c", config_path.as_posix(), "-n", "test"]

    main()
