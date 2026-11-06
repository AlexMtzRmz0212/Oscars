"""Build the annual CPI-U table used for inflation adjustment.

The figures are the Bureau of Labor Statistics' series, served as monthly values by FRED (CPIAUCNS).
Years need at least 11 months: 2025 has no October value in the series, but the current
partial year must stay out. Uses curl for the same certificate reason as fetch_wikidata.py.
"""
import csv
import io
import subprocess
from collections import defaultdict

from common import DATA, USER_AGENT

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS"
CPI_FILE = DATA / "reference" / "cpi_u_annual.csv"
MIN_MONTHS = 11


def annual_averages(monthly_rows):
    by_year = defaultdict(list)
    for row in monthly_rows:
        value = row["CPIAUCNS"].strip()
        if value and value != ".":
            by_year[int(row["observation_date"][:4])].append(float(value))
    return {year: round(sum(values) / len(values), 3) for year, values in sorted(by_year.items()) if len(values) >= MIN_MONTHS}


def run():
    result = subprocess.run(["curl", "-sSfL", "-m", "60", "-A", USER_AGENT, URL], capture_output=True, check=True)
    rows = csv.DictReader(io.StringIO(result.stdout.decode("utf-8")))
    averages = annual_averages(rows)
    CPI_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CPI_FILE, "w", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["year", "cpi_u"])
        writer.writerows(averages.items())
    print(f"  wrote {len(averages)} years, {min(averages)} to {max(averages)}")


if __name__ == "__main__":
    run()
