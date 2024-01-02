# Import dependencies
import streamlit as st
from base64 import b64encode
from Utilities.get_about_data import get_about_data
from Utilities.pull_prop_data import pull_prop_data
from Utilities.pull_water_consumption import pull_water_consumption
from Utilities.pull_monthly_energy import pull_monthly_energy
from Utilities.generate_pdf import generate_pdf
from Utilities.pull_monthly_metrics import pull_monthly_metrics
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
                            options = [2023, 2022, 2021, 2020, 2019,
                                        2018, 2017, 2016])
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

# Add a checkbox that will allow to calculate the reissued dates for la buildings ending in 0, 1, 2, 3
reissued_check = st.checkbox(label = 'Run P&G with reissued dates.', 
                            value = False, 
                            help = ' '.join(['This will alter the comparative period used for', 
                                             'the EBEWE properties with LADBS IDs ending in 0, 1, 2 and 3.'])
                            )
if reissued_check:
    reissued_date = st.selectbox('Select the reissued due date.', 
                                options = ['September 7, 2023', 'October 7, 2023'])
    st.caption('Select the reissued due date that you would like to be used to calculate the EBEWE reductions.')
else:
    reissued_date = None

# Create a button to generate the report
if st.button('Generate Progress and Goals Report'):
    with st.spinner('Generating Progress and Goals Report'):

        # Check if the building and date selections are entered
        if (credential_upload and 
            prop_id and 
            year_ending and 
            month_select is not None) and (
            prop_id != 123456789):

            with st.spinner("Pulling property information data."):
                # Pull the about data
                about_data = get_about_data(prop_id, domain, auth)

            with st.spinner('Pulling annual metrics and monthly kBtu data.'):
                # Pull the property data
                (ann_metrics, 
                monthly_kbtu) = pull_prop_data(prop_id, 
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

            with st.spinner('Pulling annual metrics.'):
                # Pull the annual metrics and add them to the energy and water dfs
                monthly_energy, water_df = pull_monthly_metrics(monthly_energy, water_df, domain, auth, prop_id)

            with st.spinner('Generating Progress and Goals PDF.'):
                # Generate the progress and goals report
                p_and_g_report = generate_pdf(about_data, ann_metrics, prop_id, 
                                              year_ending, monthly_kbtu, water_df, 
                                              monthly_energy, reissued_check, reissued_date)

            # Add a button to download the Progress and Goals report
            st.download_button(
                label="Download Progress and Goals Report",
                data=p_and_g_report,
                file_name=f"{about_data['prop_address']} Progress and Goals Report.pdf",
                mime="application/pdf"
            )
            st.caption(f"Click to download the Progress and Goals report for {about_data['prop_address']}")
            # Display the plotly graphs on the streamlit app
            st.write(graph_eu(monthly_kbtu, about_data['prop_address']))
            st.write(graph_hcf(water_df, about_data['prop_address']))
            # st.write(graph_es_score(monthly_energy.loc[monthly_energy['End Date'] >= earliest_full_data(monthly_kbtu)]))
            # st.write(graph_seui(monthly_energy.loc[monthly_energy['End Date'] >= earliest_full_data(monthly_kbtu)]))
            st.write(graph_e_meters_overlay(monthly_energy))
            st.write(graph_g_meters_overlay(monthly_energy))

            
                        
            