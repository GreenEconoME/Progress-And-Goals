# Import dependencies
import requests
import pandas as pd
import numpy as np
import xmltodict
import streamlit as st

# Define a function to pull the annual metrics for each month for energy and water
def pull_monthly_metrics(energy_entries, water_entries, domain, auth, prop_id):
    session = requests.Session()
    session.auth = auth

    # Combine dates from both dataframes
    if water_entries is not None:
        all_entries = set(list(water_entries['End Date']) + list(energy_entries['End Date']))
    else:
        all_entries = set(list(energy_entries['End Date']))

    for entry_date in all_entries:
        year = entry_date.year
        month = entry_date.month

        def fetch_metrics(headers):
            url = f"{domain}/property/{prop_id}/metrics?year={year}&month={month}&measurementSystem=EPA"
            response = session.get(url, headers=headers)
            return xmltodict.parse(response.content)

        def safe_assign(df, date, column, value):
            df.loc[df['End Date'] == date, column] = value if isinstance(value, str) else np.nan

        # Determine which type of request is needed
        if water_entries is None or month not in water_entries['End Date'].dt.month.values:
            # Only energy
            metrics_dict = fetch_metrics({'PM-Metrics': 'score, sourceTotalWN, medianSourceTotal, sourceIntensityWN, medianSourceIntensity'})
            metrics = metrics_dict['propertyMetrics']['metric']
            safe_assign(energy_entries, entry_date, 'Energy Star Score', metrics[0]['value'])
            safe_assign(energy_entries, entry_date, 'Weather Normalized Source EU (kBtu)', metrics[1]['value'])
            safe_assign(energy_entries, entry_date, 'National Median Source Energy Use (kBtu)', metrics[2]['value'])
            safe_assign(energy_entries, entry_date, 'Weather Normalized Source EUI (kBtu/ft²)', metrics[3]['value'])
            safe_assign(energy_entries, entry_date, 'National Median Source EUI (kBtu/ft²)', metrics[4]['value'])

        elif month not in energy_entries['End Date'].dt.month.values:
            # Only water
            metrics_dict = fetch_metrics({'PM-Metrics': 'waterIntensityTotal'})
            value = metrics_dict['propertyMetrics']['metric']['value']
            safe_assign(water_entries, entry_date, 'Water Use Intensity', value)

        else:
            # Both
            metrics_dict = fetch_metrics({'PM-Metrics': 'score, sourceTotalWN, medianSourceTotal, sourceIntensityWN, medianSourceIntensity, waterIntensityTotal'})
            metrics = metrics_dict['propertyMetrics']['metric']
            safe_assign(energy_entries, entry_date, 'Energy Star Score', metrics[0]['value'])
            safe_assign(energy_entries, entry_date, 'Weather Normalized Source EU (kBtu)', metrics[1]['value'])
            safe_assign(energy_entries, entry_date, 'National Median Source Energy Use (kBtu)', metrics[2]['value'])
            safe_assign(energy_entries, entry_date, 'Weather Normalized Source EUI (kBtu/ft²)', metrics[3]['value'])
            safe_assign(energy_entries, entry_date, 'National Median Source EUI (kBtu/ft²)', metrics[4]['value'])
            safe_assign(water_entries, entry_date, 'Water Use Intensity', metrics[5]['value'])

    # Format energy columns
    energy_cols = [
        'Energy Star Score',
        'Weather Normalized Source EU (kBtu)',
        'National Median Source Energy Use (kBtu)',
        'Weather Normalized Source EUI (kBtu/ft²)',
        'National Median Source EUI (kBtu/ft²)'
    ]
    for col in energy_cols:
        energy_entries[col] = pd.to_numeric(energy_entries[col], errors='coerce')

    if water_entries is not None:
        water_entries['Water Use Intensity'] = pd.to_numeric(water_entries['Water Use Intensity'], errors='coerce')

    return energy_entries, water_entries

