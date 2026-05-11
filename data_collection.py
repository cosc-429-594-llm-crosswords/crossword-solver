from argparse import ArgumentParser, Namespace
from datetime import date, timedelta

from src.data_collection.download_puz_file import download_puz_file


# Parse command line arguments
def parse_arguments() -> Namespace:
    parser = ArgumentParser(description="Download crosswords for a specific outlet and year range.")
    parser.add_argument(
        "--outlet", "--o", type=str, help="The crossword outlet (e.g., usa, nyt, wsj)"
    )
    parser.add_argument("--start_year", "--s", type=int, help="The year to start (e.g., 2010)")
    parser.add_argument("--end_year", "--e", type=int, help="The year to end (e.g., 2020)")
    parser.add_argument(
        "--username", "--u", type=str, help="Username for authentication", default=None
    )
    parser.add_argument(
        "--password", "--p", type=str, help="Password for authentication", default=None
    )

    return parser.parse_args()


# Generate a list of dates between the start and end years
def get_dates(start_year: int, end_year: int) -> list[date]:
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)

    dates: list[date] = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def main() -> None:
    args = parse_arguments()

    # For each date in the date range, download the corresponding .puz file
    dates = get_dates(args.start_year, args.end_year)
    for current_date in dates:
        day = current_date.strftime("%d")
        month = current_date.strftime("%m")
        year = current_date.strftime("%Y")

        # Download the .puz file for the current date and outlet
        download_puz_file(
            outlet=args.outlet,
            day=day,
            month=month,
            year=year,
            username=args.username,
            password=args.password,
        )


if __name__ == "__main__":
    main()
