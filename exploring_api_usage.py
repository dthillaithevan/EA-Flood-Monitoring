#!/usr/bin/env python3
"""
Created on Mon Mar  3 16:08:38 2025

@author: Dilaksan Thillaithevan

Test script for exploring the EA API

Notes
# List of measures
# https://environment.data.gov.uk/flood-monitoring/id/stations/{id}/measures

To list all readings from a particular station:
https://environment.data.gov.uk/flood-monitoring/id/stations/{id}/readings

"""
import json
from datetime import datetime, timedelta
import argparse
import requests
from requests.models import Response
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


BASE_URL = "https://environment.data.gov.uk/flood-monitoring"

# Taken from https://environment.data.gov.uk/flood-monitoring/doc/reference#:~:text=The%20list%20of%20currently%20available%20types%20of%20measurement%20are:
MEASURE_PARAMETER_NAMES = ["level", "flow", "wind", "temperature"]

# Format used in API
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_FORMAT = "%Y-%m-%d"


def get_time_24hrs_ago() -> datetime:
    """Returns time 24 hours ago"""
    current_time = datetime.now()
    time_24_hours_ago = current_time - timedelta(days=1)
    return time_24_hours_ago


def dt_to_str(dt: datetime, format: str = DATETIME_FORMAT) -> str:
    return dt.strftime(format)


def str_to_dt(dt_str: datetime, format: str = DATETIME_FORMAT) -> str:
    return datetime.strptime(dt_str, format)


def create_session(endpoint_extension: str = None) -> dict:
    session = requests.Session()
    if endpoint_extension is None:
        endpoint_extension = "id/stations"
    else:
        if endpoint_extension.startswith("/"):
            endpoint_extension = endpoint_extension[1:]

    endpoint = f"{BASE_URL}/{endpoint_extension}"

    print(f"Requesting endpoint: {endpoint}")
    response = session.get(endpoint)
    response.raise_for_status()
    print("\tSuccessful request")
    return response.json()


def filter_by_station_name(station_name: str) -> dict:

    # Replacing any spaces with "+"'s
    station_name = "+".join(station_name.split(" "))

    endpoint_ext = f"id/stations?search={station_name}"
    data = create_session(endpoint_ext)

    return data


def get_station_measurement_hist(
    station_id: str,
    start_end_date: tuple[datetime, datetime | None],
    measure_name: str = None,
) -> dict:

    start_date, end_date = start_end_date

    if measure_name is not None:
        measure_name = measure_name.lower()
        assert measure_name in MEASURE_PARAMETER_NAMES

    # Check station id is valid
    endpoint = f"id/stations/?stationReference={station_id}"
    station_info = create_session(endpoint)
    assert (
        len(station_info["items"]) > 0
    ), f"Station id: {station_id} not found! Ensure id is correct"

    # List of measures avaliable from station
    endpoint = f"id/stations/{station_id}/measures"
    data = create_session(endpoint)
    data = data["items"]

    station_measures = {data[i]["parameter"] for i in range(len(data))}
    if measure_name is not None:
        assert (
            measure_name in station_measures
        ), f"Measure: {measure_name} is not taken at station id: {station_id}. Use one of {station_measures} or change station_id"

    # Use start-end filter
    if end_date is not None:
        s_date = dt_to_str(start_date, DATE_FORMAT)
        e_date = dt_to_str(end_date, DATE_FORMAT)

        endpoint = (
            f"/id/stations/{station_id}/readings?startdate={s_date}&enddate={e_date}"
        )
    # Use since filter
    else:
        s_date = dt_to_str(start_date, DATETIME_FORMAT)
        endpoint = f"/id/stations/{station_id}/readings?since={s_date}"

    if measure_name is not None:
        endpoint += f"&parameter={measure_name}"

    data = create_session(endpoint)

    out = {"station": station_info, "readings": data}

    return out


