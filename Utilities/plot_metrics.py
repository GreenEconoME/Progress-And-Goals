# Import dependencies
import plotly.graph_objects as go

# Define a function that will get the date of the earliest data that contains both electric and gas - given that there are both
# This will be used to trim the data for the graphs that are plotting ES scores and SEUI for dates where there is missing energy data
# Need this data trimmed - ie if there is no gas data but there is electric data - gives an inflated ES Score and a lower SEUI
def earliest_full_data(df):
    # Check if there is both electric and gas data
    if not df['Electric kBtu'].isna().all() or df['Gas kBtu'].isna().all():
        # If there is gas data, trim the df to contain the values where there is both 
        df = df.loc[df['End Date'] >= max(df.loc[df['Electric kBtu'].first_valid_index(), 'End Date'], df.loc[df['Gas kBtu'].first_valid_index(), 'End Date'])]
        # Return the earliest date in the trimmed dataframe
        return df['End Date'].min()
    # If one of them is empty return the earliest date of the original dataframe
    else:
        return df['End Date'].min()


###################################
###################################
# Create a function to graph the monthly consumption for electric and gas
def graph_eu(kbtu_df, prop_name):
    data = []
    if not kbtu_df['Electric kBtu'].isnull().all():
        elec_kbtu = go.Scatter(x = kbtu_df['End Date'],
                               y = kbtu_df['Electric kBtu'], 
                               name = 'Electric kBtu', 
                               mode = 'lines+markers',
                               hovertemplate = 'Date: %{x}<br>Electric Consumption: %{y:,.0f} kBtu<extra></extra>')
        data.append(elec_kbtu)
        
    if not kbtu_df['Gas kBtu'].isnull().all():
        gas_kbtu = go.Scatter(x = kbtu_df['End Date'], 
                              y = kbtu_df['Gas kBtu'],  
                              name = 'Gas kBtu',  
                              mode = 'lines+markers', 
                              hovertemplate = 'Date: %{x}<br>Gas Consumption: %{y:,.0f} kBtu<extra></extra>')
        
        data.append(gas_kbtu)
        
    kbtu_fig = go.Figure(data = data)
    
    kbtu_fig.update_layout(title = f'{prop_name}<br>Monthly Energy Consumption (kBtu)', 
                           yaxis_title = 'Consumption (kBtu)', 
                           showlegend = True, 
                           legend=dict(orientation="h"))
    
    return kbtu_fig


###################################
###################################
# Create a function to graph historical water meter usage
def graph_hcf(water_df, prop_name):
    # Check if a water_df was creted (would not get created without water meters)
    if water_df is not None:
        # Check to see if there is only one water meter - will have two columns - date and usage
        if water_df.shape[1] == 2:
            # Graphing the historical meter usage
            hcf_trace_1 = go.Scatter(
                    x = water_df['End Date'],
                    y = water_df['Usage (HCF)'],
                    name = 'HCF Consumption',
                    mode = 'lines+markers', 
                    hovertemplate = 'Month: %{x}<br>Consumption: %{y:,.0f} HCF<extra></extra>')

            hcf_trace_2 = go.Scatter(
                    x = water_df['End Date'],
                    y = [water_df['Usage (HCF)'].mean()] * len(water_df['End Date']),
                    name = 'Monthly Average',
                    line_dash = 'dash',
                    mode = 'lines', 
                    hovertemplate = 'Monthly Average: %{y:,.1f} HCF<extra></extra>')

            data = [hcf_trace_1, hcf_trace_2]

            hcf_fig = go.Figure(data = data)

            hcf_fig.update_layout(title = f'{prop_name}<br>Monthly Water Consumption (HCF)', 
                                  yaxis_title = 'Consumption (HCF)', 
                                  yaxis_tickformat = '%{text:,}', 
                                  legend=dict(orientation="h"))
            # Return the hcf fig
            return hcf_fig
        
        # If there were more than one water meter, plot the water meters by meter
        else:
            # Get a list of the water meter columns to plot
            usage_columns = []
            for col in water_df.columns:
                if 'HCF' in col:
                    usage_columns.append(col)

            fig = go.Figure()
            for col in usage_columns:
                fig.add_trace(go.Scatter(x = water_df.dropna(subset = usage_columns, how = 'all')['End Date'],
                                         y = water_df.dropna(subset = usage_columns, how = 'all')[col],
                                         name = col,
                                         mode = 'lines+markers',
                                         hovertemplate = '%{y:,.0f} HCF'))

            fig.update_layout(
                            hovermode = 'x unified', 
                            title = f'Water Meter Monthly Consumption', 
                            yaxis_title = 'Consumption (HCF)', 
                            legend=dict(orientation="h"))

            # Check if anything was plotted, if so return the figure, if not return None
            if usage_columns:
                return fig
            else:
                return None
    # Return None if a water df was never created
    else:
        return None
        

