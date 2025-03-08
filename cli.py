#!/usr/bin/env python3
"""
Created on Sat Mar  8 11:42:17 2025

@author: Dilaksan Thillaithevan

Implements all CLI commands for interacting with the EA API.
"""

import random
from plotting import plot_time_series
import tabulate
from utils import str_to_dt, get_time_24hrs_ago
from api_client import APIClient, MEASURE_TYPES

MAX_PRINT_ROWS = 30

ACRONYMS = {
    "mAOD": "Metres relative to the Ordnance Survey datum",
    "mASD": "Metres relative to the local stage datum",
    "m": "Metres with an unspecified datum",
}


# ============================================================================= #
def display_acronyms(*args) -> None:
    print("\n")
    print("-" * 50)
    print("\nAcronym Definitions:")
    for key, value in ACRONYMS.items():
        print(f"{key} - {value}\n")
    print("-" * 50)


# ============================================================================= #


# ============================================================================= #
def display_measure_types(*args) -> None:
    print("\n")
    print("-" * 50)
    print("Measures:")
    for key, value in MEASURE_TYPES.items():
        print(f"{key} - {value}\n")
    print("-" * 50)


# ============================================================================= #


# ============================================================================= #
def process_sep_string(long_string: str) -> list[str]:
    """Maps 'str1;str2' -> [str1, str2]"""
    return [s.strip() for s in long_string.split(";")]


# ============================================================================= #


# ============================================================================= #
def get_random_station_id(api_client: APIClient) -> tuple[str, str]:
    all_station_ids, all_station_names = api_client.get_all_station_ids()
    r = random.randint(0, len(all_station_ids))
    return all_station_ids[r], all_station_names[r]


# ============================================================================= #


# ============================================================================= #
def _print_station_measures(
    api_client: APIClient, station_id: str, station_name: str
) -> None:
    """
    Fetches and prints available measures at a station.
    """
    try:
        measures, _, units, qualifiers = api_client.get_station_measures(station_id)
        print(f"\nAvailable Measures at {station_name}:")
        for measure, unit, qualifier in zip(measures, units, qualifiers):
            print(f"\t{measure} (Qualifier: {qualifier}, Unit: {unit})")
    except Exception as e:
        print(f"Error fetching station measures: {e}")


# ============================================================================= #


# ============================================================================= #
def _fetch_station_readings(
    api_client: APIClient,
    station_ids: list[str],
    station_names: list[str],
    prev_24_hrs_only: bool = True,
    all_measures: bool = True,
) -> None:
    """Get measurements from stations. Prints and plots data

    If more than one station id is provided, the measurement and date range are
    assumed to be constant across each station.

    prev_24_hrs_only sets whether to default to selecting readings from previous 24
    hours only or let user provide date range

    all_measures sets whether to output all measures from station or let user select
    measure(s) of interest
    """

    if not prev_24_hrs_only:
        start_date_str = input(
            "Enter start date (DD-MM-YYYY) (optional, Enter for prev-24 hours): "
        ).strip()
        end_date_str = input(
            "Enter end date (DD-MM-YYYY) (optional, press Enter for current date-time): "
        ).strip()
        start_date = (
            str_to_dt(start_date_str, "%d-%m-%Y")
            if start_date_str
            else get_time_24hrs_ago()
        )
        end_date = str_to_dt(end_date_str, "%d-%m-%Y") if start_date_str else None
    else:
        start_date = get_time_24hrs_ago()
        end_date = None

    if not all_measures:
        measure = input(
            "Enter measure type (optional, press Enter to fetch all): "
        ).strip()
    else:
        measure = None

    combined_df = None
    combined_measurement_info = {}

    for station_id, station_name in zip(station_ids, station_names):
        try:
            readings_df, measurement_info = api_client.get_station_readings(
                station_id, station_name, (start_date, end_date), measure or None
            )

            if readings_df.empty:
                print(f"\nNo readings found for station {station_id}.")
                continue

            prefixed_columns = {
                col: f"{station_name}\n{col.title()} ({measurement_info[col]['qualifier']}, {measurement_info[col]['unit']})"
                for col in readings_df.columns
                if col != "Date"
            }
            readings_df = readings_df.rename(columns=prefixed_columns)

            if combined_df is None:
                combined_df = readings_df
            else:
                combined_df = combined_df.merge(readings_df, on="Date", how="outer")

            combined_measurement_info.update(
                {
                    prefixed_columns[col]: measurement_info[col]
                    for col in measurement_info
                }
            )

        except Exception as e:
            print(f"Error fetching station {station_name} ({station_id}) readings: {e}")

    if combined_df is None or combined_df.empty:
        print("\nNo data available for the specified station(s).")
    else:
        combined_df.sort_values(by="Date", inplace=True)

        headers = ["Date"] + list(combined_df.columns.drop("Date"))
        print("\n", "-" * 50)

        print_rows = min(MAX_PRINT_ROWS, len(combined_df))
        print(
            tabulate.tabulate(
                combined_df.head(print_rows),
                headers=headers,
                tablefmt="psql",
                showindex="false",
                floatfmt=".3f",
            )
        )

        print(combined_measurement_info)

        if input("Would you like to plot the data? (yes/no): ").strip().lower() in [
            "yes",
            "y",
        ]:
            plot_time_series(combined_df, combined_measurement_info)


# ============================================================================= #


