#!/usr/bin/env python3
"""
Created on Mon Mar  3 16:08:38 2025

@author: Dilaksan Thillaithevan
"""

import json
from datetime import datetime
import argparse
import requests


def test_api():
    session = requests.Session()
    endpoint = f"{BASE_URL}/id/stations"
    response = session.get(endpoint)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    BASE_URL = "https://environment.data.gov.uk/flood-monitoring"

    data = test_api()

    print(len(data["items"]))
