import subprocess

import toml


def get_package_name() -> str:
    """Retrieve package name from pyproject.toml."""
    project_data = toml.load("pyproject.toml")
    return str(project_data["project"]["name"])


def test_package_functionality() -> None:
    """Test the package dynamically after installation."""
    package_name = get_package_name()

    # Install the package
    subprocess.run(["pip", "install", "."], check=True)

    # Dynamically import the package
    result = subprocess.run(
        ["python", "-c", f"import {package_name}"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Dynamic package import failed: {result.stderr}"

    # Cleanup: Uninstall the package
    subprocess.run(["pip", "uninstall", "-y", package_name], check=True)
