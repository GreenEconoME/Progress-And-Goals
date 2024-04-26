# Import dependencies
import xmltodict
import requests
from datetime import datetime
from calendar import monthrange
import numpy as np
import pandas as pd
import math
import streamlit as st

# Create helper function to sort the best WNSEUI and WUI changes the first four years and the last year in compliance period
def filter_tuple_list(given_list, target_value):
    for x, y in given_list:
        if x == target_value:
            return y


def pull_prop_data(espm_id, year_ending, month_ending, domain, auth):
    # Given the year/month ending date, pull the metrics for the year ending and the previous four years

    # Create a list to hold the dictionaries of metrics for each year
    annual_metrics = []
    historical_consumption = []
    units_of_metrics = []
    # Loop through the year ending and the previous four years to gather progress and goals metrics
    for i in range(5):
        # Create dictionaries to hold the current years metrics
        year_data = {}
        consumption_data = {}

        # Pulling the current year data metrics
        year_ending_metrics = requests.get(domain + f'/property/{espm_id}/metrics?year={year_ending - i}&month={month_ending}&measurementSystem=EPA', 
                                           headers = {'PM-Metrics' : 
                                                      'score, ' + 
                                                      'sourceTotalWN, ' + 
                                                      'sourceIntensityWN, ' + 
                                                      'medianSourceTotal, ' + 
                                                      'medianSourceIntensity, ' +
                                                      'waterScore, ' + 
                                                      'waterUseTotal, ' +
                                                      'waterIntensityTotal, ' + 
                                                      'totalLocationBasedGHGEmissions,' + 
                                                      'totalLocationBasedGHGEmissionsIntensity'},
                                           auth = auth)

        # Parse the api call into a dictionary
        year_ending_dict = xmltodict.parse(year_ending_metrics.content)

        ## Pull the data from the api call into the year_data dictionary

        # Save the current year ending date
        year_data['Year Ending'] = datetime(year_ending - i, 
                                            month_ending, 
                                            monthrange(year_ending - i, month_ending)[1])
        
        # Add the units for each of the metrics for the first year that is pulled
        if i == 0:
            for j in [1, 2, 3, 4, 6, 7, 8, 9]:
                # If the metric exists, add it to the units of metrics list
                try:
                    units_of_metrics.append(year_ending_dict['propertyMetrics']['metric'][j]['@uom'])
                # If tht metric does not exist, add an empty string
                except:
                    units_of_metrics.append('')
                
        # Check to see if each metric is populated (a string) and then save it to the dictionary
        # If the metric is not populated - assign it to np.nan
        if type(year_ending_dict['propertyMetrics']['metric'][0]['value']) == str:
            year_data['ENERGY STAR Score'] = year_ending_dict['propertyMetrics']['metric'][0]['value']
        else:
            year_data['ENERGY STAR Score'] = 'N/A'

        if type(year_ending_dict['propertyMetrics']['metric'][1]['value']) == str:
            year_data[f"Weather Normalized Source Energy Use {units_of_metrics[0]}"] = year_ending_dict['propertyMetrics']['metric'][1]['value']
        else:
            year_data[f"Weather Normalized Source Energy Use {units_of_metrics[0]}"] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][2]['value']) == str:
            year_data[f"Weather Normalized Source Energy Use Intensity {units_of_metrics[1]}"] = year_ending_dict['propertyMetrics']['metric'][2]['value']
        else:
            year_data[f"Weather Normalized Source Energy Use Intensity {units_of_metrics[1]}"] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][3]['value']) == str:
            year_data[f"National Median Source Energy Use {units_of_metrics[2]}"] = year_ending_dict['propertyMetrics']['metric'][3]['value']
        else:
            year_data[f"National Median Source Energy Use {units_of_metrics[2]}"] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][4]['value']) == str:
            year_data[f"National Median Source Energy Use Intensity {units_of_metrics[3]}"] = year_ending_dict['propertyMetrics']['metric'][4]['value']
        else:
            year_data[f"National Median Source Energy Use Intensity {units_of_metrics[3]}"] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][5]['value']) == str:
            year_data['Water Score (Multifamily Only)'] = year_ending_dict['propertyMetrics']['metric'][5]['value']
        else:
            year_data['Water Score (Multifamily Only)'] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][6]['value']) == str:
            year_data[f"Total Water Use {units_of_metrics[4]}"] = year_ending_dict['propertyMetrics']['metric'][6]['value']
        else:
            year_data[f"Total Water Use {units_of_metrics[4]}"] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][7]['value']) == str:
            year_data[f"Water Use Intensity {units_of_metrics[5]}"] = year_ending_dict['propertyMetrics']['metric'][7]['value']
        else:
            year_data[f"Water Use Intensity {units_of_metrics[5]}"] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][8]['value']) == str:
            year_data[f"Total GHG Emissions {units_of_metrics[6]}"] = year_ending_dict['propertyMetrics']['metric'][8]['value']
        else:
            year_data[f"Total GHG Emissions {units_of_metrics[6]}"] = np.nan

        if type(year_ending_dict['propertyMetrics']['metric'][9]['value']) == str:
            year_data[f"Total GHG Emissions Intensity {units_of_metrics[7]}"] = year_ending_dict['propertyMetrics']['metric'][9]['value']
        else:
            year_data[f"Total GHG Emissions Intensity {units_of_metrics[7]}"] = np.nan

        # Append the year_data dictionary to the annual_metrics list
        annual_metrics.append(year_data)

    
    electric_kbtu = []
    gas_kbtu = []

    for i in range(5):
        # Pull the current years kbtu energy consumption
        monthly_kbtu_data = requests.get(domain + f"/property/{espm_id}/metrics/monthly?year={year_ending - i}&month={12}&measurementSystem=EPA", 
                                        headers = {'PM-Metrics': 'siteElectricityUseMonthly, siteNaturalGasUseMonthly'}, 
                                        auth = auth)
        # Parse the kbtu call into a dictionary
        kbtu_dict = xmltodict.parse(monthly_kbtu_data.content)
        
        if 'monthlyMetric' in kbtu_dict['propertyMetrics']['metric'][0]:
            for month in range(len(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'])):
                e_kbtu = {}
                e_kbtu['End Date'] = pd.Timestamp(datetime(int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][month]['@year']), 
                                                                            int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][month]['@month']), 
                                                                            monthrange(int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][month]['@year']), 
                                                                                        int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][month]['@month']))[1]))
                if type(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][month]['value']) == str:
                    e_kbtu['Electric kBtu'] = kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][month]['value']
                else:
                    e_kbtu['Electric kBtu'] = np.nan
                electric_kbtu.append(e_kbtu)
            
        if 'monthlyMetric' in kbtu_dict['propertyMetrics']['metric'][1]:
            for month in range(len(kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'])):
                g_kbtu = {}
                g_kbtu['End Date'] = pd.Timestamp(datetime(int(kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][month]['@year']), 
                                                                            int(kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][month]['@month']), 
                                                                            monthrange(int(kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][month]['@year']), 
                                                                                        int(kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][month]['@month']))[1]))
                if type(kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][month]['value']) == str:
                    g_kbtu['Gas kBtu'] = kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][month]['value']
                else:
                    g_kbtu['Gas kBtu'] = np.nan
                gas_kbtu.append(g_kbtu)
            
    e_kbtu_df = pd.DataFrame(electric_kbtu)
    g_kbtu_df = pd.DataFrame(gas_kbtu)

    kbtu_df = pd.merge(e_kbtu_df, g_kbtu_df, on = 'End Date', how = 'outer')

    # Format the datatypes of the kBtu consumption columns
    kbtu_df['Electric kBtu'] = pd.to_numeric(kbtu_df['Electric kBtu'])
    kbtu_df['Gas kBtu'] = pd.to_numeric(kbtu_df['Gas kBtu'])

    # Drop the NaN values - use thresh of 2 to drop the rows that have neither gas nor electric consumption
    kbtu_df.dropna(thresh = 2, inplace = True)
    
    # Sort the kbtu_df by End Date
    kbtu_df.sort_values(by = 'End Date', inplace = True)


    # Create a dataframe from the pulled metrics
    annual_df = pd.DataFrame(annual_metrics)
    # Drop the rows for the years that there is no data
    # Create a threshold to drop by to account for the AB802 properties without water
    if annual_df.dropna(thresh = 7).shape[0] == 0:
        threshold = 5
    else:
        threshold = 6
    annual_df.dropna(thresh = threshold, inplace = True)

    # Sort the values of the annual metrics by ascending Year Ending values
    annual_df.sort_values(by = 'Year Ending', ascending = True, inplace = True)
        
    return annual_df, kbtu_df