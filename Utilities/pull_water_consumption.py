# Import dependencies
import requests
import xmltodict
import pandas as pd

def pull_water_consumption(prop_id, domain, auth):
    # Pull the historical water consumption
    # Get the meters and their associations
    meter_associations = requests.get(domain + f'/association/property/{prop_id}/meter', 
                                      auth = auth)

    # Parse the meter associations call
    meter_assoc_dict = xmltodict.parse(meter_associations.content)
    
    # Check if the building has a water meter
    if 'waterMeterAssociation' in meter_assoc_dict['meterPropertyAssociationList'].keys():

        # Get a list of the energy meters ids
        water_meters = meter_assoc_dict['meterPropertyAssociationList']['waterMeterAssociation']['meters']['meterId']
        # If there is more than one energy meter - continue, else put the energy meter into a list to iterate through
        if type(water_meters) == list:
            # Set the meter count to 0
            meter_count = 0

            for meter in water_meters:
                # Using the meter Id, get the information for that meter
                meter_info = requests.get(domain + f'/meter/{meter}', 
                                        auth = auth)

                # Parse the metrics call
                meter_info_dict = xmltodict.parse(meter_info.content)

                # Get the type of meter and the meter name from the meter info
                meter_descriptor = meter_info_dict['meter']['type'] + f" ({meter_info_dict['meter']['unitOfMeasure']})" + ' Meter: ' + meter_info_dict['meter']['name'] + f' Id: {meter}'

                # Get consumption data for the water meter
                consumption_data = requests.get(domain + f'/meter/{meter}/consumptionData', 
                                        # headers = espm_headers,
                                        auth = auth)
                water_consumption = xmltodict.parse(consumption_data.content)

                # Create a dataframe from the energy meter consumption
                water_data = []
                for i in range(len(water_consumption['meterData']['meterConsumption'])):
                    monthly_data = {}
                    monthly_data['End Date'] = water_consumption['meterData']['meterConsumption'][i]['endDate']
                    monthly_data[meter_descriptor] = water_consumption['meterData']['meterConsumption'][i]['usage']

                    water_data.append(monthly_data)

                # Create the water dataframe
                meter_df = pd.DataFrame(water_data)

                # Format the dataframe columns
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

                # If we are pulling the first meter, set the water_df equal to the meter_df
                if meter_count == 0:
                    water_df = copy.deepcopy(meter_df)

                # Merge the meter_df into the existing water_df
                else:
                    water_df = pd.merge(left = water_df, right = meter_df, how = 'outer', left_on = 'End Date', right_on = 'End Date')


                meter_count += 1

            # Rename the water columns
            for col in water_df.columns:
                new_name = col.replace('Municipally Supplied Potable Water - Mixed Indoor/Outdoor (ccf (hundred cubic feet))', 'Water (HCF)')
                water_df.rename(columns = {col : new_name},
                            inplace = True)


            # Format the datatype of the water meter data columns
            water_df['End Date'] = pd.to_datetime(water_df['End Date'])

            # Insert a total water consumption column
            water_df.insert(1, 'Total HCF Consumption', water_df.sum(axis = 1))
            
        else:
            # Get consumption data for the water meter
            meter_data = requests.get(domain + f'/meter/{water_meters}/consumptionData', 
                                    auth = auth)

            # Parse the water consumption meter data into a dictionary
            water_consumption = xmltodict.parse(meter_data.content)

            # Create a dataframe from the water meter consumption
            water_data = []
            for i in range(len(water_consumption['meterData']['meterConsumption'])):
                monthly_data = {}
                monthly_data['End Date'] = water_consumption['meterData']['meterConsumption'][i]['endDate']
                monthly_data['Usage (HCF)'] = water_consumption['meterData']['meterConsumption'][i]['usage']

                water_data.append(monthly_data)

            # Create the water dataframe
            water_df = pd.DataFrame(water_data)

            # Format the datatype of the water meter data columns
            water_df['End Date'] = pd.to_datetime(water_df['End Date'])
            water_df['Usage (HCF)'] = pd.to_numeric(water_df['Usage (HCF)'])
        
        return water_df

    else:
        return None