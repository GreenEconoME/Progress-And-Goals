# Import dependencies
import requests
import xmltodict
import pandas as pd
from calendar import monthrange


# Make a volume converter to handle standardize the meter entries to be graphed together
class VolumeConverter:
    @staticmethod
    def convert(value, meter_type, current_units, conversions):
        conversion_factor = conversions[meter_type][current_units]
        return float(value) * conversion_factor


def pull_monthly_energy(prop_id, domain, auth): 
    # Add a conversions table to standardize the meter data before plotting it
    conversions = {
            'Electric': {
                'kWh (thousand Watt-hours)' : 1, 
                '(kBtu (thousand Btu))' : 0.000293071,
                'kBtu (thousand Btu)' : 0.000293071
            },
            'Electric on Site Solar' : {
                '(kWh (thousand Watt-hours))' : -1, 
                'kWh (thousand Watt-hours)' : -1, 
                '(MWh (million Watt-hours))' : -0.001,
                'MWh (million Watt-hours)' : -0.001
            },
            'Natural Gas': {
                'therms' : 1,
                '(kBtu (thousand Btu))' : 0.010002388,
                'kBtu (thousand Btu)' : 0.010002388,
                '(MBtu (million Btu))' : 10.002388,
                'MBtu (million Btu)' : 10.002388,
                'ccf (hundred cubic feet)' : 1.037
            },
            'Propane': {
                'cf (cubic feet)' : 0.02565826330532213, 
                'Gallons (US)' : 0.916
            }, 
            'Municipally Supplied Potable Water - Indoor': {
                'ccf (hundred cubic feet)' : 0.748052,
                'KGal (thousand gallons) (US)' : 1
            },
            'Municipally Supplied Potable Water - Outdoor': {
                'ccf (hundred cubic feet)' : 0.748052,
                'KGal (thousand gallons) (US)' : 1
            },
            'Municipally Supplied Potable Water - Mixed Indoor/Outdoor': {
                'ccf (hundred cubic feet)' : 0.748052,
                '(cf (cubic feet))' : 0.00748052,
                'cf (cubic feet)' : 0.00748052,
                'Gallons (US)' : 1,
                'cGal (hundred gallons) (US)' : .1,
                'kcf (thousand cubic feet)' : 7.48052,
                'KGal (thousand gallons) (US)' : 1
            }, 
            'Municipally Supplied Reclaimed Water - Outdoor' : {
                '(ccf (hundred cubic feet))' : 0.748052,
                'ccf (hundred cubic feet)' : 0.748052,
                'KGal (thousand gallons) (US)' : 1
            }, 
            'Municipally Supplied Reclaimed Water - Mixed Indoor/Outdoor' : {
                '(ccf (hundred cubic feet))' : 0.748052,
                'ccf (hundred cubic feet)' : 0.748052,
                'KGal (thousand gallons) (US)' : 1
            }
        }

    # Create a dictionary to hold the mappings for the standard units for each meter type
    standard_units = {
        'Electric': 'kWh',
        'Electric on Site Solar' : 'kWh',
        'Municipally Supplied Potable Water - Indoor': 'Gallons',
        'Municipally Supplied Reclaimed Water - Mixed Indoor/Outdoor': 'Gallons',
        'Municipally Supplied Potable Water - Outdoor': 'Gallons',
        'Municipally Supplied Potable Water - Mixed Indoor/Outdoor': 'Gallons',
        'Natural Gas': 'therms',
        'Propane': 'therms'
    }
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

    # Initialize an empty list to store dataframes
    meter_dataframes = []

    # Iterate through the energy meters to pull meter information and consumption data
    for meter in energy_meters:
        # Using the meter Id, get the information for that meter
        meter_info = requests.get(domain + f'/meter/{meter}', 
                                  auth = auth)

        # Parse the meter call
        meter_info_dict = xmltodict.parse(meter_info.content)

        # Get the type of meter and the meter name from the meter info to store into a meter descriptor which will be the column name 
        meter_descriptor = meter_info_dict['meter']['type'] + f" ({standard_units[meter_info_dict['meter']['type']]})" + ' Meter: ' + meter_info_dict['meter']['name'] + f' Id: {meter}'

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

        # Handle single and multiple entries
        consumption_entries = energy_consumption['meterData'][consump_key]
        if isinstance(consumption_entries, dict):
            consumption_entries = [consumption_entries]

        for entry in consumption_entries:
            data = {
                'End Date': pd.to_datetime(entry[delivery_key]),
                meter_descriptor: VolumeConverter.convert(entry[amount_key], 
                                                            meter_info_dict['meter']['type'], 
                                                            meter_info_dict['meter']['unitOfMeasure'], 
                                                            conversions)
            }
            energy_data.append(data)

        # Create the energy dataframe for this meter
        meter_df = pd.DataFrame(energy_data)

        # Resample to monthly data
        meter_df.set_index('End Date', inplace=True)
        meter_df = meter_df.resample('M').sum().reset_index()

        meter_dataframes.append(meter_df)

    # Merge all meter dataframes on 'Date'
    energy_df = pd.DataFrame()
    for meter_df in meter_dataframes:
        if energy_df.empty:
            energy_df = meter_df
        else:
            energy_df = pd.merge(energy_df, meter_df, on='End Date', how='outer')

    # Sort the energy_df by Date and reset the index
    energy_df.sort_values(by='End Date', ascending=False, inplace=True)
    energy_df.reset_index(drop=True, inplace=True)

    return energy_df
