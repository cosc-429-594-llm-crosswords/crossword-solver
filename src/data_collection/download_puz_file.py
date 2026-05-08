import os
import subprocess

from src.constants import PUZ_FILE_DIR


# Using the xword-dl python package, download .puz files in bulk for a given outlet (New York Times, Washington Post, LA Times, etc.) and date range.
# The function checks if the file already exists before downloading to avoid duplicates.
# Source: https://github.com/thisisparker/xword-dl
def download_puz_file(
    outlet: str,
    day: str,
    month: str,
    year: str,
    username: str | None = None,
    password: str | None = None,
) -> None:

    # Define the output path for the downloaded .puz file
    os.makedirs(PUZ_FILE_DIR, exist_ok=True)
    date = f"{year}-{month}-{day}"
    output_filename = f"{outlet}_{date}.puz".replace("-", "_")
    output_path = os.path.join(PUZ_FILE_DIR, output_filename)

    # Check if the file already exists before attempting to download
    if os.path.exists(output_path):
        print(
            f"PUZ file for {outlet} on {date} already exists at {output_path}. Skipping download."
        )
        return

    # Define the command-line arguments for the xword-dl tool
    arguments = [
        "uvx",
        "xword-dl",
        outlet,
        "--date",
        date,
        "--output",
        output_path,
    ]

    # Add username and password arguments if provided (for outlets that require authentication like the New York Times)
    if username and password:
        arguments.extend(["--username", username, "--password", password])

    try:
        # Run the command to download the .puz file
        print(f"Downloading PUZ file for {outlet} on {date}...")
        print(f"Running command: {' '.join(arguments)}")
        subprocess.run(
            arguments,
            check=True,
            text=False,
        )
    except subprocess.CalledProcessError:
        print(f"Error occurred while downloading PUZ file for {outlet} on {date}")