def get_station_measurement_hist_prev_24_hrs(
    station_id: str,
    measure_name: str = None,
):
    return get_station_measurement_hist(
        station_id,
        start_end_date=(get_time_24hrs_ago(), None),
        measure_name=measure_name,
    )


def find_stations_by_parameter(parameter: str):
    assert parameter in MEASURE_PARAMETER_NAMES
    ext = f"id/stations?parameter={parameter}"
    return create_session(ext)


def post_process_readings(readings: dict):

    date_times, values = zip(
        *[
            (str_to_dt(d["dateTime"], DATETIME_FORMAT), d["value"])
            for d in readings["items"]
        ]
    )

    return date_times, values


def create_measurement_df(
    dates: list[datetime], values: list[float], variable_name: str = "Value"
) -> pd.DataFrame:
    df = pd.DataFrame({"Date": dates, variable_name: values})
    df["Date"] = pd.to_datetime(df["Date"], format=DATE_FORMAT)
    df = df.sort_values(by="Date")

    return df


def plot_data(
    data: pd.DataFrame, title: str = "Test", variable_to_plot: str = "Value"
) -> None:

    plt.figure(figsize=(12, 7), dpi=100)

    plt.plot(
        data["Date"],
        data[variable_to_plot],
        "-",
        color="#3366cc",
        linewidth=2.5,
        alpha=0.8,
    )
    plt.scatter(
        data["Date"],
        data[variable_to_plot],
        color="#3366cc",
        s=60,
        alpha=0.7,
        edgecolors="white",
        linewidth=1.5,
    )
    plt.fill_between(data["Date"], data[variable_to_plot], color="#3366cc", alpha=0.2)

    plt.grid(True, linestyle="--", alpha=0.7, color="#cccccc")

    plt.gca().set_facecolor("#f8f9fa")
    plt.gcf().patch.set_facecolor("#f8f9fa")

    plt.gcf().autofmt_xdate()

    # Add labels and title with custom styling
    plt.xlabel("Date", fontsize=12, fontweight="bold", labelpad=10)
    plt.ylabel(variable_to_plot, fontsize=12, fontweight="bold", labelpad=10)
    plt.title(title, fontsize=16, fontweight="bold", pad=20)

    plt.box(True)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)
    plt.gca().spines["left"].set_color("#555555")
    plt.gca().spines["bottom"].set_color("#555555")

    max_value_idx = data[variable_to_plot].idxmax()
    min_value_idx = data[variable_to_plot].idxmin()

    plt.annotate(
        f"Max: {data[variable_to_plot].max():.1f}",
        xy=(data["Date"][max_value_idx], data[variable_to_plot][max_value_idx]),
        xytext=(10, 15),
        textcoords="offset points",
        arrowprops=dict(
            arrowstyle="->", connectionstyle="arc3,rad=.2", color="#222222"
        ),
        fontsize=10,
        color="#222222",
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
    )

    plt.annotate(
        f"Min: {data[variable_to_plot].min():.1f}",
        xy=(data["Date"][min_value_idx], data[variable_to_plot][min_value_idx]),
        xytext=(10, -25),
        textcoords="offset points",
        arrowprops=dict(
            arrowstyle="->", connectionstyle="arc3,rad=.2", color="#222222"
        ),
        fontsize=10,
        color="#222222",
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
    )

    plt.tight_layout()


if __name__ == "__main__":

    # sess = create_session()
    # data = base_api()
    # ex = filter_by_station_name("River Wey")

    # stations = find_stations_by_parameter('flow')

    # start = datetime(2025, 3, 1)
    # end = datetime(2025, 3, 2)
    # data = get_station_measurement_hist('E2534',
    #                                     start_end_date = (start, end),
    #                                     since_date = None,
    #                                     measure_name = 'flow')

    param = "flow"
    data = get_station_measurement_hist_prev_24_hrs("E2534", measure_name=param)

    dates, values = post_process_readings(data["readings"])
    df = create_measurement_df(dates, values, variable_name=param)
    plot_data(df, variable_to_plot="flow")