# ============================================================================= #
def _print_station_info(api_client: APIClient, station_id: str) -> None:
    """
    Fetches and displays station information.
    """
    try:
        data = api_client.get_station_info(station_id)
        print("\n", "-" * 30)
        print(f"Station ({station_id}) Information:")

        for key, value in data[0].items():
            if key != "@id":
                if key == "measures":
                    print(f"\tMeasures: {[_['parameter'] for _ in value]}")
                else:
                    print(f"\t{key.title()} - {value}")
        print("-" * 30)

    except Exception as e:
        print(f"Error fetching station information: {e}")


# ============================================================================= #
def get_random_station_id_name_pair(
    api_client: APIClient,
) -> tuple[list[str], list[str]]:
    station_id, station_name = get_random_station_id(api_client)
    station_ids = [station_id]
    station_names = [station_name]
    print(f"\tRandomly chosen station: {station_names[0].title()} (id: {station_id})")
    return station_ids, station_names


# ============================================================================= #


# ============================================================================= #
def capitalise_station_names(station_names: list[str]) -> list[str]:
    """Capitalises works in station_names, ignore intermediate words"""

    IGNORE_WORDS = ["at"]
    out = []
    for n in station_names:
        capitalised = " ".join(
            word.title() if word.lower() not in IGNORE_WORDS else word
            for word in n.split(" ")
        )
        out += [capitalised]
    return out


# ============================================================================= #
def preprocess_station_info(api_client: APIClient) -> tuple[list[str], list[str]]:
    """Preprocessing function.
    Allows user to get measures by station name(s) or station id(s).
    If station name(s) do not provide an exact match then user can select based
    on closest station name matches that are found.
    """
    id_or_name = input(
        "\nPress 0 to use station id(s). Press 1 to use station name(s): "
    ).strip()

    if id_or_name == "0":
        station_input = input(
            "\nEnter station ID (optional, press Enter for random station.\nUse ; to seperate multiple station ids): "
        ).strip()
        if not station_input:
            station_ids, station_names = get_random_station_id_name_pair(api_client)
        else:
            station_ids = process_sep_string(station_input)
            station_names = [
                api_client.get_station_name_from_id(id) for id in station_ids
            ]

    elif id_or_name == "1":
        station_input = input(
            "\nEnter station name (optional, press Enter for random station.\nUse ; to seperate multiple station names): "
        ).strip()

        if not station_input:
            station_ids, station_names = get_random_station_id_name_pair(api_client)
        else:
            # Convert to list of station names
            station_names_pre = process_sep_string(station_input)
            station_names_pre = capitalise_station_names(station_names_pre)

            station_names = []
            station_ids = []

            for n in station_names_pre:
                print(f"Searching station name '{n}'...")
                names, ids = api_client.station_name_to_ids(n, print_on_error=False)

                if len(names) == 0:
                    cont = (
                        input(
                            f"Could not find station {n}. Do you wish to continue (yes/no): "
                        )
                        .strip()
                        .lower()
                    )
                    if cont in ["no", "n"]:
                        print("Exiting...")
                        break
                    continue

                else:
                    names = [n for n in names]
                    ids = [id for id in ids]

                    if n not in names:
                        print(
                            f"Could not find explicit match for station: '{n}'. Please select one of the following: "
                        )

                        print(f"\t{0}. All listed stations")
                        for i, station_name in enumerate(names):
                            print(f"\t{i+1}. {station_name}")

                        idxs = input(
                            "\nEnter your selection (use ; to select multiple indices): "
                        ).strip()
                        idxs = process_sep_string(idxs)
                        idxs = [int(id) for id in idxs]

                        if 0 in idxs:
                            station_ids += ids
                            station_names += names
                        else:
                            station_ids += [ids[i - 1] for i in idxs]
                            station_names += [names[i - 1] for i in idxs]
            print(f"\nFetching measurements for {station_names}")
        return station_ids, station_names
    else:
        raise ValueError("Invalid choice, please chose from 0 or 1 only!")


# ============================================================================= #
def search_stations_by_name(api_client: APIClient) -> None:
    station_name = input("Enter station name or keyword: ").strip()
    station_name = capitalise_station_names([station_name])[0]

    try:
        station_names, station_ids = api_client.station_name_to_ids(station_name)
        data = zip(station_ids, station_names)

        print("\nMatching Stations:")
        print(
            tabulate.tabulate(
                data,
                headers=["station_id", "station_name"],
                tablefmt="psql",
                floatfmt=".3f",
            )
        )
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================= #


# ============================================================================= #
def fetch_station_readings_prev_24_hrs_all_measures(api_client: APIClient) -> None:
    try:
        station_ids, station_names = preprocess_station_info(api_client)

        _fetch_station_readings(
            api_client,
            station_ids,
            station_names,
            prev_24_hrs_only=True,
            all_measures=True,
        )
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================= #


# ============================================================================= #
def fetch_station_readings(api_client: APIClient) -> None:
    try:
        station_ids, station_names = preprocess_station_info(api_client)
        _fetch_station_readings(
            api_client,
            station_ids,
            station_names,
            prev_24_hrs_only=False,
            all_measures=False,
        )
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================= #


# ============================================================================= #
def fetch_station_measures(api_client: APIClient) -> None:
    try:
        station_ids, station_names = preprocess_station_info(api_client)
        [
            _print_station_measures(api_client, id, name)
            for id, name in zip(station_ids, station_names)
        ]
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================= #


# ============================================================================= #
def fetch_station_info(api_client: APIClient) -> None:
    try:
        station_ids, _ = preprocess_station_info(api_client)
        [_print_station_info(api_client, id) for id in station_ids]
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================= #
