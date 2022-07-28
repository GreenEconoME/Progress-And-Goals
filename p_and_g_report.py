# Import dependencies
import streamlit as st
from base64 import b64encode
from Utilities.get_about_data import get_about_data
from Utilities.pull_prop_data import pull_prop_data
from Utilities.pull_water_consumption import pull_water_consumption
from Utilities.pull_monthly_energy import pull_monthly_energy
from Utilities.generate_pdf import generate_pdf
from Utilities.plot_metrics import (graph_eu, graph_hcf, graph_es_score, 
                            graph_seui, graph_e_meters_overlay, 
                            graph_g_meters_overlay)

# Set a title for the page
st.markdown("<h1 style = 'text-align: center; color: green;'>Green EconoME</h1>", unsafe_allow_html = True)
st.markdown("<h2 style = 'text-align: center; color: black;'>Progress and Goals Report</h2>", unsafe_allow_html = True)

# Set the domain for the API calls
domain = 'https://portfoliomanager.energystar.gov/ws'

# Load credentials for the API calls into the auth variable
credential_upload = st.file_uploader('Upload ESPM API Credentials')
if credential_upload:
    creds = []
    for line in credential_upload:
        creds.append(line.decode().strip())
    auth = (creds[0], creds[1])

st.caption('Upload the API credentials within a .txt file with the Username and Password on seperate lines. <br>' + 
            'The .txt file should be of the following format:<br>' + 
            'Username<br>' + 
            'Password', unsafe_allow_html = True)

# Create a dictionary to hold the numeric value of the month selection
month_dict = {'Jan': 1, 'Feb' : 2, 'Mar' : 3, 'Apr' : 4, 'May' : 5, 
                'Jun' : 6, 'Jul' : 7, 'Aug' : 8, 'Sep' : 9, 'Oct' : 10,
                'Nov' : 11, 'Dec' : 12}

# Add an input for the ESPM property ID
prop_id = int(st.text_input('Enter the Property ID', 
                            value = 123456789))
st.caption('Enter the Energy Star Portfolio Manager property ID.')

# Add a select box to choose the year ending
year_ending = st.selectbox('Select the year ending', 
                            options = [2022, 2021, 2020, 2019,
                                        2018, 2017, 2016, 2015])
st.caption('Select the final year of metrics you would like to see.<br>' + 
            'The Progress and Goals Report will include five years of data, ending with this year', 
            unsafe_allow_html = True)

# Add a selectbox to choose the month for the year ending
month_select = st.selectbox('Select the month', 
                            options = ['Dec', 'Nov', 'Oct', 'Sep', 'Aug', 
                                        'Jul', 'Jun', 'May', 'Apr', 'Mar',
                                        'Feb', 'Jan'])
st.caption('Select the month that will be used to pull the year ending metrics for.')

# Grab the numberical value from the month dict for the month within the year ending
month_ending = month_dict[month_select]

# Create a button to generate the report
if st.button('Generate Progress and Goals Report'):
    with st.spinner('Generating Progress and Goals Report'):

        if (credential_upload and 
            prop_id and 
            year_ending and 
            month_select is not None) and(
            prop_id != 123456789):

            with st.spinner("Pulling property information data."):

                # Pull the about data
                about_data = get_about_data(prop_id, domain, auth)

            with st.spinner('Pulling annual metrics and monthly kBtu data.'):
                # Pull the property data
                (ann_metrics, 
                monthly_kbtu, 
                best_eui_change_year, 
                best_eui_change_value, 
                best_wui_change_year, 
                best_wui_change_value) = pull_prop_data(prop_id, 
                                                        year_ending, 
                                                        month_ending, 
                                                        domain, 
                                                        auth)

            with st.spinner('Pulling monthly water consumption.'):
                # Pull the water dataframe
                water_df = pull_water_consumption(prop_id, domain, auth)

            with st.spinner('Pulling monthly gas and electricity consumption.'):
                # Pull the energy dataframe
                monthly_energy = pull_monthly_energy(prop_id, domain, auth)

            with st.spinner('Generating Progress and Goals PDF.'):
                # Generate the progress and goals report
                p_and_g_report = generate_pdf(about_data, ann_metrics, prop_id, 
                                                year_ending, best_eui_change_year, 
                                                best_eui_change_value, best_wui_change_year, 
                                                best_wui_change_value, monthly_kbtu, water_df, 
                                                monthly_energy)

            with st.spinner('Encoding PDF to display and download.'):
                # Embed the progress and goals report to display it:
                base64_pdf = b64encode(p_and_g_report).decode("utf-8")

                # Display the progress and goals report on the page                                   
                pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="400" type="application/pdf">'
                st.markdown(pdf_display, unsafe_allow_html=True)


            # Add a button to download the Progress and Goals report
            st.download_button(
                label="Download Progress and Goals Report",
                data=p_and_g_report,
                file_name="Progress and Goals Report.pdf",
                mime="application/pdf"
            )
            st.caption(f"Click to download the Progress and Goals report for {about_data['prop_address']}")

            st.write(graph_eu(monthly_kbtu, about_data['prop_address']))
            st.write(graph_hcf(water_df, about_data['prop_address']))
            st.write(graph_es_score(monthly_energy))
            st.write(graph_seui(monthly_energy))
            st.write(graph_e_meters_overlay(monthly_energy))
            st.write(graph_g_meters_overlay(monthly_energy))

            
                        
            