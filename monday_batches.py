import csv
from datetime import date, timedelta


def get_mondays_in_range(start: date, end: date) -> list[date]:
    """Return all Mondays between start and end (inclusive)."""
    # Advance start to the first Monday on or after it
    days_until_monday = (7 - start.weekday()) % 7  # weekday(): Mon=0, Sun=6
    first_monday = start + timedelta(days=days_until_monday)

    mondays = []
    current = first_monday
    while current <= end:
        mondays.append(current)
        current += timedelta(weeks=1)

    return mondays


def batch_mondays(start: date, end: date, batch_size: int = 5):
    """Yield batches of `batch_size` Mondays within the date range."""
    mondays = get_mondays_in_range(start, end)
    for i in range(0, len(mondays), batch_size):
        yield mondays[i : i + batch_size]


def write_batches_to_csv(start: date, end: date, output_path: str, batch_size: int = 5):
    """Write Monday batches to a CSV file."""
    # Header: batch_num + one column per slot (monday_1 … monday_N)
    headers = ["batch_num"] + [f"monday_{i+1}" for i in range(batch_size)]

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for batch_num, batch in enumerate(batch_mondays(start, end, batch_size), start=1):
            formatted = [d.strftime("%Y-%m-%d") for d in batch]
            # Pad with empty strings if the last batch is smaller than batch_size
            row = [batch_num] + formatted + [""] * (batch_size - len(formatted))
            writer.writerow(row)

    print(f"Saved {output_path}")


# ── Example usage ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    start_date  = date(2025, 1, 1)
    end_date    = date(2026, 1, 1)
    output_file = "monday_batches.csv"

    write_batches_to_csv(start_date, end_date, output_file)
