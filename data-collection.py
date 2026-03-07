from src.data_collection.download_puz_file import download_puz_file
from argparse import ArgumentParser
import pandas as pd
from multiprocessing import Pool


def parse_arguments():
    parser = ArgumentParser(
        description="Download crosswords for a specific outlet and year range."
    )
    parser.add_argument(
        "--outlet", "--o", type=str, help="The crossword outlet (e.g., usa, nyt, wsj)"
    )
    parser.add_argument(
        "--start_year", "--s", type=int, help="The year to start (e.g., 2010)"
    )
    parser.add_argument(
        "--end_year", "--e", type=int, help="The year to end (e.g., 2020)"
    )
    parser.add_argument(
        "--username", "--u", type=str, help="Username for authentication", default=None
    )
    parser.add_argument(
        "--password", "--p", type=str, help="Password for authentication", default=None
    )
    return parser.parse_args()


def generate_tasks(outlet, start_year, end_year, username=None, password=None):
    start_str = f"{start_year}-01-01"
    end_str = f"{end_year}-12-31"
    dates = pd.date_range(start=start_str, end=end_str).tolist()

    return [(date, outlet, username, password) for date in dates]


def fetch_crossword(args):
    date, outlet, username, password = args

    day = date.strftime("%d")
    month = date.strftime("%m")
    year = date.strftime("%Y")

    download_puz_file(
        outlet=outlet,
        day=day,
        month=month,
        year=year,
        username=username,
        password=password,
    )


def main():
    args = parse_arguments()

    tasks = generate_tasks(
        args.outlet, args.start_year, args.end_year, args.username, args.password
    )

    print(f"Starting download for {args.outlet} across {len(tasks)} dates...")

    with Pool() as pool:
        pool.map(fetch_crossword, tasks)

    print("Download complete.")


if __name__ == "__main__":
    main()
