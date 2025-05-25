from rpi_camera_colony.acquisition.acquisition_control import PiAcquisitionControl


def run_rcc_server():
    """Run the rcc server"""
    # REST API endpoints for acquisition control
    # create/interact with PiAcquisitionControl in separate thread

    print("Starting rcc server", PiAcquisitionControl)


def run_rcc_client():
    """Run the rcc server client"""
    # REST API calls
    # input args: same as remote control, but add ip/port of server
    # -> needs to adhere to namespace requirements of MSW

    print("Starting rcc server client to talk to rcc server")
