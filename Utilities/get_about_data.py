# Import dependencies
import requests
import xmltodict

# Create a function to pull the about data
def get_about_data(prop_id, domain, auth):
    # Get the property information for a given property id
    prop_info = requests.get(domain + f'/property/{prop_id}',
                        auth = auth)
    prop_info_dict = xmltodict.parse(prop_info.content)
    
    # Make a call to get the LA Building Id
    prop_ld_id_call = requests.get(domain + f'/property/{prop_id}/identifier/list', 
                                   auth = auth)
    prop_la_id_dict = xmltodict.parse(prop_ld_id_call.content)

    # Create a dictionary to hold the property's about data
    about_data = {}
    about_data['prop_name'] = prop_info_dict['property']['name']
    about_data['prop_address'] = prop_info_dict['property']['address']['@address1']
    about_data['prop_city'] = prop_info_dict['property']['address']['@city']
    about_data['prop_postal_code'] = prop_info_dict['property']['address']['@postalCode']
    about_data['prop_state'] = prop_info_dict['property']['address']['@state']
    about_data['prop_function'] = prop_info_dict['property']['primaryFunction']
    about_data['prop_sq_ft'] = prop_info_dict['property']['grossFloorArea']['value']

    # Check if the call for the LA Building ID was successful and appened the id if it did or None if it didn't
    if prop_la_id_dict['additionalIdentifiers'] is not None:
        about_data['prop_la_id'] = prop_la_id_dict['additionalIdentifiers']['additionalIdentifier']['value']
    else:
        about_data['prop_la_id'] = 'None'
        
    return about_data