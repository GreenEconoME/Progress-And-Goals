# Import dependencies
import requests
import pandas as pd
import numpy as np
import xmltodict
import streamlit as st


# Define a function to pull the annual metrics for each month for energy and water
@st.cache
def pull_monthly_metrics(energy_entries, water_entries, domain, auth, prop_id):
    # Create a list of the end date entries
    if water_entries is not None:
        all_entries = set(list(water_entries['End Date']) + list(energy_entries['End Date']))
    else:
        all_entries = set(list(energy_entries['End Date']))

    for entry_date in all_entries:
        # Save the year and month of the month (date)
        year = entry_date.year
        month = entry_date.month

        # Will pull data based on if the current month is in only water, only energy or in both to reduce redundant api calls
        # Check if the month is only in the water_entries df
        if month in water_entries['End Date'].values and month not in energy_entries['End Date'].values:
            water_metrics = requests.get(domain + f"/property/{prop_id}/metrics?year={year}&month={month}&measurementSystem=EPA", 
                                        headers = {'PM-Metrics': 'waterIntensityTotal'}, 
                                        auth = auth)

            # Parse the historical call
            water_metrics_dict = xmltodict.parse(water_metrics.content)
            # Save the water use intensity value
            wui_metric = water_metrics_dict['propertyMetrics']['metric']['value']

            # For the metric in the water_metrics_dict,
            # Check if the metric exists (will be a string), and add it to the current row column
            # If the metric does not exist, fill the value with a nan
            water_entries.loc[water_entries['End Date'] == entry_date, 'Water Use Intensity'] = wui_metric if isinstance(wui_metric, str) else np.nan
            
            # Format the datatype of the water use intensity column
            water_entries['Water Use Intensity'] = pd.to_numeric(water_entries['Water Use Intensity'])
            
        # Check if the month is only in the energy_entries df
        elif month not in water_entries['End Date'].values and month in energy_entries['End Date'].values:
            # Make the call to get the historical metrics for the current month/year
            energy_metrics = requests.get(domain + f"/property/{prop_id}/metrics?year={year}&month={month}&measurementSystem=EPA",
                                        headers={'PM-Metrics': 'score, sourceTotalWN, medianSourceTotal, sourceIntensityWN, medianSourceIntensity'},
                                        auth=auth)

            # Parse the historical metrics call
            energy_metrics_dict = xmltodict.parse(energy_metrics.content)

            # Save the list containing the returned metrics
            metrics = energy_metrics_dict['propertyMetrics']['metric']

            # Create variables to hold the values for each of the metrics
            energy_star_score = metrics[0]['value']
            weather_normalized_source_eu = metrics[1]['value']
            national_median_source_energy_use = metrics[2]['value']
            weather_normalized_source_eui = metrics[3]['value']
            national_median_source_eui = metrics[4]['value']
            
            # Add the metrics to the current row - if they exist they will be strings if they don't exist, insert a nan as the value
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'Energy Star Score'] = energy_star_score if isinstance(energy_star_score, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'Weather Normalized Source EU (kBtu)'] = weather_normalized_source_eu if isinstance(weather_normalized_source_eu, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'National Median Source Energy Use (kBtu)'] = national_median_source_energy_use if isinstance(national_median_source_energy_use, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'Weather Normalized Source EUI (kBtu/ft²)'] = weather_normalized_source_eui if isinstance(weather_normalized_source_eui, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'National Median Source EUI (kBtu/ft²)'] = national_median_source_eui if isinstance(national_median_source_eui, str) else np.nan
            
            # Format the datatype of the energy metric columns
            energy_entries['Energy Star Score'] = pd.to_numeric(energy_entries['Energy Star Score'])
            energy_entries['Weather Normalized Source EU (kBtu)'] = pd.to_numeric(energy_entries['Weather Normalized Source EU (kBtu)'])
            energy_entries['National Median Source Energy Use (kBtu)'] = pd.to_numeric(energy_entries['National Median Source Energy Use (kBtu)'])
            energy_entries['Weather Normalized Source EUI (kBtu/ft²)'] = pd.to_numeric(energy_entries['Weather Normalized Source EUI (kBtu/ft²)'])
            energy_entries['National Median Source EUI (kBtu/ft²)'] = pd.to_numeric(energy_entries['National Median Source EUI (kBtu/ft²)'])
        
        # Else, the month is in both
        else:
            # Make the call to get the historical metrics for the current month/year
            all_metrics = requests.get(domain + f"/property/{prop_id}/metrics?year={year}&month={month}&measurementSystem=EPA",
                                        headers={'PM-Metrics': 'score, sourceTotalWN, medianSourceTotal, sourceIntensityWN, medianSourceIntensity, waterIntensityTotal'},
                                        auth=auth)

            # Parse the historical metrics call
            all_metrics_dict = xmltodict.parse(all_metrics.content)

            # Save the list containing the returned metrics
            metrics = all_metrics_dict['propertyMetrics']['metric']

            # Create variables to hold the values for each of the metrics
            energy_star_score = metrics[0]['value']
            weather_normalized_source_eu = metrics[1]['value']
            national_median_source_energy_use = metrics[2]['value']
            weather_normalized_source_eui = metrics[3]['value']
            national_median_source_eui = metrics[4]['value']
            wui_metric = metrics[5]['value']
            
            # Add the metrics to the current date - if they exist they will be strings if they don't exist, insert a nan as the value
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'Energy Star Score'] = energy_star_score if isinstance(energy_star_score, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'Weather Normalized Source EU (kBtu)'] = weather_normalized_source_eu if isinstance(weather_normalized_source_eu, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'National Median Source Energy Use (kBtu)'] = national_median_source_energy_use if isinstance(national_median_source_energy_use, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'Weather Normalized Source EUI (kBtu/ft²)'] = weather_normalized_source_eui if isinstance(weather_normalized_source_eui, str) else np.nan
            energy_entries.loc[energy_entries['End Date'] == entry_date, 'National Median Source EUI (kBtu/ft²)'] = national_median_source_eui if isinstance(national_median_source_eui, str) else np.nan
            water_entries.loc[water_entries['End Date'] == entry_date, 'Water Use Intensity'] = wui_metric if isinstance(wui_metric, str) else np.nan
            
            # Format the datatype of the annual metric columns
            energy_entries['Energy Star Score'] = pd.to_numeric(energy_entries['Energy Star Score'])
            energy_entries['Weather Normalized Source EU (kBtu)'] = pd.to_numeric(energy_entries['Weather Normalized Source EU (kBtu)'])
            energy_entries['National Median Source Energy Use (kBtu)'] = pd.to_numeric(energy_entries['National Median Source Energy Use (kBtu)'])
            energy_entries['Weather Normalized Source EUI (kBtu/ft²)'] = pd.to_numeric(energy_entries['Weather Normalized Source EUI (kBtu/ft²)'])
            energy_entries['National Median Source EUI (kBtu/ft²)'] = pd.to_numeric(energy_entries['National Median Source EUI (kBtu/ft²)'])
            water_entries['Water Use Intensity'] = pd.to_numeric(water_entries['Water Use Intensity'])

    return energy_entries, water_entries