# Import dependencies
import requests
import xmltodict

# Create a function to pull the about data
def get_about_data(prop_id, domain, auth):
    # Get the property information for a given property id
    prop_info = requests.get(domain + f'/property/{prop_id}',
                        auth = auth)
    # Parse the call into a dictionary
    prop_info_dict = xmltodict.parse(prop_info.content)
    
    # Make a call to get the LA Building Id
    prop_la_id_call = requests.get(domain + f'/property/{prop_id}/identifier/list', 
                                   auth = auth)
    # Parse the call into a dictionary
    prop_la_id_dict = xmltodict.parse(prop_la_id_call.content)

    # Create a dictionary to hold the property's about data
    about_data = {}
    # Parse the property information call and store the relevant about data within the dictionary
    about_data['prop_name'] = prop_info_dict['property']['name']
    about_data['prop_address'] = prop_info_dict['property']['address']['@address1']
    about_data['prop_city'] = prop_info_dict['property']['address']['@city']
    about_data['prop_postal_code'] = prop_info_dict['property']['address']['@postalCode']
    about_data['prop_state'] = prop_info_dict['property']['address']['@state']
    about_data['prop_function'] = prop_info_dict['property']['primaryFunction']
    about_data['prop_sq_ft'] = prop_info_dict['property']['grossFloorArea']['value']

    # Check if the call for the LA Building ID was successful and appened the id if it did or None if it didn't
    if prop_la_id_dict['additionalIdentifiers'] is not None:
        # If there are more than one additional identifier, iterate through them to grab the LA building ID identifier
        if type(prop_la_id_dict['additionalIdentifiers']['additionalIdentifier']) == list:
            for i in range(len(prop_la_id_dict['additionalIdentifiers']['additionalIdentifier'])):
                if prop_la_id_dict['additionalIdentifiers']['additionalIdentifier'][i]['additionalIdentifierType']['@name'] == 'Los Angeles Building ID':
                    about_data['prop_la_id'] = prop_la_id_dict['additionalIdentifiers']['additionalIdentifier'][i]['value']
        # If there is only one identifier, add it as the property la id
        else:
            about_data['prop_la_id'] = prop_la_id_dict['additionalIdentifiers']['additionalIdentifier']['value']
    # If there are no additional identifiers, set the property's la building id to 'None'
    else:
        about_data['prop_la_id'] = 'None'
        
    # Return the about_data dictionary
    return about_data