import logging
import os
import shutil
import subprocess
from glob import glob

log = logging.getLogger("__main__." + __name__)


def download_models(models_dir: str = "/opt/models"):
    """Download the required models for the PDF-Extract-Kit."""
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    # Check if models are already present
    required_files = [
        "MFD/weights.pt",
        "Layout/config.json",
        "MFR/UniMERNet/config.json",
        "TabRec/StructEqTable/config.json",
    ]

    missing_files = [f for f in required_files if not os.path.exists(os.path.join(models_dir, f))]
    if missing_files:
        log.info("Missing model files detected. Downloading models...")
        subprocess.run(["git", "lfs", "install"], check=True)
        subprocess.run(
            ["git", "clone", "https://huggingface.co/wanderkid/PDF-Extract-Kit", "/opt/models/PDF-Extract-Kit"],
            check=True,
        )

        # Move the downloaded files to the correct location
        for file_path in glob("/opt/models/PDF-Extract-Kit/models/*/*"):
            destination = os.path.join(models_dir, os.path.relpath(file_path, "/opt/models/PDF-Extract-Kit/models"))
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.move(file_path, destination)

        # Clean up
        shutil.rmtree("/opt/models/PDF-Extract-Kit")

        log.info("Models downloaded and moved successfully.")
    else:
        log.info("All required model files are present.")
