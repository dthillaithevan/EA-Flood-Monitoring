#!/usr/bin/env python3
"""
Created on Mon Mar  3 20:12:56 2025

@author: Dilaksan Thillaithevan

Implements API Client class for access Environmental Agency Flood Risk API
"""

from utils import dt_to_str, str_to_dt, get_time_24hrs_ago
from datetime import datetime
import requests
import matplotlib.pyplot as plt
import pandas as pd


class APIClient:

    STATION_ENDPOINT = "id/stations/?stationReference={station_id}"
    MEASURES_ENDPOINT = "id/stations/{station_id}/measures"
    DATE_FILTER_ENDPOINT = (
        "/id/stations/{station_id}/readings?startdate={start_date}&enddate={end_date}"
    )
    DATE_SINCE_FILTER_ENDPOINT = "/id/stations/{station_id}/readings?since={start_date}"
    READINGS_SINCE_FILTER = "/readings?since={start_date}"
    READINGS_DATE_FILTER = "/readings?startdate={start_date}&enddate={end_date}"
    BASE_URL = "https://environment.data.gov.uk/flood-monitoring"
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    DATE_FORMAT = "%Y-%m-%d"

    # Taken from https://environment.data.gov.uk/flood-monitoring/doc/reference#:~:text=The%20list%20of%20currently%20available%20types%20of%20measurement%20are:
    MEASURE_PARAMETER_NAMES = ["level", "flow", "wind", "temperature"]

    def get_api_response(self, endpoint_extension: str = None) -> dict:
        """
        Defaults to stations list.
        Note: Returns the 'items' key of the API response
        """

        session = requests.Session()
        if endpoint_extension is None:
            endpoint_extension = "id/stations"
        else:
            if endpoint_extension.startswith("/"):
                endpoint_extension = endpoint_extension[1:]

        if not endpoint_extension.startswith("http"):
            endpoint = f"{self.BASE_URL}/{endpoint_extension}"
        else:
            endpoint = endpoint_extension

        print(f"Requesting endpoint: {endpoint}")
        response = session.get(endpoint)
        response.raise_for_status()
        print("\tSuccessful request")
        return response.json()["items"]

    def check_valid_station_id(self, station_id: str) -> None:
        """Ceheck if station id is valid"""
        endpoint = self.STATION_ENDPOINT.format(station_id=station_id)
        station_info = self.get_api_response(endpoint)

        assert (
            len(station_info) > 0
        ), f"Station id: {station_id} not found! Ensure id is correct"

    def get_station_measures(self, station_id: int) -> tuple[list[str]]:
        """Get all measurements taken at a station."""
        endpoint = self.MEASURES_ENDPOINT.format(station_id=station_id)
        data = self.get_api_response(endpoint)

        station_measures = list(
            {d["parameter"] for d in data if d.get("latestReading", False)}
        )
        station_measures_eps = list(
            {
                d["latestReading"]["measure"]
                for d in data
                if d.get("latestReading", False)
            }
        )
        station_measues_unit = list(
            {d["unitName"] for d in data if d.get("latestReading", False)}
        )
        station_measues_qualifiers = list(
            {d["qualifier"] for d in data if d.get("latestReading", False)}
        )

        return (
            station_measures,
            station_measures_eps,
            station_measues_unit,
            station_measues_qualifiers,
        )

    def get_station_info(self, station_id: int) -> dict:
        endpoint = self.MEASURES_ENDPOINT.format(station_id=station_id)
        return self.get_api_response(endpoint)

    def check_station_measure(self, station_id: int, measure_name: str) -> None:
        """Checks if measurement is taken at given station (id)"""
        station_measures, _, _, _ = self.get_station_measures(station_id)
        assert (
            measure_name in station_measures
        ), f"Station does not measure: {measure_name}. Valid station measures are {station_measures}"

    def station_name_to_ids(self, station_name: str) -> list:
        """Gets list of station ids that (partially) match the given station name.
        Returns list of station ids and associated station names"""

        station_name = "+".join(station_name.split(" "))

        endpoint_ext = f"id/stations?search={station_name}"
        data = self.get_api_response(endpoint_ext)

        names, ids = zip(*[(d["label"], d["stationReference"]) for d in data])

        return (names, ids)

    def check_is_valid_measure(self, measure_name: str) -> None:
        # measure_name = measure_name.lower()
        assert (
            measure_name in self.MEASURE_PARAMETER_NAMES
        ), f"Measure: {measure_name} is not valid. Use one of {self.MEASURE_PARAMETER_NAMES}"

    def create_date_filter_endpoint(
        self, station_id: int, start_end_date: tuple[datetime, datetime | None]
    ) -> str:
        """Creates a reading date filter based on station id"""

        start_date, end_date = start_end_date

        # Use start-end filter
        if end_date is not None:
            s_date = dt_to_str(start_date, self.DATE_FORMAT)
            e_date = dt_to_str(end_date, self.DATE_FORMAT)

            endpoint = self.DATE_FILTER_ENDPOINT.format(
                station_id=station_id, start_date=s_date, end_date=e_date
            )

        # Use since filter
        else:
            s_date = dt_to_str(start_date, self.DATETIME_FORMAT)
            endpoint = self.DATE_SINCE_FILTER_ENDPOINT.format(
                station_id=station_id, start_date=s_date
            )

        return endpoint

    def create_reading_date_filter_endpoint(
        self, start_end_date: tuple[datetime, datetime | None]
    ) -> str:
        """Creates a reading date filter based on reading endpoint"""

        start_date, end_date = start_end_date

        # Use start-end filter
        if end_date is not None:
            s_date = dt_to_str(start_date, self.DATE_FORMAT)
            e_date = dt_to_str(end_date, self.DATE_FORMAT)

            endpoint = self.READINGS_DATE_FILTER.format(
                start_date=s_date, end_date=e_date
            )

        # Use since filter
        else:
            s_date = dt_to_str(start_date, self.DATETIME_FORMAT)
            endpoint = self.READINGS_SINCE_FILTER.format(start_date=s_date)

        return endpoint

    def get_station_readings(
        self,
        station_id: int,
        start_end_date: tuple[datetime, datetime | None],
        measure_name: str = None,
    ) -> pd.DataFrame:
        """Get the readings for a station within given start-end date tuple.
        If end date is not specifed all readings from start date to current date"""

        print(measure_name)
        # Check measure id is valid
        if measure_name is not None:
            self.check_is_valid_measure(measure_name)

        # Check station id is valid
        self.check_valid_station_id(station_id)

        # Check station collects this particular measurement
        if measure_name is not None:
            self.check_station_measure(station_id, measure_name)

        # If measure name is provided get only that measure
        if measure_name is not None:
            # Get all measures
            (
                station_measures,
                station_measures_eps,
                station_measues_units,
                station_measues_qualifiers,
            ) = self.get_station_measures(station_id)

            # Filter down for measure of interest
            endpoints = [
                ep
                for (ep, m) in zip(station_measures_eps, station_measures)
                if m == measure_name
            ]
            units = [
                unit
                for (unit, m) in zip(station_measues_units, station_measures)
                if m == measure_name
            ]
            qualifiers = [
                q
                for (q, m) in zip(station_measues_qualifiers, station_measures)
                if m == measure_name
            ]
            measure_names = [measure_name]

            # endpoint = self.create_date_filter_endpoint(station_id, start_end_date)
            # endpoint += f"&parameter={measure_name}"
            # endpoints = [endpoint]
            # measure_names = [measure_name]

        # If no measure name is provided get all readings
        else:
            measure_names, endpoints, units, qualifiers = self.get_station_measures(
                station_id
            )

        reading_date_filter = self.create_reading_date_filter_endpoint(
            start_end_date=start_end_date
        )
        endpoints = [ep + reading_date_filter for ep in endpoints]

        dfs = []
        for measure, endpoint in zip(measure_names, endpoints):
            data = self.get_api_response(endpoint)
            dfs += [self.post_process_station_measurement_data(data, measure)]

        measurement_info = {
            m: {"qualifier": q, "unit": u}
            for m, q, u in zip(measure_names, qualifiers, units)
        }

        return pd.concat(dfs, axis=1), measurement_info

    def get_station_measure_info(self, station_id: int, measure_name: str):

        (
            station_measures,
            station_measures_eps,
            station_measues_unit,
            station_measues_qualifiers,
        ) = self.get_station_measures(station_id)

    def post_process_station_measurement_data(
        self,
        data: dict,
        measurement_name: str,
    ) -> pd.DataFrame:

        dates, values = zip(
            *[
                (str_to_dt(d["dateTime"], self.DATETIME_FORMAT), d["value"])
                for d in data
            ]
        )

        return self.create_measurement_df(dates, values, measurement_name)

    def create_measurement_df(
        self,
        dates: list[datetime],
        measurements: list[float],
        measurement_name: str = "Measurement",
    ) -> pd.DataFrame:

        df = pd.DataFrame({"Date": dates, measurement_name: measurements})
        df["Date"] = pd.to_datetime(df["Date"], format=self.DATE_FORMAT)
        df = df.sort_values(by="Date")

        return df


if __name__ == "__main__":

    client = APIClient()

    print(client.get_station_measures("E2534"))
    # print (client.station_name_to_ids("River"))
    # print (client.station_name_to_ids("River"))
    print(
        client.get_station_readings(
            "E2534", (get_time_24hrs_ago(), None), measure_name="flow"
        )
    )
