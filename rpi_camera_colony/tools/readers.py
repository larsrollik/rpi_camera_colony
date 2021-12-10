import json
import logging
from glob import glob
from pathlib import Path

import pandas as pd
import pandas.errors


def __read_json(file=None):
    with open(file, "r") as f:
        data = f.read()

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        logging.debug(f"Failed to read JSON file: {file}")
        return {}


def exclude_files_by_pattern(file_list=None):
    exclusions_contains = ["DLC_resnet"]
    for excl in exclusions_contains:
        file_list = [f for f in file_list if excl not in f]
    return file_list


def read_session_data(session_dir=None):
    """Read RCC session metadata & video paths (not video data itself).

    File name pattern:
        [session_name].camera_51_blue.20210928_100502.rcc.metadata.json
        [session_name].[camera_id].[dt].rcc.[namespace_id]

    Expected files per camera in acquisition:
        - .rcc.metadata.json
        - .rcc.timestamps_ttl_in.csv    : frame timestamps + input timestamps
        - .rcc.timestamps_ttl_out.csv   : frame timestamps == output timestamps
        - .rcc.video.h264
        - .rcc.video.h264.mp4 [only there is run MSW post acquisition tasks]

    """
    session_dir = Path(session_dir)
    assert session_dir.exists()

    namespace_signature = ".rcc."
    rcc_files_in_dir = glob(str(session_dir / f"*{namespace_signature}*"))
    rcc_files_in_dir = exclude_files_by_pattern(rcc_files_in_dir)

    def get_namespace_identifier(file):
        """Return identifier part. Move to new namespace (underscores replaced with dots) for dict keys."""
        return str(file.split(namespace_signature)[-1].replace("_", "."))

    session_data = {}
    for filepath in rcc_files_in_dir:
        filename = Path(filepath).name
        cam = filename.split(".")[1]
        ftype = get_namespace_identifier(filename)

        if cam not in session_data:
            logging.debug(f"New camera found in session '{filename}': {cam}")
            session_data[cam] = {}
            session_data[cam]["has_h264"] = False
            session_data[cam]["has_mp4"] = False

        # Add data
        if "metadata.json" in ftype:
            session_data[cam][ftype.replace(".json", "")] = __read_json(file=filepath)

        elif ftype.endswith(".csv"):
            # Expect TTL to be empty if not connected.
            try:
                csv_data = pd.read_csv(filepath)

                # Assert that matches TTL-in (shape[1]=1) or TTL-out (shape[1]=2) column layout
                assert csv_data.shape[1] in (1, 2)

                # Remove leading hash and whitespace from column names
                for c in csv_data.columns:
                    csv_data = csv_data.rename(columns={c: c.strip("#").strip(" ")})

            except (pandas.errors.EmptyDataError, AssertionError):
                csv_data = pd.DataFrame()

            session_data[cam][ftype.replace(".csv", "")] = csv_data

        elif ftype == "video.h264":
            session_data[cam]["has_h264"] = True
            session_data[cam]["video_file_h264"] = str(
                Path(filepath).relative_to(session_dir)
            )

        elif ftype == "video.h264.mp4":
            session_data[cam]["has_mp4"] = True
            session_data[cam]["video_file_mp4"] = str(
                Path(filepath).relative_to(session_dir)
            )

    return session_data
