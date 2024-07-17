# Import dependencies
import requests
import xmltodict
import pandas as pd
import copy
import numpy as np
from calendar import monthrange
import math
from datetime import datetime
import streamlit as st

def pull_monthly_energy(prop_id, domain, auth): 
    # Make a call to get the meter associations for the property   
    meter_associations = requests.get(domain + f'/association/property/{prop_id}/meter', 
                                      auth = auth)

    # Parse the meter associations call into a dictionary
    meter_assoc_dict = xmltodict.parse(meter_associations.content)

    # Get a list of the energy meters ids to use for calls for consumption
    energy_meters = meter_assoc_dict['meterPropertyAssociationList']['energyMeterAssociation']['meters']['meterId']
    # If there is more than one energy meter - continue, else put the energy meter into a list to iterate through
    if type(energy_meters) == list:
        pass
    else:
        energy_meters = [meter_assoc_dict['meterPropertyAssociationList']['energyMeterAssociation']['meters']['meterId']]

    # Set the meter count to 0
    meter_count = 0

    # Iterate through the energy meters to pull meter information and consumption data
    for meter in energy_meters:
        # Using the meter Id, get the information for that meter
        meter_info = requests.get(domain + f'/meter/{meter}', 
                                  auth = auth)

        # Parse the metrics call
        meter_info_dict = xmltodict.parse(meter_info.content)

        # Get the type of meter and the meter name from the meter info to store into a meter descriptor which will be the column name 
        meter_descriptor = meter_info_dict['meter']['type'] + f" ({meter_info_dict['meter']['unitOfMeasure']})" + ' Meter: ' + meter_info_dict['meter']['name'] + f' Id: {meter}'

        # Get consumption data for the energy meter
        consumption_data = requests.get(domain + f'/meter/{meter}/consumptionData', 
                                        auth = auth)
        energy_consumption = xmltodict.parse(consumption_data.content)

        # Create a dataframe from the energy meter consumption
        energy_data = []
        # Create a variable to hold the key corresponding to the list of entries for delivery/consumption
        if 'meterDelivery' in energy_consumption['meterData']:
            consump_key = 'meterDelivery'
            delivery_key = 'deliveryDate'
            amount_key = 'quantity'
        else:
            consump_key = 'meterConsumption'
            delivery_key = 'endDate'
            amount_key = 'usage'
        # If there is a single entry for the meter, it will return a dictionary for the single entry
        if isinstance(energy_consumption['meterData'][consump_key], dict):
            monthly_data = {}
            monthly_data['End Date'] = energy_consumption['meterData'][consump_key][delivery_key]
            monthly_data[meter_descriptor] = energy_consumption['meterData'][consump_key][amount_key]

            energy_data.append(monthly_data)
        else:
            # Iterate through the energy consumption call, and store the usage for each date into a dictionary to append the the energy_data list
            for i in range(len(energy_consumption['meterData'][consump_key])):
                monthly_data = {}
                monthly_data['End Date'] = energy_consumption['meterData'][consump_key][i][delivery_key]
                monthly_data[meter_descriptor] = energy_consumption['meterData'][consump_key][i][amount_key]

                energy_data.append(monthly_data)

        # Create the energy dataframe for this meter
        meter_df = pd.DataFrame(energy_data)

        # Format the datatypes of the columns
        meter_df['End Date'] = pd.to_datetime(meter_df['End Date'])
        meter_df[meter_descriptor] = pd.to_numeric(meter_df[meter_descriptor])

        # Check if the end dates are set to the end of the month, 
        # if they are not then adjust the end date to be the end of the month that contains the majority of the billing period
        # Check if every month is the end of the month
        if not meter_df['End Date'].dt.is_month_end.sum() == len(meter_df['End Date']):

            # Store the year and month of the first value
            ending_year = meter_df.loc[0,'End Date'].year
            ending_month = meter_df.loc[0,'End Date'].month
            # Get the last day of the month
            last_day_of_month = monthrange(ending_year, 
                                           ending_month)[1]

            # Check if the end date is at least half of the month
            if meter_df.loc[0, 'End Date'].day >= math.floor(last_day_of_month/2):

                # Set the date as the end of the month
                meter_df.loc[0, 'End Date'] = pd.Timestamp(datetime(ending_year, 
                                                                      ending_month, 
                                                                      last_day_of_month))

            else:

                # Check to see if the ending month is january - if not subtract one month
                if ending_month != 1:
                    ending_month = ending_month - 1

                # If the ending month is January, set the ending month/year to be december of the previous year 
                else:
                    ending_month = 12
                    ending_year = ending_year - 1

                # Get the last day of the previous month
                last_day_of_month = monthrange(ending_year, 
                                               ending_month)[1]

                # Set the ending date to be the end of the previous month
                meter_df.loc[0, 'End Date'] = pd.Timestamp(datetime(ending_year, 
                                                                      ending_month, 
                                                                      last_day_of_month)) 
            for row in meter_df.index[1:]:
                # Get the previous year and month
                prev_row_year = meter_df.loc[row - 1, 'End Date'].year
                prev_row_month = meter_df.loc[row - 1, 'End Date'].month

                # Check if the previous rows ending month is january, set this rows ending month/year to dec of previous year
                if prev_row_month == 1:
                    new_month = 12
                    new_year = prev_row_year - 1
                    meter_df.loc[row, 'End Date'] = pd.Timestamp(datetime(new_year, 
                                                                            new_month, 
                                                                            monthrange(new_year, 
                                                                                       new_month)[1]))

                else:
                    meter_df.loc[row, 'End Date'] = pd.Timestamp(datetime(prev_row_year, 
                                                                            prev_row_month - 1, 
                                                                            monthrange(prev_row_year,
                                                                                       prev_row_month - 1)[1]))

        # If we are pulling the first meter, set the energy_df equal to the meter_df
        if meter_count == 0:
            energy_df = copy.deepcopy(meter_df)

        # Merge the meter_df into the existing energy_df
        else:
            energy_df = pd.merge(left = energy_df, right = meter_df, how = 'outer', left_on = 'End Date', right_on = 'End Date')

        # Increase the meter count
        meter_count += 1

    # Sort the energy_df by End Date and reset the index
    energy_df.sort_values(by = 'End Date', ascending = False, inplace = True)
    energy_df.reset_index(drop = True, inplace = True)

            
    return energy_df