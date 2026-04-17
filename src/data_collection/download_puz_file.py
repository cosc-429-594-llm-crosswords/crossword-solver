import os
import subprocess

from src.constants import PUZ_FILE_DIR


def download_puz_file(
    outlet: str,
    day: str,
    month: str,
    year: str,
    username: str | None = None,
    password: str | None = None,
) -> None:
    os.makedirs(PUZ_FILE_DIR, exist_ok=True)

    date = f"{year}-{month}-{day}"
    output_filename = f"{outlet}_{date}.puz".replace("-", "_")
    output_path = os.path.join(PUZ_FILE_DIR, output_filename)

    if os.path.exists(output_path):
        print(
            f"PUZ file for {outlet} on {date} already exists at {output_path}. Skipping download."
        )
        return

    arguments = [
        "uvx",
        "xword-dl",
        outlet,
        "--date",
        date,
        "--output",
        output_path,
    ]

    if username and password:
        arguments.extend(["--username", username, "--password", password])

    try:
        print(f"Downloading PUZ file for {outlet} on {date}...")
        print(f"Running command: {' '.join(arguments)}")
        subprocess.run(
            arguments,
            check=True,
            text=False,
        )
    except subprocess.CalledProcessError:
        print(f"Error occurred while downloading PUZ file for {outlet} on {date}")
