# Import dependencies
import xmltodict
import requests
from datetime import datetime
from calendar import monthrange
import numpy as np
import pandas as pd
import math

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
                                                      'totalGHGEmissions,' + 
                                                      'totalGHGEmissionsIntensity'},
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
            year_data['Energy Star Score'] = year_ending_dict['propertyMetrics']['metric'][0]['value']
        else:
            year_data['Energy Star Score'] = 'N/A'

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

        # Make a call to pull the historical monthly kBtu data for electric and gas
        kbtu_data = []
        for i in range(5):
            # Pull the current years kbtu energy consumption
            monthly_kbtu_data = requests.get(domain + f"/property/{espm_id}/metrics/monthly?year={year_ending-i}&month={month_ending}&measurementSystem=EPA", 
                                             headers = {'PM-Metrics': 'siteElectricityUseMonthly, siteNaturalGasUseMonthly'}, 
                                             auth = auth)
            # Parse the kbtu call into a dictionary
            kbtu_dict = xmltodict.parse(monthly_kbtu_data.content)

            # Loop through the response dictionary and add the monthly usage to the monthly kbtu dict
            for i in range(len(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'])):
                monthly_kbtu = {}
                # Add the year, month, date as the End Date value
                monthly_kbtu['End Date'] = pd.Timestamp(datetime(int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][i]['@year']), 
                                                                     int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][i]['@month']), 
                                                                     monthrange(int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][i]['@year']), 
                                                                                int(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][i]['@month']))[1]))

                # Check if the consumption exists for that month and add it to the monthly kbtu dict
                # If there is no electric or gas data for that month, fill the value with a nan
                if type(kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][i]['value']) == str:
                    monthly_kbtu['Electric kBtu'] = kbtu_dict['propertyMetrics']['metric'][0]['monthlyMetric'][i]['value']
                else:
                    monthly_kbtu['Electric kBtu'] = np.nan

                if type(kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][i]['value']) == str:
                    monthly_kbtu['Gas kBtu'] = kbtu_dict['propertyMetrics']['metric'][1]['monthlyMetric'][i]['value']
                else:
                    monthly_kbtu['Gas kBtu'] = np.nan

                # Append the current years monthly kbtu values to the kbtu_data list
                kbtu_data.append(monthly_kbtu)

    # Create the kbtu dataframe
    kbtu_df = pd.DataFrame(kbtu_data)

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
    annual_df.dropna(thresh = 7, inplace = True)
    
    # Sort the values of the annual metrics by ascending Year Ending values
    annual_df.sort_values(by = 'Year Ending', ascending = True, inplace = True)
    
    ## Get the best WNSEUI and WUI % Changes from the compliance period and the final year of the compliance period
    # Create a list to hold the percent change and year of each of the WNSEUI values
    eui_percent_changes = []
    
    # Create a variable to hold the final year's WN SEUI value
    final_value = float(annual_df.loc[annual_df['Year Ending'] == annual_df.iloc[-1, annual_df.columns.get_loc('Year Ending')], f'Weather Normalized Source Energy Use Intensity {units_of_metrics[1]}'].item())
    
    # Loop through the years and get the percent change compared to the final year in the compliance period
    for year in annual_df['Year Ending'].iloc[:-1]:
        current_value = float(annual_df.loc[annual_df['Year Ending'] == year, f'Weather Normalized Source Energy Use Intensity {units_of_metrics[1]}'].item())
        
        # Append the percent change and the year to the percent changes list
        eui_percent_changes.append(((final_value - current_value) / current_value, year.strftime('%m/%d/%Y')))
    
    # Save the best eui percent change and the corresponding year
    best_eui_change_year = filter_tuple_list(eui_percent_changes, min(eui_percent_changes, key = lambda x: float('inf') if math.isnan(x[0]) else x[0])[0])
    best_eui_change_value = round(min(eui_percent_changes, key = lambda x: float('inf') if math.isnan(x[0]) else x[0])[0] * 100, 2)

    # Create a list to hold the percent change and year of each of the WUI values
    wui_percent_changes = []
    
    # Create a variable to hold the final year's WUI value
    final_value = float(annual_df.loc[annual_df['Year Ending'] == annual_df.iloc[-1, annual_df.columns.get_loc('Year Ending')], f'Water Use Intensity {units_of_metrics[5]}'].item())
    
    # Loop through the years and get the percent change compared to the final year in the compliance period
    for year in annual_df['Year Ending'].iloc[:-1]:
        current_value = float(annual_df.loc[annual_df['Year Ending'] == year, f'Water Use Intensity {units_of_metrics[5]}'].item())
        
        # Append the percent change and the year to the percent changes list                      
        wui_percent_changes.append(((final_value - current_value) / current_value, year.strftime('%m/%d/%Y')))
    
    # Save the best eui percent change and the corresponding year
    best_wui_change_year = filter_tuple_list(wui_percent_changes, min(wui_percent_changes, key = lambda x: float('inf') if math.isnan(x[0]) else x[0])[0])
    best_wui_change_value = round(min(wui_percent_changes, key = lambda x: float('inf') if math.isnan(x[0]) else x[0])[0] * 100, 2)
    
    
    return annual_df, kbtu_df, best_eui_change_year, best_eui_change_value, best_wui_change_year, best_wui_change_value