###################################
###################################
# Create function to graph the historical energy star scores
def graph_es_score(energy_df):
    # Check if there are non null ES Score values, if there are - plot the historical ES scores
    if not energy_df['Energy Star Score'].isnull().all():
        es_trace = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                              y = energy_df['Energy Star Score'], 
                              name = 'Energy Star Score', 
                              mode = 'lines+markers', 
                              hovertemplate = 'Date: %{x}<br>Energy Star Score: %{y}<extra></extra>')
        data = [es_trace]
        es_fig = go.Figure(data = data)

        es_fig.update_layout(title = f'Monthly Energy Star Score', 
                             yaxis_title = 'Energy Star Score', 
                             showlegend = True, 
                             legend=dict(orientation="h"))
        return es_fig

###################################
###################################
# Create a function to graph the WNSEUI and the National Median source eui
def graph_seui(energy_df):
    # Create a trace for the WNSEUI
    wnseui = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                        y = energy_df['Weather Normalized Source EUI (kBtu/ft²)'], 
                        name = 'Weather Normalized Source EUI', 
                        mode = 'lines+markers', 
                        hovertemplate = 'Date: %{x}<br>WN Source EUI: %{y} (kBtu/ft²)<extra></extra>')
    
    # Create a trace for the national median source eui
    nat_med_seui = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                                y = energy_df['National Median Source EUI (kBtu/ft²)'], 
                                name = 'National Median Source EUI', 
                                mode = 'lines+markers', 
                                hovertemplate = 'Date: %{x}<br>Nat. Med. Source EUI: %{y} (kBtu/ft²)<extra></extra>')
    
    # Add the traces to the data list
    data = [wnseui, nat_med_seui]
    
    # Create the figure
    seui_fig = go.Figure(data = data)
    
    # Add the title, axis title, add legend to bottom of plot
    seui_fig.update_layout(title = f'Source Energy Use Intensity', 
                           yaxis_title = 'Energy Use Intensity (kBtu/ft²)', 
                           legend=dict(orientation="h"))
    
    return seui_fig


###################################
###################################
# Create a function to graph the electric meters monthly consumption
def graph_e_meters_overlay(energy_df):
    # Get a list of the electric meter columns to plot
    usage_columns = []
    for col in energy_df.columns:
        if 'kWh' in col:
            usage_columns.append(col)
            
    fig = go.Figure()
    # Iterate through the columns that contain kWh and create a trace for each one
    for col in usage_columns:
        fig.add_trace(go.Scatter(x = energy_df.dropna(subset = usage_columns, how = 'all')['End Date'],
                                 y = energy_df.dropna(subset = usage_columns, how = 'all')[col],
                                 name = col,
                                 mode = 'lines+markers',
                                 hovertemplate = '%{y:,.0f} kWh'))
        
    fig.update_layout(hovermode = 'x unified', 
                      title = f'Electric Meter Monthly Consumption', 
                      yaxis_title = 'kWh Consumption', 
                      legend=dict(orientation="h"))
    
    # Check if anything was plotted, if so return the figure, if not return None
    if usage_columns:
        return fig
    else:
        return None

###################################
###################################
# Create a function to graph the gas meters monthly consumption
def graph_g_meters_overlay(energy_df):
    # Get a list of the electric meter columns to plot
    usage_columns = []
    for col in energy_df.columns:
        if 'therm' in col:
            usage_columns.append(col)
            
    fig = go.Figure()
    # Iterate through the columns that contain 'therm' and create a trace for each to plot
    for col in usage_columns:
        fig.add_trace(go.Scatter(x = energy_df.dropna(subset = usage_columns, how = 'all')['End Date'],
                                 y = energy_df.dropna(subset = usage_columns, how = 'all')[col],
                                 name = col,
                                 mode = 'lines+markers',
                                 hovertemplate = '%{y:,.0f} Therms'))
        
    fig.update_layout(hovermode = 'x unified', 
                      title = f'Gas Meter Monthly Consumption', 
                      yaxis_title = 'Therm Consumption', 
                      legend=dict(orientation="h"))
    
    # Check if anything was plotted, if so return the figure, if not return None
    if usage_columns:
        return fig
    else:
        return None