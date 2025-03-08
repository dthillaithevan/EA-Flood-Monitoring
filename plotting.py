#!/usr/bin/env python3
"""
Created on Wed Mar  5 23:26:35 2025

@author: Dilaksan Thillaithevan
"""
from pandas import DataFrame
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
def plot_time_series(df: DataFrame, measurement_info: dict):
    """ """
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
    df.set_index(df.columns[0], inplace=True)

    num_cols = len(df.columns)
    start_date = df.index.min().strftime("%d-%m-%Y")
    end_date = df.index.max().strftime("%d-%m-%Y")

    num_cols = len(df.columns)

    if num_cols == 1:
        col_name = df.columns[0]
        # col_name += f" ({measurement_info[col_name]['unit']}, {measurement_info[col_name]['qualifier']})"
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df.iloc[:, 0], label=col_name)
        y_label = (
            measurement_info[col_name]["measurement_name"]
            + " - "
            + measurement_info[col_name]["qualifier"]
            + " ("
            + measurement_info[col_name]["unit"]
            + ")"
        )
        ax.set_ylabel(y_label)
        ax.set_title(f"{col_name} ({start_date} - {end_date})")
        ax.grid(True, linestyle="--", alpha=0.7, color="#cccccc")
        ax.spines[["right", "top"]].set_visible(False)
        ax.spines["left"].set_color("#555555")
        ax.spines["bottom"].set_color("#555555")

    else:
        fig, axes = plt.subplots(num_cols, 1, figsize=(10, 5 * num_cols), sharex=True)

        if num_cols == 1:
            axes = [axes]

        for ax, col in zip(axes, df.columns):
            ax.plot(df.index, df[col], label=col)
            y_label = (
                measurement_info[col]["measurement_name"]
                + " - "
                + measurement_info[col]["qualifier"]
                + " ("
                + measurement_info[col]["unit"]
                + ")"
            )
            ax.set_ylabel(y_label)
            ax.set_xlabel("Date")
            ax.set_title(f"{col}")
            ax.legend()
            ax.grid(True, linestyle="--", alpha=0.7, color="#cccccc")
            ax.spines["left"].set_color("#555555")
            ax.spines["bottom"].set_color("#555555")
            ax.spines[["right", "top"]].set_visible(False)

    plt.gca().set_facecolor("#f8f9fa")
    plt.gcf().patch.set_facecolor("#f8f9fa")

    plt.xticks(rotation=45)
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    plt.show()


# =============================================================================
