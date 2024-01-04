# Import dependencies
from fpdf import FPDF
import numpy as np
import copy
import io
from datetime import date
import math
import calendar
import pandas as pd
from Utilities.plot_metrics import (graph_eu, graph_hcf, graph_es_score, 
                                    graph_seui, graph_e_meters_overlay, 
                                    graph_g_meters_overlay)
import streamlit as st

def earliest_full_data(df):
    # Check if there is both electric and gas data
    if not (df['Electric kBtu'].isna().all() or df['Gas kBtu'].isna().all()):
        # If there is gas data, trim the df to contain the values where there is both 
        df = df.loc[df['End Date'] >= max(df.loc[df['Electric kBtu'].first_valid_index(), 'End Date'], df.loc[df['Gas kBtu'].first_valid_index(), 'End Date'])]
        # Return the earliest date in the trimmed dataframe
        return df['End Date'].min()
    # If one of them is empty return the earliest date of the original dataframe
    else:
        return df['End Date'].min()

# Using the fpdf library, generate a progress and goals report for the selected property
def generate_pdf(about_data, ann_metrics, prop_id, 
                 year_ending, monthly_kbtu, water_df, 
                 monthly_energy, reissued_check, reissued_date = None):

    class PDF(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 7)
            self.cell(0, 
                     10, 
                     ' | '.join(['GREENECONOME.COM', 
                                '424-422-9696', 
                                'info@greeneconome.com', 
                                'CA Contractors License B and C-10 #1001368']),
                     align = 'C')

    # Create the pdf object and set the author and title
    # pdf = FPDF()
    pdf = PDF()
    pdf.set_author('Kyle Gee')
    pdf.set_title('Progress and Goals Report')
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 20)

    # Set the background for the top progress and goals section
    start_x = pdf.x
    start_y = pdf.y
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(w = pdf.epw, 
             h = pdf.eph / 2,
            #  border = 1,
             txt = '', 
             fill = True
        )
    pdf.set_xy(start_x, start_y)

    # Add the logo to the top left of the pdf
    # Add width and height variables for the logo
    logo_w = 80
    logo_h = round(logo_w / 4.3626)
    pdf.image(x = 11,
              y = 11, 
              name = 'Resources/NEW Green EconoME Logo.png', 
              w = logo_w, 
              h = logo_h)

    # Set the x,y coordinates to the right of the logo to write Progress and Goals Report
    pdf.set_xy(pdf.x + logo_w, 5)
    # Add the Progress and Goals Report title
    pdf.cell(w = pdf.epw - logo_w, 
             h = 20,
             txt = 'Progress and Goals Report', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
             border = 0,
             fill = False)

    # Add cell to place an empty gap between Progress and Goals Report and the About Info
    pdf.set_xy(pdf.x, pdf.y)
    pdf.set_font('helvetica', '', 18)
    pdf.multi_cell(w = 0, 
             h = None,
             txt = f"**{about_data['prop_name']}**\n",
             align = 'C',
             new_x = 'LEFT', 
             new_y = 'NEXT', 
             border = 0,
             markdown = True)

    # Add the Energy Star Score Cell 
    # Set the coordinates to be under the logo
    pdf.set_xy(x = 10, y = pdf.y + 2)
    pdf.set_font('helvetica', '', 65)
    # Set variables for the energy star score height and width
    es_score_w = 40
    es_score_h = 20
    # Insert the Energy Star Score for the selected year ending date
    pdf.cell(w = es_score_w,  
             h = es_score_h,  
             txt = f"**{ann_metrics.loc[0, 'Energy Star Score']}**", 
             markdown = True,
             border = 0, 
             align = 'C')
    bottom_of_es_cell = pdf.y + 2

    # Add the address and the property use data (Middle Column)
    pdf.set_font('helvetica', '', 12)
    pdf.multi_cell(w = (pdf.epw - es_score_w) / 2, 
                   h = None,
                   txt = f"**Primary Property Type:** {about_data['prop_function']}\n" + 
                         f"**Gross Floor Area:** {'{:,}'.format(int(about_data['prop_sq_ft']))}\n" + 
                         f'\n' + 
                         f"**For Year Ending:** {ann_metrics['Year Ending'].dt.date[0]}\n" + 
                         f"**Date Generated:** {date.today()}", 
                   border = 0, 
                   align = 'L',
                   markdown = True, 
                   new_x = 'RIGHT', 
                   new_y = 'TOP')

    # Store the property type cell coordinates
    prop_type_x = pdf.x
    prop_type_y = pdf.y

    # Add the address and the IDs (Right Column)
    pdf.set_font('helvetica', '', 12)
    id_line = []
    if about_data['prop_la_id'] != 'None':
        id_line.append(f"**LA Building ID:** {about_data['prop_la_id']}")
    if about_data['prop_ca_id'] != 'None':
        id_line.append(f"**CA Building ID:** {about_data['prop_ca_id']}")

    pdf.multi_cell(w = (pdf.epw - es_score_w) / 2, 
                   h = None,
                   txt = '**Property Address:**\n' + 
                         f"{about_data['prop_address']}\n" + 
                         f"{about_data['prop_city']}, {about_data['prop_state']} {about_data['prop_postal_code']}\n" + 
                         f'\n' + 
                         f'**ESPM Property ID:** {prop_id}\n' + 
                         '\n'.join(id_line), 
                   border = 0,
                   align = 'L',
                   markdown = True)

    # Store the property address cell coordinates
    prop_add_x = pdf.x
    prop_add_y = pdf.y

    # Write Energy Star Score below the Energy Star Score number
    # pdf.set_xy(10 , es_score_h + logo_h + 20)
    pdf.set_xy(10 , bottom_of_es_cell + es_score_h)
    pdf.cell(w = es_score_w, 
             txt = 'Energy Star® Score', 
             border = 0, 
             align = 'C')

    # Clear the coloring above the benchmarking analytics table
    # Fill a white rectangle under the lowest data, and add a boarder at the top (bottom of P&G about data section)
    pdf.set_xy(x = 10, y = max([prop_type_y, prop_add_y]) + 5)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(w = pdf.epw, 
             h = 10, 
             txt = '',
             border = "T",
             fill = True
        )

    # Color the Benchmarking Analytics title area
    pdf.set_xy(10, max([prop_type_y, prop_add_y]) + 10)
    # pdf.set_fill_color(93, 189, 119)
    pdf.cell(w = pdf.epw, 
             h = 12, 
             txt = '', 
             fill = True
        )

    # Write the title for the benchmarking analytics
    pdf.set_xy(x = 10, y = max([prop_type_y, prop_add_y]) + 10)
    pdf.set_font('helvetica', '', 20)
    pdf.cell(w = 0, 
             h = 12,
             txt = '**Benchmarking Analytics**', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
             border = 1,
             markdown = True,
             fill = False)


    # Save the location after writing the benchmarking analytics title
    post_analytics_title_x = pdf.x
    post_analytics_title_y = pdf.y

    ##### Write in the benchmarking analytics table
    # Create a copy of the annual metrics to format for displaying
    if 'Weather Normalized Source Energy Use Intensity ' in ann_metrics.columns:
        ann_metrics.rename(columns = {'Weather Normalized Source Energy Use Intensity ' : 'Weather Normalized Source Energy Use Intensity kBtu/ft²'}, 
                            inplace = True)
    plot_metrics_df = copy.deepcopy(ann_metrics)
    if about_data['prop_function'] != 'Multifamily Housing':
        plot_metrics_df.drop(columns = ['Water Score (Multifamily Only)'], inplace = True)

    ## Drop the columns that are not used in consultations
    # Iterate through the possible columns for wnseu, if not available won't have units
    for col in ['Weather Normalized Source Energy Use kBtu', 'Weather Normalized Source Energy Use ']:
        if col in plot_metrics_df.columns:
            plot_metrics_df.drop(columns = [col], inplace = True)
    # Drop the National Median Source Energy Use and Total Water Use columns (units don't get pulled if there is no data)
    plot_metrics_df = plot_metrics_df.loc[:,~plot_metrics_df.columns.str.contains('^National Median Source Energy Use', case=False)]
    plot_metrics_df = plot_metrics_df.loc[:,~plot_metrics_df.columns.str.contains('^Total Water Use', case=False)]

    # Format the dataframe to interate through and add to the pdf file
    plot_metrics_df['Year Ending'] = [x.strftime('%Y-%m-%d') for x in plot_metrics_df['Year Ending']]
    plot_metrics_df =  plot_metrics_df.T.reset_index()
    plot_metrics_df.replace(np.nan, 'N/A', inplace = True)

    # Set the font for the Benchmarking Analytics table
    pdf.set_font('helvetica', '', 5)

    # Set a line height to create determine the distance for a new line between each row of data
    line_height = pdf.font_size * 7

    # Define a helper function to color the rows of the tables
    def color_rows(r1, g1, b1, r2, g2, b2, iteration, current_line_height, pdf_width):
        if iteration % 2 == 0:
            pdf.set_fill_color(r1, g1, b1)
        else:
            pdf.set_fill_color(r2, g2, b2)

        pdf.cell(w = pdf_width, 
                 h = current_line_height, 
                 border = 1,
                 fill = True
            )

    for i in range(plot_metrics_df.shape[0]):
        pdf.set_xy(post_analytics_title_x, post_analytics_title_y + line_height * i)
        color_rows(r1 = 237, g1 = 237, b1 = 237, r2 = 255, g2 = 255, b2 = 255, 
                   iteration = i, current_line_height = line_height, pdf_width = pdf.epw)
            

    # Return to the location of the start of the benchmarking analytics table data to fill the colored cells with data
    pdf.set_xy(post_analytics_title_x, post_analytics_title_y)

    # Iterate through the dataframe to create cells for each value in the dataframe
    for row_index, row in plot_metrics_df.iterrows():
        for column_index, value in row.items():

            # Format the index column to be larger in size and smaller in font
            if column_index == 'index':
                alignment = 'L'
                bolden = '**'
                pdf.set_font('helvetica', '', 10)
                col_width = pdf.epw / (len(plot_metrics_df.columns) - 1)

            # If the current column is not the index, center and increase the size of the value with a smaller cell width
            else:
                alignment = 'C'
                bolden = ''
                pdf.set_font('helvetica', '', 11)
                col_width = (pdf.epw - pdf.epw / (len(plot_metrics_df.columns) - 1)) / (len(plot_metrics_df.columns) - 1)

            # If the value is Energy Star Score, replace it with Energy Star® Score
            if value == 'Energy Star Score':
                value = 'Energy Star® Score'

            # For the row indicies that have longer names and need to be on multiple lines, put in a multicell
            if row_index in [2, 3, 4, 5, 6, 7] and column_index == 'index':
                pdf.multi_cell(w = col_width, 
                               h = None, 
                               txt = bolden + str(value) + bolden,
                               align = alignment,
                               border = 0,
                               new_x = 'RIGHT', 
                               new_y = 'TOP', 
                               markdown = True)
            else:
                # Using the formatting defined above, create the cell for the dataframe value
                pdf.cell(w = col_width, 
                            h = line_height, 
                            txt = bolden + str(value) + bolden,
                            align = alignment,
                            border = 'L',
                            new_x = 'RIGHT', 
                            new_y = 'TOP', 
                            markdown = True)

        # After finishing the row, add a line break before adding the next row of data
        pdf.ln(line_height)

    # Create a dictionary to hold the last year of the compliance period and their corresponding last digit of the LADBS Building ID
    comp_periods = {'0' : 2020,
                    '1' : 2020, 
                    '2' : 2021, 
                    '3' : 2021, 
                    '4' : 2022, 
                    '5' : 2022, 
                    '6' : 2023, 
                    '7' : 2023, 
                    '8' : 2024, 
                    '9' : 2024}
    
    # Check if the reissued dates are being used
    # If they are, change the ids ending in 0, 1, 2, 3 to have a 2023 compliance year
    if reissued_check:
        comp_periods = {'0' : 2022,
                        '1' : 2022, 
                        '2' : 2022, 
                        '3' : 2022, 
                        '4' : 2022, 
                        '5' : 2022, 
                        '6' : 2023, 
                        '7' : 2023, 
                        '8' : 2024, 
                        '9' : 2024}
    
    
    # Check if there is an LADBS Building ID, and if the last digit corresponds with the last year of the compliance period
    if about_data['prop_la_id'] != 'None' and comp_periods[about_data['prop_la_id'][-1]] == int(year_ending):
        ## Add the EBEWE reduction metrics

        # Add the best reductions table's title
        pdf.set_font('helvetica', '', 17)
        # Old green coloring for headers
        # pdf.set_fill_color(93, 189, 119)
        pdf.set_y(pdf.y + 3)
        pdf.cell(w = pdf.epw, 
                 h = 11, 
                 border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = '**Best Energy And Water Shifts**', 
                 markdown = True)

        # Add column title - WN SEUI
        # Old coloring
        # pdf.set_fill_color(93, 149, 119)
        pdf.set_fill_color(237, 237, 237)
        pdf.set_font('helvetica', '', 14)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = 'Weather Normalized Source EUI')

        # Add column title - WUI
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = 'Water Use Intensity')

        # Add the EBEWE reduction best shifts - WNSEUI Shift
        
        # Filter the monthly energy dataframe down to the years that will be used to compare to the compliance period
        # i.e. the last month of the comparative period and the next 11 months
        # If the reissued dates are being used, change the filter for the months that will be used
        # to check if a satisfactory exemption is met
        if reissued_check:
            ## Need to create different masks for 0,1 and 2,3 (shifted one month)
            if reissued_date == 'September 7, 2023':
                energy_start_mask = (monthly_energy['End Date'] >= f'10-31-{year_ending}')
                energy_end_mask = (monthly_energy['End Date'] <= f'8-31-{year_ending + 1}')
                water_start_mask = (water_df['End Date'] >= f'10-31-{year_ending}')
                water_end_mask = (water_df['End Date'] <= f'8-31-{year_ending + 1}')
            elif reissued_date == 'October 7, 2023':
                energy_start_mask = (monthly_energy['End Date'] >= f'11-30-{year_ending}')
                energy_end_mask = (monthly_energy['End Date'] <= f'9-30-{year_ending + 1}')
                water_start_mask = (water_df['End Date'] >= f'11-30-{year_ending}')
                water_end_mask = (water_df['End Date'] <= f'9-30-{year_ending + 1}')
            # If the ladbs id doesn't end in 0,1,2, or 3, then the comparative period remains the same
            else:
                energy_start_mask = (monthly_energy['End Date'] >= f'12-31-{year_ending}')
                energy_end_mask = (monthly_energy['End Date'] <= f'11-30-{year_ending + 1}')
                water_start_mask = (water_df['End Date'] >= f'12-31-{year_ending}')
                water_end_mask = (water_df['End Date'] <= f'11-30-{year_ending + 1}')
        else:
            energy_start_mask = (monthly_energy['End Date'] >= f'12-31-{year_ending}')
            energy_end_mask = (monthly_energy['End Date'] <= f'11-30-{year_ending + 1}')
            water_start_mask = (water_df['End Date'] >= f'12-31-{year_ending}')
            water_end_mask = (water_df['End Date'] <= f'11-30-{year_ending + 1}')

        # Create a temp_df that holds the months that will be used to compare to the months in the comparative period
        temp_df = monthly_energy.loc[energy_start_mask & energy_end_mask]
        temp_df.reset_index(drop = True, inplace = True)

        # Create a list to hold the eui info for each month/year for the baseline periods
        eui_values = []
        # For each available eui in the period we will compare, gather that months eui for the previous years
        for index, row in temp_df.iterrows():
            for i in range(1, 5):
                eui_data = {}

                eui_data['Recent Year'] = row['End Date'].year
                eui_data['Recent Month'] = row['End Date'].month
                eui_data['Recent WNSEUI'] = row['Weather Normalized Source EUI (kBtu/ft²)']

                year_mask = (monthly_energy['End Date'].dt.year == (row['End Date'].year - i))
                month_mask = (monthly_energy['End Date'].dt.month == row['End Date'].month)


                eui_data['Comparative Year'] = row['End Date'].year - i
                eui_data['Comparative Month'] = row['End Date'].month
                eui_data['Comparative WNSEUI'] = monthly_energy.loc[year_mask & month_mask, 'Weather Normalized Source EUI (kBtu/ft²)'].item()
                eui_values.append(eui_data)


        # Create a dataframe of the EUI values     
        comparative_eui_df = pd.DataFrame(eui_values)
        # Crete a column that contains the shift from the baseline to the recent month
        comparative_eui_df['EUI Shift'] = (comparative_eui_df['Recent WNSEUI'] - comparative_eui_df['Comparative WNSEUI']) / comparative_eui_df['Comparative WNSEUI']
        # Sort the dataframe by the EUI shift and reset the index
        comparative_eui_df.sort_values(by = 'EUI Shift', inplace = True)
        comparative_eui_df.reset_index(drop = True, inplace = True)

        # Get the best eui shift and the period (from and to)
        best_eui_shift = round(comparative_eui_df.loc[0, 'EUI Shift'].item() * 100, 2)
        best_eui_from = f"{calendar.month_abbr[comparative_eui_df.loc[0, 'Comparative Month'].item()]} {comparative_eui_df.loc[0, 'Comparative Year'].item()}"
        best_eui_to = f"{calendar.month_abbr[comparative_eui_df.loc[0, 'Recent Month'].item()]} {comparative_eui_df.loc[0, 'Recent Year'].item()}"
        
        # Filter the monthly water dataframe down to the years that will be used to compare to the compliance period
        # i.e. the last month of the comparative period and the next 11 months
        temp_df = water_df.loc[water_start_mask & water_end_mask]
        temp_df.reset_index(drop = True, inplace = True)

        # Create a list to hold the wui info for each month/year for the baseline periods
        wui_values = []
        # For each available wui in the period we will compare, gather that months wui for the previous years
        for index, row in temp_df.iterrows():
            for i in range(1, 5):
                wui_data = {}

                wui_data['Recent Year'] = row['End Date'].year
                wui_data['Recent Month'] = row['End Date'].month
                wui_data['Recent WUI'] = row['Water Use Intensity']

                year_mask = (water_df['End Date'].dt.year == (row['End Date'].year - i))
                month_mask = (water_df['End Date'].dt.month == row['End Date'].month)


                wui_data['Comparative Year'] = row['End Date'].year - i
                wui_data['Comparative Month'] = row['End Date'].month
                wui_data['Comparative WUI'] = water_df.loc[year_mask & month_mask, 'Water Use Intensity'].item()
                wui_values.append(wui_data)


        # Create a dataframe of the WUI values     
        comparative_wui_df = pd.DataFrame(wui_values)
        # Crete a column that contains the shift from the baseline to the recent month
        comparative_wui_df['WUI Shift'] = (comparative_wui_df['Recent WUI'] - comparative_wui_df['Comparative WUI']) / comparative_wui_df['Comparative WUI']
        # Sort the dataframe by the WUI shift and reset the index
        comparative_wui_df.sort_values(by = 'WUI Shift', inplace = True)
        comparative_wui_df.reset_index(drop = True, inplace = True)

        # Get the best wui shift and the period (from and to)
        best_wui_shift = round(comparative_wui_df.loc[0, 'WUI Shift'].item() * 100, 2)
        best_wui_from = f"{calendar.month_abbr[comparative_wui_df.loc[0, 'Comparative Month'].item()]} {comparative_wui_df.loc[0, 'Comparative Year'].item()}"
        best_wui_to = f"{calendar.month_abbr[comparative_wui_df.loc[0, 'Recent Month'].item()]} {comparative_wui_df.loc[0, 'Recent Year'].item()}"

        # Old coloring
        # pdf.set_fill_color(93, 129, 119)
        # Add a check if there was no best_eui_change_year and value
        # This occurs when there is no WNSEUI for the year generated
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font('helvetica', '', 11)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f'From {best_eui_from} to {best_eui_to}: {best_eui_shift}% shift')

        # Add the EBEWE reduction best shifts - WUI Shift
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f'From {best_wui_from} to {best_wui_to}: {best_wui_shift}% shift')

     # If it is not the end of the building's compliance period,
     # Add the recent (last two years pulled) shift for WUI and WNSEUI 
    else:
        # Calculate the shifts for the WN SEUI and WUI for the most recent two years within the benchmarking metrics
        latest_wnseui = float(ann_metrics['Weather Normalized Source Energy Use Intensity kBtu/ft²'].iloc[-1])
        try:
            previous_wnseui = float(ann_metrics['Weather Normalized Source Energy Use Intensity kBtu/ft²'].iloc[-2])
        # If there is only one year of data, set the previous wnseui as the current
        except IndexError:
            previous_wnseui = latest_wnseui
        wnseui_shift = round((latest_wnseui - previous_wnseui) / previous_wnseui * 100, 2)

        # Using partial matching - may not have a water meter to pull the units used to create the column title
        latest_wui = float(ann_metrics.filter(like = 'Water Use Intensity').iloc[-1])
        try:
            previous_wui = float(ann_metrics.filter(like = 'Water Use Intensity').iloc[-2])
        except IndexError:
            previous_wui = latest_wui
        try:
            wui_shift = round((latest_wui - previous_wui) / previous_wui * 100, 2)
        except ZeroDivisionError:
            wui_shift = 'UNDEF'

        # Check if the shifts are available, if not replace with N/A
        if math.isnan(wnseui_shift):
            wnseui_shift = 'N/A'
        else:
            wnseui_shift = str(wnseui_shift) + '% shift'
        # Check first that it wasn't a zero division error
        if wui_shift != 'UNDEF':
            if math.isnan(wui_shift):
                wui_shift = 'N/A'
            else:
                wui_shift = str(wui_shift) + '% shift'

        # Add the Recent energy and water shifts table's title
        pdf.set_font('helvetica', '', 17)
        # Old green coloring for headers
        # pdf.set_fill_color(93, 189, 119)
        pdf.set_y(pdf.y + 3)
        pdf.cell(w = pdf.epw, 
                 h = 11, 
                #  border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = '**Recent Energy and Water Shifts**', 
                 markdown = True)

        # Add the WNSEUI shift column title
        # Old coloring
        # pdf.set_fill_color(93, 149, 119)
        pdf.set_fill_color(237, 237, 237)
        pdf.set_font('helvetica', '', 14)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = 'Weather Normalized Source EUI')

        # Add the WUI shift column title
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = 'Water Use Intensity')

        # Add the EBEWE reduction recent shifts - WNSEUI
        recent_year = ann_metrics['Year Ending'].iloc[-1].year
        try:
            second_most_recent_year = ann_metrics['Year Ending'].iloc[-2].year
        # If there are not more than one year, set the second most recent year to the most recent year
        except IndexError:
            second_most_recent_year = recent_year
        # Old Coloring
        # pdf.set_fill_color(93, 129, 119)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font('helvetica', '', 11)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f"From {second_most_recent_year} to {recent_year}: {wnseui_shift}")

        # Add the EBEWE reduction recent shifts - WUI
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f"From {second_most_recent_year} to {recent_year}: {wui_shift}")


    #### Generate and add the plots to the P&G report

    ## Monthly Consumption Plots
    pdf.add_page()

    # Add title for the Energy and Water Consumption plots page
    pdf.set_font('helvetica', '', 30)
    # Old green coloring for headers
    # pdf.set_fill_color(93, 189, 119)
    pdf.cell(w = 0, 
             h = 12,
             txt = 'Energy and Water Consumption', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
            #  border = 1,
             fill = True)

    # Generate and save the historical kbtu usage
    # Create an image object to hold the figure
    kbtu_buffer = io.BytesIO()
    kbtu_plot = graph_eu(monthly_kbtu, about_data['prop_address'])
    kbtu_plot.write_image(kbtu_buffer)
    # Plot the historical kbtu consumption
    pdf.image(kbtu_buffer, 
              w = pdf.epw, 
              h = (pdf.eph / 2) * 0.9)

    # Generate and save the historical water consumption
    # Create an image object to hold the figure
    hcf_consump_buff = io.BytesIO()
    # Generate the plot
    water_plot = graph_hcf(water_df, about_data['prop_address'])
    # Check if the plot exists - if there is no water meter graph_hcf will return None
    if water_plot is not None:
        water_plot.write_image(hcf_consump_buff)
        # Plot the historical water data
        pdf.image(hcf_consump_buff,
                  w = pdf.epw,
                  h = (pdf.eph / 2) * 0.9)
    # If there is no water consumption graph, write that there is no water meter
    else:
        pdf.set_font('helvetica', '', 20)
        pdf.cell(w = 0, 
                 h = None,
                 txt = 'This Property does not have a water meter.', 
                 border = 0, 
                 align = 'C')


    ## Monthly ESPM Metrics
    pdf.add_page()

    # Add title for the Source EUI and Energy Star Score page
    pdf.set_font('helvetica', '', 30)
    pdf.cell(w = 0, 
             h = 12,
             txt = 'Source EUI and Energy Star® Score', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
            #  border = 1,
             fill = True)

    # Add the monthly Source Energy Use Intensity plot
    seui_buff = io.BytesIO()
    monthly_seui_plot = graph_seui(monthly_energy.loc[monthly_energy['End Date'] >= earliest_full_data(monthly_kbtu)])
    monthly_seui_plot.write_image(seui_buff)
    pdf.image(seui_buff, 
              w = pdf.epw, 
              h = (pdf.eph / 2) * 0.9)

    # Add the monthly energy star score
    es_score_buff = io.BytesIO()
    monthly_es_plot = graph_es_score(monthly_energy.loc[monthly_energy['End Date'] >= earliest_full_data(monthly_kbtu)])
    # Check if there is a monthly ES plot - will return None if there is no historical ES scores
    if monthly_es_plot is not None:
        monthly_es_plot.write_image(es_score_buff)
        pdf.image(es_score_buff, 
                  w = pdf.epw, 
                  h = (pdf.eph / 2) * 0.9)
    # If there are no historical ES scores, write that the property does not qualify for an ES score
    else:
        pdf.set_font('helvetica', '', 20)
        pdf.cell(w = 0, 
                 h = None,
                 txt = 'This Property does not qualify for an Energy Star® Score.', 
                 border = 0, 
                 align = 'C')

    ## Monthly consumption by meters
    pdf.add_page()

    # Add title for the Source EUI and Energy Star Score page
    pdf.set_font('helvetica', '', 30)
    pdf.cell(w = 0, 
             h = 12,
             txt = 'Monthly Electric and Gas Consumption', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
            #  border = 1,
             fill = True)

    # Add the monthly consumption by electric meter
    e_meter_buff = io.BytesIO()
    monthly_e_meters = graph_e_meters_overlay(monthly_energy)
    # Check if there is a monthly electric meter - monthly_e_meters will return None if there is no meter
    if monthly_e_meters is not None:
        monthly_e_meters.write_image(e_meter_buff)
        pdf.image(e_meter_buff, 
                  w = pdf.epw, 
                  h = (pdf.eph / 2) * 0.9)
    # If there is no plot, write that the property does not have an electric meter
    else:
        pdf.set_font('helvetica', '', 20)
        pdf.cell(w = 0, 
                 h = None,
                 txt = 'This Property does not contain an electric meter.', 
                 border = 0, 
                 align = 'C')

    # Add the monthly consumption by gas meter
    g_meter_buff = io.BytesIO()
    monthly_g_meters = graph_g_meters_overlay(monthly_energy)
    # Cehck if there is a monthly gas consumption plot - monthly_g_meters will return None if there is no gas meters
    if monthly_g_meters is not None:
        monthly_g_meters.write_image(g_meter_buff)
        pdf.image(g_meter_buff, 
                  w = pdf.epw, 
                  h = (pdf.eph / 2) * 0.9)
    # If there is no plot, write that the property does not contain a gas meter
    else:
        pdf.set_font('helvetica', '', 20)
        pdf.cell(w = 0, 
                 h = None,
                 txt = 'This Property does not contain a gas meter.', 
                 border = 0, 
                 align = 'C')


    ### Add the EBEWE Compliance page
    # Check if the building has an LADBS Building ID for EBEWE - if it does, generate the page for EBEWE info
    if about_data['prop_la_id'] != 'None':
        pdf.add_page()

        # Add the title for the EBEWE Compliance dates table
        pdf.set_font('helvetica', '', 20)
        # Old green coloring for headers
        # pdf.set_fill_color(93, 189, 119)
        pdf.cell(w = 0, 
                 h = 12,
                 txt = '**EBEWE Compliance Dates**', 
                 new_x = 'LEFT',
                 new_y = 'NEXT',
                 align = 'C', 
                 border = 1,
                 markdown = True,
                 fill = True)

        # Set the font size for the compliance dates table
        pdf.set_font('helvetica', '', 10)

        # Read in the EBEWE Dates excel file
        ebewe_dates = pd.read_excel('Resources/EBEWE Dates.xlsx', header = None)
        # If using the reissed dates, alter the cells for the compliance due dates of the 0/1, 2/3 buildings
        if reissued_check:
            if reissued_date == 'September 7, 2023':
                comp_due_date = 'Sept 7, 2023*'
            else:
                comp_due_date = 'Oct 7, 2023*'
            # Change the complince due date
            ebewe_dates.at[1, 1] = comp_due_date
            ebewe_dates.at[2, 1] = comp_due_date


        # Save the column width to distribute the columns evenly across the page
        col_width = pdf.epw / len(ebewe_dates.columns)
        # Iterate through the rows and columns of the table to create a cell for each value in the table
        for row_index, row in ebewe_dates.iterrows():
            for column_index, value in row.items():
                # Set the fill colors for the rows to alternate shades of green
                if row_index % 2 == 0:
                    # Old coloring
                    # pdf.set_fill_color(93, 149, 119)
                    pdf.set_fill_color(237, 237, 237)
                else:
                    # Old coloring
                    # pdf.set_fill_color(93, 129, 119)
                    pdf.set_fill_color(255, 255, 255)
                # Make a cell to hold the table value
                pdf.multi_cell(w = col_width, 
                               h = line_height, 
                               txt = value, 
                               align = 'C',
                               fill = True, 
                               border = 1, 
                               new_x="RIGHT", 
                               new_y="TOP",
                               max_line_height=pdf.font_size)
            # After each row, create a line break to start the next row beneath
            pdf.ln(line_height)

        # Add in the note for historical benchmarking
        pdf.set_xy(10, pdf.y + 2)
        pdf.write(txt = ''.join(['* Green Econome can provide historic benchmarking and Phase II reporting, ', 
                                'to bring any past due EBEWE compliance up to date. ']))
        
        # Add the title for the most common EBEWE Exemptions
        pdf.ln(pdf.font_size * 2)
        pdf.set_font('helvetica', '', 20)
        # Old green coloring for headers
        # pdf.set_fill_color(93, 189, 119)
        pdf.cell(w = 0, 
                 h = 12,
                 txt = '**Most Common EBEWE Phase II Exemptions**', 
                 new_x = 'LEFT',
                 new_y = 'NEXT',
                 align = 'C', 
                #  border = 1,
                 markdown = True,
                 fill = True)
        
        # Add the ES Score row
        pdf.ln(pdf.font_size * 1.2)
        pdf.set_font('helvetica', '', 16)
        # ES Score Title block
        pdf.multi_cell(w = pdf.epw / 3, 
                       h = None,
                       txt = '**Energy Star® Score**', 
                       new_x = 'RIGHT', 
                       new_y = 'TOP', 
                       align = 'C', 
                       border = 0, 
                       markdown = True)
        # ES Score Result block
        pdf.set_font('helvetica', '', 15)
        pdf.multi_cell(w = pdf.epw * 2 / 3, 
                       h = None,
                       txt = '- An Energy Star® Score of 75 or higher can grant an Energy Exemption.', 
                       new_x = 'LEFT', 
                       new_y = 'NEXT', 
                       align = 'L', 
                       border = 0, 
                       markdown = True)
        
        ## Add the WNSEUI Reduction row
        pdf.ln(pdf.font_size * 1.2)
        pdf.set_font('helvetica', '', 16)
        # WNSEUI Title block
        pdf.multi_cell(w = pdf.epw / 3, 
                       h = None,
                       txt = '**Weather Normalized Source EUI Reduction**', 
                       new_x = 'RIGHT', 
                       new_y = 'TOP', 
                       align = 'C', 
                       border = 0, 
                       markdown = True)
        # WNSEUI Result block
        pdf.set_font('helvetica', '', 15)
        pdf.multi_cell(w = pdf.epw * 2 / 3, 
                       h = None,
                       txt = '- A 15% reduction in Weather Normalized Source EUI can grant an Energy Exemption.', 
                       new_x = 'LEFT', 
                       new_y = 'NEXT', 
                       align = 'L', 
                       border = 0, 
                       markdown = True)
        
        ## Add the WUI Reduction row
        pdf.ln(pdf.font_size * 1.2)
        pdf.set_font('helvetica', '', 16)
        # WUI Title block
        pdf.multi_cell(w = pdf.epw / 3, 
                       h = None,
                       txt = '**Water Use Intensity Reduction**', 
                       new_x = 'RIGHT', 
                       new_y = 'TOP', 
                       align = 'C', 
                       border = 0, 
                       markdown = True)
        # WUI Result block
        pdf.set_font('helvetica', '', 15)
        pdf.multi_cell(w = pdf.epw * 2 / 3, 
                       h = None,
                       txt = '- A 20% reduction in Water Use Intensity can grant a water exemption.', 
                       new_x = 'LEFT', 
                       new_y = 'NEXT', 
                       align = 'L', 
                       border = 0, 
                       markdown = True)
  
        # # Add in the note for the tolled compliance due dates if running for the reissued dates
        # if reissued_check:
        #     pdf.set_xy(10, pdf.y + 2)
        #     pdf.write(txt = ''.join(['* Change in dates due to the 2020-2022 tolled EBEWE deadlines.']))


        # # Set a variable to hold the date of compliance based on reissued due dates
        # if reissued_check:
        #     if reissued_date == 'September 7, 2023':
        #         due_date = 'Sept 7'
        #     elif reissued_date == 'October 7, 2023':
        #         due_date = 'Oct 7'
        #     else:
        #         due_date = 'Dec 1'
        # else:
        #     due_date = 'Dec 1'

    #     pdf.set_font('helvetica', '', 12)
    #     pdf.set_xy(10, pdf.y + 15)
    #     pdf.write(txt = f"{about_data['prop_address']} has the Los Angeles Building ID: {about_data['prop_la_id']}. \n\n" 
    #               f"- The compliance due date is {due_date}, {comp_periods[about_data['prop_la_id'][-1]] + 1}.\n\n" 
    #               f"- The above benchmarking metrics can be used for the following EBEWE Phase II Exemptions\n"
    #               f"    - A 15% reduction in Weather Normalized Source EUI or an Energy Star® Score of 75 or higher\n"
    #               f"      can satisfy an energy exemption. \n\n" 
    #               f"    - A 20% reduction in Water Use Intensity can satisfy a water exemption.\n\n"
    #               f"- Current Weather Normalized Source EUI and Water Use Intensity values will be compared to the 5\n"
    #               f"  year period preceding the building's compliance due date to detmine if the above exemptions are\n"
    #               f"  met")
        
    #     # If the report was generated for the final year of the compliance period - generate exemption results
    #     if comp_periods[about_data['prop_la_id'][-1]] == int(year_ending):
    #         # Add the title for the EBEWE Exemption status section
    #         pdf.ln(pdf.font_size * 2)
    #         pdf.set_font('helvetica', '', 20)
    #         # Old green coloring for headers
    #         # pdf.set_fill_color(93, 189, 119)
    #         pdf.cell(w = 0, 
    #                  h = 12,
    #                  txt = '**Current EBEWE Phase II Exemption Status***', 
    #                  new_x = 'LEFT',
    #                  new_y = 'NEXT',
    #                  align = 'C', 
    #                 #  border = 1,
    #                  markdown = True,
    #                  fill = True)
            
    #         # Add the message for the EBEWE Exemption status section
    #         # pdf.ln(pdf.font_size * 2)
    #         pdf.set_font('helvetica', '', 8)
    #         pdf.multi_cell(w = 0,
    #                     txt = ''.join(["*These options represent the current Phase II Exemption Eligibility ",
    #                                 "at the time of the running of this report. ", 
    #                                 "LADBS requires the most current data to determine Exemption Eligibility. ",
    #                                 "Due to this, Reduction Exemption metrics will need to be re-run after September ",
    #                                 "1st of the current reporting year."]), 
    #                     align = 'C')
            
    #         ## Create the text for the exemption messages determined by either satisfying the exemption or not
    #         # Check if there is an es score available
    #         if ann_metrics.loc[0, 'Energy Star Score'] == 'N/A':
    #             es_message = f"- Energy Star® Score not calculated for {ann_metrics['Year Ending'].dt.date[0]}"
    #         # Check for an ES score of 75 or higher
    #         elif float(ann_metrics.loc[0, 'Energy Star Score']) >= 75:
    #             es_message = (f"- Achieved an Energy Star® Score of {ann_metrics.loc[0, 'Energy Star Score']}.\n" + 
    #                           f"- Apply for Energy Star® Certification to receive an energy exemption.")
                              
    #         else:
    #             es_message = f"- Did not achieve an Energy Star® Score of 75 or above."
    #         # Check if there was at least a 15% reduction in WNSEUI
    #         # Check first if we have reassigned best_eui_shift to NA if it was not available during the year ending
    #         if best_eui_shift == 'NA':
    #             eui_message = f"- Weather Normalized Source EUI not available to check reduction."
    #         elif best_eui_shift <= -15:
    #             eui_message = (f"- Satisfied the 15% Weather Normalized Source Energy Use Intensity Reduction.\n" + 
    #                            f"- From {best_eui_from} to {best_eui_to}: {best_eui_shift}% reduction.")
    #         else:
    #             eui_message = f"- Did not satisfy the 15% reduction for Weather Normalized Source EUI."
    #         # Check if there was at least a 20% reduction in WUI
    #         if best_wui_shift == 'UNDEF':
    #             wui_message = f"- Did not Satisfy the 20% reduction for Water Use Intensity."
    #         elif best_wui_shift <= -20:
    #             wui_message = ("- Satisfied the 20% Water Use Intensity Reduction.\n" + 
    #                            f"- From {best_wui_from} to {best_wui_to}: {best_wui_shift}% reduction.")
    #         else:
    #             wui_message = f"- Did not Satisfy the 20% reduction for Water Use Intensity."
                
    #         ### Add the results for ES score WNEUI/WUI reductions
    #         ## Add the ES Score row
    #         pdf.ln(pdf.font_size * 1.2)
    #         pdf.set_font('helvetica', '', 16)
    #         # ES Score Title block
    #         pdf.multi_cell(w = pdf.epw / 3, 
    #                        h = None,
    #                        txt = '**Energy Star® Score**', 
    #                        new_x = 'RIGHT', 
    #                        new_y = 'TOP', 
    #                        align = 'C', 
    #                        border = 0, 
    #                        markdown = True)
    #         # ES Score Result block
    #         pdf.set_font('helvetica', '', 15)
    #         pdf.multi_cell(w = pdf.epw * 2 / 3, 
    #                        h = None,
    #                        txt = es_message, 
    #                        new_x = 'LEFT', 
    #                        new_y = 'NEXT', 
    #                        align = 'L', 
    #                        border = 0, 
    #                        markdown = True)
            
    #         ## Add the WNSEUI Reduction row
    #         pdf.ln(pdf.font_size * 1.2)
    #         pdf.set_font('helvetica', '', 16)
    #         # WNSEUI Title block
    #         pdf.multi_cell(w = pdf.epw / 3, 
    #                        h = None,
    #                        txt = '**Weather Normalized Source EUI Reduction**', 
    #                        new_x = 'RIGHT', 
    #                        new_y = 'TOP', 
    #                        align = 'C', 
    #                        border = 0, 
    #                        markdown = True)
    #         # WNSEUI Result block
    #         pdf.set_font('helvetica', '', 15)
    #         pdf.multi_cell(w = pdf.epw * 2 / 3, 
    #                        h = None,
    #                        txt = eui_message, 
    #                        new_x = 'LEFT', 
    #                        new_y = 'NEXT', 
    #                        align = 'L', 
    #                        border = 0, 
    #                        markdown = True)
            
    #         ## Add the WUI Reduction row
    #         pdf.ln(pdf.font_size * 1.2)
    #         pdf.set_font('helvetica', '', 16)
    #         # WUI Title block
    #         pdf.multi_cell(w = pdf.epw / 3, 
    #                        h = None,
    #                        txt = '**Water Use Intensity Reduction**', 
    #                        new_x = 'RIGHT', 
    #                        new_y = 'TOP', 
    #                        align = 'C', 
    #                        border = 0, 
    #                        markdown = True)
    #         # WUI Result block
    #         pdf.set_font('helvetica', '', 15)
    #         pdf.multi_cell(w = pdf.epw * 2 / 3, 
    #                        h = None,
    #                        txt = wui_message, 
    #                        new_x = 'LEFT', 
    #                        new_y = 'NEXT', 
    #                        align = 'L', 
    #                        border = 0, 
    #                        markdown = True)

    # Return the Progress and Goals PDF
    return bytes(pdf.output())