# Import dependencies
import plotly.graph_objects as go


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
                           # xaxis_title = 'Month', 
                           yaxis_title = 'Consumption (kBtu)', 
                           showlegend = True, 
                           legend=dict(orientation="h"))
    
    return kbtu_fig


###################################
###################################
# Create a function to graph historical water meter usage
def graph_hcf(water_df, prop_name):
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
    else:
        # Get a list of the electric meter columns to plot
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

    return hcf_fig

###################################
###################################
# Create function to graph the historical energy star scores
def graph_es_score(energy_df):
    if not energy_df['Energy Star Score'].isnull().all():
        es_trace = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                              y = energy_df['Energy Star Score'], 
                              name = 'Energy Star Score', 
                              mode = 'lines+markers', 
                              hovertemplate = 'Date: %{x}<br>Energy Star Score: %{y}<extra></extra>')
        data = [es_trace]
        es_fig = go.Figure(data = data)

        es_fig.update_layout(title = f'Monthly Energy Star Score', 
                             # xaxis_title = 'Date', 
                             yaxis_title = 'Energy Star Score', 
                             showlegend = True, 
                             legend=dict(orientation="h"))
        return es_fig

###################################
###################################
# Create a function to graph the WNSEUI and the National Median source eui
def graph_seui(energy_df):
    wnseui = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                        y = energy_df['Weather Normalized Source EUI (kBtu/ft²)'], 
                        name = 'Weather Normalized Source EUI', 
                        mode = 'lines+markers', 
                        hovertemplate = 'Date: %{x}<br>WN Source EUI: %{y} (kBtu/ft²)<extra></extra>')
    
    nat_med_seui = go.Scatter(x = energy_df.loc[11:, 'End Date'], 
                                y = energy_df['National Median Source EUI (kBtu/ft²)'], 
                                name = 'National Median Source EUI', 
                                mode = 'lines+markers', 
                                hovertemplate = 'Date: %{x}<br>Nat. Med. Source EUI: %{y} (kBtu/ft²)<extra></extra>')
    
    data = [wnseui, nat_med_seui]
    
    seui_fig = go.Figure(data = data)
    
    seui_fig.update_layout(title = f'Source Energy Use Intensity', 
                           # xaxis_title = 'Date', 
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