import subprocess
import sys


def ensure_toml_installed() -> None:
    """Ensure toml is installed in the current environment."""
    try:
        __import__("toml")
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "toml"],
            check=True,
        )


def test_python_version() -> None:
    """Test that Python version is compatible with the environment."""
    assert sys.version_info >= (3, 8), "Python version must be 3.8 or higher"


def test_package_installation() -> None:
    """Test dynamic installation and uninstallation of the package."""
    ensure_toml_installed()
    import toml

    # Dynamically read the package name
    package_name = toml.load("pyproject.toml")["project"]["name"]

    # Install the package
    subprocess.run([sys.executable, "-m", "pip", "install", "."], check=True)

    # Check that the package is installed
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Package installation failed"

    # Uninstall the package
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
        check=True,
    )

    # Verify the package is uninstalled
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Package uninstallation failed"
