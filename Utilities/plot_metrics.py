# Import dependencies
import plotly.graph_objects as go
import plotly.express as px

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
                               marker_color = 'blue',
                               hovertemplate = 'Date: %{x}<br>Electric Consumption: %{y:,.0f} kBtu<extra></extra>')
        data.append(elec_kbtu)
        
    if not kbtu_df['Gas kBtu'].isnull().all():
        gas_kbtu = go.Scatter(x = kbtu_df['End Date'], 
                              y = kbtu_df['Gas kBtu'],  
                              name = 'Gas kBtu',  
                              mode = 'lines+markers',
                              marker_color = 'red', 
                              hovertemplate = 'Date: %{x}<br>Gas Consumption: %{y:,.0f} kBtu<extra></extra>')
        
        data.append(gas_kbtu)
        
    kbtu_fig = go.Figure(data = data)
    
    kbtu_fig.update_layout(title = f'{prop_name}<br>MONTHLY ENERGY CONSUMPTION (kBtu)', 
                           yaxis_title = 'Consumption (kBtu)',
                           font_family = 'Arial',
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
                    marker_color = 'blue', 
                    hovertemplate = 'Month: %{x}<br>Consumption: %{y:,.0f} HCF<extra></extra>')

            hcf_trace_2 = go.Scatter(
                    x = water_df['End Date'],
                    y = [water_df['Usage (HCF)'].mean()] * len(water_df['End Date']),
                    name = 'Monthly Average',
                    line_dash = 'dash',
                    mode = 'lines', 
                    marker_color = 'red', 
                    hovertemplate = 'Monthly Average: %{y:,.1f} HCF<extra></extra>')

            data = [hcf_trace_1, hcf_trace_2]

            hcf_fig = go.Figure(data = data)

            hcf_fig.update_layout(title = f'{prop_name}<br>MONTHLY WATER CONSUMPTION (HCF)', 
                                  yaxis_title = 'Consumption (HCF)', 
                                  yaxis_tickformat = '%{text:,}', 
                                  font_family = 'Arial',
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
            colors = px.colors.qualitative.Plotly
            for count, col in enumerate(usage_columns):
                fig.add_trace(go.Scatter(x = water_df.dropna(subset = usage_columns, how = 'all')['End Date'],
                                         y = water_df.dropna(subset = usage_columns, how = 'all')[col],
                                         name = col,
                                         mode = 'lines+markers',
                                         marker_color = colors[count % (len(colors) - 1)],
                                         hovertemplate = '%{y:,.0f} HCF'))

            fig.update_layout(
                            hovermode = 'x unified', 
                            title = 'WATER METER MONTHLY CONSUMPTION', 
                            yaxis_title = 'Consumption (HCF)',
                            font_family = 'Arial', 
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
                              name = 'ENERGY STAR Score', 
                              mode = 'lines+markers',
                              marker_color = 'blue', 
                              hovertemplate = 'Date: %{x}<br>Energy Star Score: %{y}<extra></extra>')

        es_trace_2 = go.Scatter(x = energy_df['End Date'],
                                y = [75] * len(energy_df['End Date']),
                                name = 'ENERGY STAR Score Target',
                                line_dash = 'dash',
                                mode = 'lines', 
                                marker_color = 'green',
                                hovertemplate = 'ES Certifical Goal<extra></extra>')
                    
        data = [es_trace, es_trace_2]
        es_fig = go.Figure(data = data)

        es_fig.update_layout(title = f'MONTHLY ENERGY STAR SCORE', 
                             yaxis_title = 'ENERGY STAR Score', 
                             showlegend = True, 
                             font_family = 'Arial',
                             legend=dict(orientation="h"))
        return es_fig

###################################
###################################
# Create a function to graph the WNSEUI and the National Median source eui
def graph_seui(energy_df):
    # Create a trace for the WNSEUI
    wnseui = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                        y = energy_df['Weather Normalized Source EUI (kBtu/ft²)'], 
                        name = 'Building Energy Use Intensity (EUI)', 
                        mode = 'lines+markers', 
                        marker_color = 'blue',
                        hovertemplate = 'Date: %{x}<br>WN Source EUI: %{y} (kBtu/ft²)<extra></extra>')
    
    # Create a trace for the national median source eui
    nat_med_seui = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                                y = energy_df['National Median Source EUI (kBtu/ft²)'], 
                                name = 'National Median Source EUI', 
                                mode = 'lines+markers', 
                                marker_color = 'red',
                                hovertemplate = 'Date: %{x}<br>Nat. Med. Source EUI: %{y} (kBtu/ft²)<extra></extra>')
    
    # Add the traces to the data list
    data = [wnseui, nat_med_seui]
    
    # Create the figure
    seui_fig = go.Figure(data = data)
    
    # Add the title, axis title, add legend to bottom of plot
    seui_fig.update_layout(title = 'MONTHLY OVERALL ENERGY USAGE ON A SQ. FT. BASIS<br>MONTHLY ENERGY USE VS. NATIONAL MEDIAN COMPARISON (SOURCE EUI)', 
                           yaxis_title = 'Energy Use Intensity (kBtu/ft²)', 
                           font_family = 'Arial',
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
    colors = px.colors.qualitative.Plotly
    for count, col in enumerate(usage_columns):
        fig.add_trace(go.Scatter(x = energy_df.dropna(subset = usage_columns, how = 'all')['End Date'],
                                 y = energy_df.dropna(subset = usage_columns, how = 'all')[col],
                                 name = col,
                                 mode = 'lines+markers',
                                 marker_color = colors[count % (len(colors) - 1)],
                                 hovertemplate = '%{y:,.0f} kWh'))
        
    fig.update_layout(hovermode = 'x unified', 
                      title = 'MONTHLY ELECTRIC METER CONSUMPTION (kWh)', 
                      yaxis_title = 'kWh Consumption', 
                      font_family = 'Arial',
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
    colors = px.colors.qualitative.Plotly
    for count, col in enumerate(usage_columns):
        fig.add_trace(go.Scatter(x = energy_df.dropna(subset = usage_columns, how = 'all')['End Date'],
                                 y = energy_df.dropna(subset = usage_columns, how = 'all')[col],
                                 name = col,
                                 mode = 'lines+markers',
                                 marker_color = colors[count % (len(colors) - 1)],
                                 hovertemplate = '%{y:,.0f} Therms'))
        
    fig.update_layout(hovermode = 'x unified', 
                      title = 'MONTHLY GAS METER CONSUMPTION (Therms)', 
                      yaxis_title = 'Therm Consumption', 
                      font_family = 'Arial',
                      legend=dict(orientation="h"))
    
    # Check if anything was plotted, if so return the figure, if not return None
    if usage_columns:
        return fig
    else:
        return None