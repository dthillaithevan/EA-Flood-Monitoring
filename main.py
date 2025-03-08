#!/usr/bin/env python3
"""
Created on Wed Mar  5 21:58:26 2025

@author: Dilaksan Thillaithevan

Main entry for CLI interface for EA API.
"""

from collections import namedtuple
from cli import (
    search_stations_by_name,
    fetch_station_readings_prev_24_hrs_all_measures,
    fetch_station_readings,
    fetch_station_measures,
    fetch_station_info,
    display_acronyms,
    display_measure_types,
)
from api_client import APIClient


# ============================================================================= #
# I am using namedTuple to ensure added choices are mapped correctly. Avoids
# needing to manually keep track of choice numbers and descriptions.
UserChoice = namedtuple("UserChoice", ["func", "description"])

CHOICE_MAPPINGS = {
    "1": UserChoice(search_stations_by_name, "Search for stations by name"),
    "2": UserChoice(
        fetch_station_readings_prev_24_hrs_all_measures,
        "Fetch station(s) readings over past 24 hrs",
    ),
    "3": UserChoice(
        fetch_station_readings,
        "Fetch station readings for provided date range and measures of interest",
    ),
    "4": UserChoice(
        fetch_station_measures, "List measures that are taken given station(s)"
    ),
    "5": UserChoice(fetch_station_info, "List infomation for chosen station(s)"),
    "6": UserChoice(display_acronyms, "List acronym defitions"),
    "7": UserChoice(display_measure_types, "List all valid types of measures"),
    "8": UserChoice(lambda x: exit, "Exit"),
}
# ============================================================================= #


# ============================================================================= #
def main():
    """Implemnts CL interface for interacting with APIClinet.
    Lets user select from options provided in CHOICE_MAPPING"""

    api_client = APIClient()

    while True:
        print("\nOptions:")
        [print(f"{k}: {v.description}") for k, v in CHOICE_MAPPINGS.items()]

        max_choice = len(CHOICE_MAPPINGS) + 1
        choice = input(f"Enter your choice (1-{max_choice}): ").strip()

        choice_func = CHOICE_MAPPINGS.get(choice, False)

        if not choice_func:
            print(f"Invalid choice, please enter a number between 1 and {max_choice}.")

        else:
            choice_func.func(api_client)


# ============================================================================= #

if __name__ == "__main__":
    main()
