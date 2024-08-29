import logging
import os
import subprocess

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
            ["git", "lfs", "clone", "https://huggingface.co/wanderkid/PDF-Extract-Kit", models_dir], check=True
        )
        for model_subdir in ["Layout", "MFD", "MFR/UniMERNet", "TabRec/StructEqTable"]:
            os.makedirs(os.path.join(models_dir, model_subdir), exist_ok=True)
        subprocess.run(["mv", "/opt/models/PDF-Extract-Kit/models/*", models_dir], shell=True, check=True)
        subprocess.run(["rm", "-rf", "/opt/models/PDF-Extract-Kit"], shell=True, check=True)
        log.info("Models downloaded successfully.")
    else:
        log.info("All required model files are present.")
