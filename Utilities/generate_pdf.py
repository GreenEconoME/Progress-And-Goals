# Import dependencies
from fpdf import FPDF
import numpy as np
import copy
import io
from datetime import date
import math
import pandas as pd
from Utilities.plot_metrics import (graph_eu, graph_hcf, graph_es_score, 
                            graph_seui, graph_e_meters_overlay, 
                            graph_g_meters_overlay)

def generate_pdf(about_data, ann_metrics, prop_id, 
                year_ending, best_eui_change_year, 
                best_eui_change_value, best_wui_change_year, 
                best_wui_change_value, monthly_kbtu, water_df, 
                monthly_energy):
    pdf = FPDF()
    pdf.set_author('Kyle Gee')
    pdf.set_title('Progress and Goals Report')
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 30)

    # Set the background
    start_x = pdf.x
    start_y = pdf.y
    pdf.set_fill_color(206, 255, 246)
    pdf.cell(w = pdf.epw, 
             h = pdf.eph / 2,
             border = 1,
             txt = '', 
             fill = True
        )
    pdf.set_xy(start_x, start_y)

    # Add the logo to the top left of the pdf
    # Add width and height variables for the logo
    logo_w = 40
    logo_h = 54
    pdf.image(x = 11, 
              name = 'Resources/NEW Green EconoME Logo.png', 
              w = logo_w, 
              h = logo_h)

    pdf.set_xy(pdf.x + logo_w, 10)
    # Add the Progress and Goals Report title
    pdf.cell(w = pdf.epw - logo_w, 
             h = 20,
             txt = 'Progress and Goals Report', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
             border = 0,
             fill = False)

    # Add cell to place an empty gap between title and About Info
    pdf.set_xy(pdf.x, pdf.y + 10)
    pdf.set_font('helvetica', '', 23)
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
    pdf.set_xy(x = 10, y = 10 + logo_h + 1)
    pdf.set_font('helvetica', '', 65)
    # Set variables for the energy star score height and width
    es_score_w = 40
    es_score_h = 20
    pdf.cell(w = es_score_w,  
             h = es_score_h,  
             txt = f"**{ann_metrics.loc[0, 'Energy Star Score']}**", 
             markdown = True,
             border = 0, 
             align = 'C')


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

    # Add the address and the property use data (Right Column)
    pdf.set_font('helvetica', '', 12)
    pdf.multi_cell(w = (pdf.epw - es_score_w) / 2, 
                   h = None,
                   txt = '**Property Address:**\n' + 
                         f"{about_data['prop_address']}\n" + 
                         f"{about_data['prop_city']}, {about_data['prop_state']} {about_data['prop_postal_code']}\n" + 
                         f'\n' + 
                         f'**ESPM Property ID:** {prop_id}\n' + 
                         f"**LA Building ID:** {about_data['prop_la_id']}", 
                   border = 0,
                   align = 'L',
                   markdown = True)

    # Store the property address cell coordinates
    prop_add_x = pdf.x
    prop_add_y = pdf.y

    # Write Energy Star Score below the Energy Star Score number
    pdf.set_xy(10 , es_score_h + logo_h + 11)
    pdf.cell(w = es_score_w, 
             txt = 'Energy Star Score', 
             border = 0, 
             align = 'C')

    # Clear the coloring above the benchmarking analytics table
    pdf.set_xy(x = 10, y = max([prop_type_y, prop_add_y]) + 5)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(w = pdf.epw, 
             h = 10, 
             txt = '',
             border = "T",
             fill = True
        )

    # Color the Benchmarking Analytics area
    pdf.set_xy(10, max([prop_type_y, prop_add_y]) + 10)
    pdf.set_fill_color(93, 189, 119)
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
    plot_metrics_df = copy.deepcopy(ann_metrics)

    # Format the dataframe to interate through and add to the pdf file
    plot_metrics_df['Year Ending'] = [x.strftime('%Y-%m-%d') for x in plot_metrics_df['Year Ending']]
    plot_metrics_df =  plot_metrics_df.T.reset_index()
    plot_metrics_df.replace(np.nan, 'N/A', inplace = True)

    # Add the annual metrics to the pdf file
    pdf.set_font('helvetica', '', 5)

    # Set a line height to create gaps between each row of data
    line_height = pdf.font_size * 7

    # Define a helper function to color the rows
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
    
    # Iterate through where the table will be and color the energy, water and ghg rows
    for i in range(plot_metrics_df.shape[0]):
        pdf.set_xy(post_analytics_title_x, post_analytics_title_y + line_height * i)
        # Color the energy related rows
        if i <= 5:
            color_rows(r1 = 93, g1 = 149, b1 = 119, r2 = 93, g2 = 129, b2 = 119, 
                       iteration = i, current_line_height = line_height, pdf_width = pdf.epw)
        # Color the water related rows
        elif i <= 8:
            color_rows(r1 = 74, g1 = 197, b1 = 199, r2 = 65, g2 = 169, b2 = 171, 
                       iteration = i, current_line_height = line_height, pdf_width = pdf.epw)
        # Color the GHG rows   
        else:
            color_rows(r1 = 164, g1 = 209, b1 = 86, r2 = 148, g2 = 189, b2 = 77, 
                       iteration = i, current_line_height = line_height, pdf_width = pdf.epw)

    # Return to the location of the start of the benchmarking analytics table data
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

            if row_index in [2, 3, 4, 5, 8, 9, 10] and column_index == 'index':
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
            # print(f'Cell Value: {value}')
            # print(f'x: {pdf.x}, y: {pdf.y}')
            # print(f'Col index: {column_index}')
            # print(f'Row index: {row_index}')
        # After finishing the row, create a line break before adding the next row of data
        pdf.ln(line_height)

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

    if about_data['prop_la_id'] != 'None' and comp_periods[about_data['prop_la_id'][-1]] == int(year_ending):
        # Add the EBEWE reduction metrics
        pdf.set_font('helvetica', '', 17)
        pdf.set_fill_color(93, 189, 119)
        pdf.set_y(pdf.y + 3)
        pdf.cell(w = pdf.epw, 
                 h = 11, 
                 border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = '**EBEWE Phase II: Best Reductions**', 
                 markdown = True)

        pdf.set_fill_color(93, 149, 119)
        pdf.set_font('helvetica', '', 14)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = 'Weather Normalized Source EUI')

        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = 'Water Use Intensity')

        # Add the EBEWE reduction best shifts
        pdf.set_fill_color(93, 129, 119)
        pdf.set_font('helvetica', '', 11)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f'From {best_eui_change_year.split("/")[-1]} to {year_ending}: {best_eui_change_value}% shift')

        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f'From {best_wui_change_year.split("/")[-1]} to {year_ending}: {best_wui_change_value}% shift')

     # Add the shifts for buildings/years that are selected and are not for an EBEWE Compliance period
    else:
        # Calculate the shifts for the WN SEUI and WUI for the most recent two years within the benchmarking metrics
        latest_wnseui = float(ann_metrics['Weather Normalized Source Energy Use Intensity kBtu/ft²'].iloc[-1])
        previous_wnseui = float(ann_metrics['Weather Normalized Source Energy Use Intensity kBtu/ft²'].iloc[-2])
        wnseui_shift = round((latest_wnseui - previous_wnseui) / previous_wnseui * 100, 2)

        # Using partial matching - may not have a water meter to pull the units
        latest_wui = float(ann_metrics.filter(like = 'Water Use Intensity').iloc[-1])
        previous_wui = float(ann_metrics.filter(like = 'Water Use Intensity').iloc[-2])
        wui_shift = round((latest_wui - previous_wui) / previous_wui * 100, 2)

        # Check if the shifts are available, if not replace with N/A
        if math.isnan(wnseui_shift):
            wnseui_shift = 'N/A'
        else:
            wnseui_shift = str(wnseui_shift) + '% shift'
        if math.isnan(wui_shift):
            wui_shift = 'N/A'
        else:
            wui_shift = str(wui_shift) + '% shift'

        pdf.set_font('helvetica', '', 17)
        pdf.set_fill_color(93, 189, 119)
        pdf.set_y(pdf.y + 3)
        pdf.cell(w = pdf.epw, 
                 h = 11, 
                 border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = '**Recent Energy and Water Shifts**', 
                 markdown = True)

        pdf.set_fill_color(93, 149, 119)
        pdf.set_font('helvetica', '', 14)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = 'Weather Normalized Source EUI')

        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'LMARGIN',
                 new_y = 'NEXT',
                 fill = True,
                 txt = 'Water Use Intensity')

        # Add the EBEWE reduction best shifts
        pdf.set_fill_color(93, 129, 119)
        pdf.set_font('helvetica', '', 11)
        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f"From {ann_metrics['Year Ending'].iloc[-2].year} to {ann_metrics['Year Ending'].iloc[-1].year}: {wnseui_shift}")

        pdf.cell(w = pdf.epw / 2, 
                 h = 6, 
                 border = 1,
                 align = 'C',
                 new_x = 'RIGHT',
                 new_y = 'TOP',
                 fill = True,
                 txt = f"From {ann_metrics['Year Ending'].iloc[-2].year} to {ann_metrics['Year Ending'].iloc[-1].year}: {wui_shift}")


    ### Add the EBEWE Compliance due date table
    if about_data['prop_la_id'] != 'None':
        pdf.add_page()

        # Add the title for the EBEWE Compliance dates table
        pdf.set_font('helvetica', '', 20)
        pdf.set_fill_color(93, 189, 119)
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

        # Save the x and y coordinates after the ebewe compliance dates title
        post_ebewe_dates_title_x = pdf.x
        post_ebewe_dates_title_y = pdf.y

        ebewe_dates = pd.read_excel('Resources/EBEWE Dates.xlsx', header = None)
        col_width = pdf.epw / len(ebewe_dates.columns)
        for row_index, row in ebewe_dates.iterrows():
            for column_index, value in row.items():
                # Set the fill colors for the rows
                if row_index % 2 == 0:
                    pdf.set_fill_color(93, 149, 119)
                else:
                    pdf.set_fill_color(93, 129, 119)

                pdf.multi_cell(w = col_width, 
                               h = line_height, 
                               txt = value, 
                               align = 'C',
                               fill = True, 
                               border = 1, 
                               new_x="RIGHT", 
                               new_y="TOP",
                               max_line_height=pdf.font_size)
            pdf.ln(line_height)
            
        # Add the compliance information for the current property
        # Set the font size and add a gap between the dates table and the text
        pdf.set_font('helvetica', '', 12)
        pdf.set_xy(10, pdf.y + 15)
        pdf.write(txt = f"{about_data['prop_address']} has the Los Angeles building id: {about_data['prop_la_id']}. \n\n" + 
                  f"    - The compliance due date is Dec 1, {comp_periods[about_data['prop_la_id'][-1]]}.\n\n" +
                  f"    - The above benchmarking metrics can be used for the following EBEWE Phase II Exemptions:\n\n"
                  f"        - Avaliable energy exemptions include a 15% reduction in Weather Normalized Source EUI and an Energy Star Score of 75 or higher. \n\n" + 
                  f"        - A 20% reduction in Water Use Intensity can satisfy a water exemption.\n\n"
                  f"    - Weather Normalized Source EUI and Water Use Intensity values for Dec 31, {comp_periods[about_data['prop_la_id'][-1]] - 1} " + 
                      f"will be compared to the values from the following years: " + 
                      f"Dec 31, {[comp_periods[about_data['prop_la_id'][-1]] - x for x in range(2, 6)][0]}, " + 
                      f"Dec 31, {[comp_periods[about_data['prop_la_id'][-1]] - x for x in range(2, 6)][1]}, " + 
                      f"Dec 31, {[comp_periods[about_data['prop_la_id'][-1]] - x for x in range(2, 6)][2]} and " + 
                      f"Dec 31, {[comp_periods[about_data['prop_la_id'][-1]] - x for x in range(2, 6)][3]}. " + 
                      f"The percent changes between the final year of the comparative period to the other years " + 
                      f"will be used to determine if the above exemptions can be met.")
        
        # If the report was generated for the final year of the compliance period - generate exemption results
        if comp_periods[about_data['prop_la_id'][-1]] == int(year_ending):
            # Add the title for the EBEWE Exemption status section
            pdf.ln(pdf.font_size * 2)
            pdf.set_font('helvetica', '', 20)
            pdf.set_fill_color(93, 189, 119)
            pdf.cell(w = 0, 
                     h = 12,
                     txt = '**EBEWE Phase II Exemption Status**', 
                     new_x = 'LEFT',
                     new_y = 'NEXT',
                     align = 'C', 
                     border = 1,
                     markdown = True,
                     fill = True)
            
            # Create the text for the exemption messages
            if float(ann_metrics.loc[0, 'Energy Star Score']) >= 75:
                es_message = (f"- Achieved an Energy Star Score of {ann_metrics.loc[0, 'Energy Star Score']}.\n" + 
                              f"- Apply for Energy Star Certification to receive an energy exemption.")
                              
            else:
                es_message = f"- Did not achieve an Energy Star Score of 75 or above"
            if best_eui_change_value <= -15:
                eui_message = (f"- Satisfied the 15% Weather Normalized Source Energy Use Intensity Reduction.\n" + 
                               f"- From {best_eui_change_year.split('/')[-1]} to {year_ending}: {best_eui_change_value}% reduction.")
            else:
                eui_message = f"- Did not satisfy the 15% reduction for Weather Normalized Source EUI"
            if best_wui_change_value <= -20:
                wui_message = ("- Satisfied the 20% Water Use Intensity Reduction.\n" + 
                               f"- From {best_wui_change_year.split('/')[-1]} to {year_ending}: {best_wui_change_value}% reduction.")
            else:
                wui_message = f"- Did not Satisfy the 20% reduction for Water Use Intensity"
                
            # Add the ES Score row
            pdf.ln(pdf.font_size * 1.2)
            pdf.set_font('helvetica', '', 16)
            # ES Score Title block
            pdf.multi_cell(w = pdf.epw / 3, 
                           h = None,
                           txt = '**Energy Star Score**', 
                           new_x = 'RIGHT', 
                           new_y = 'TOP', 
                           align = 'C', 
                           border = 0, 
                           markdown = True)
            # ES Score Result block
            pdf.set_font('helvetica', '', 15)
            pdf.multi_cell(w = pdf.epw * 2 / 3, 
                           h = None,
                           txt = es_message, 
                           new_x = 'LEFT', 
                           new_y = 'NEXT', 
                           align = 'L', 
                           border = 0, 
                           markdown = True)
            
            # Add the WNSEUI Reduction row
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
                           txt = eui_message, 
                           new_x = 'LEFT', 
                           new_y = 'NEXT', 
                           align = 'L', 
                           border = 0, 
                           markdown = True)
            
            # Add the WUI Reduction row
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
                           txt = wui_message, 
                           new_x = 'LEFT', 
                           new_y = 'NEXT', 
                           align = 'L', 
                           border = 0, 
                           markdown = True)

    #### Generate and add the plots

    ## Monthly Consumption Plots
    pdf.add_page()

    # Add title for the first graph page
    pdf.set_font('helvetica', '', 30)
    pdf.set_fill_color(93, 189, 119)
    pdf.cell(w = 0, 
             h = 12,
             txt = 'Energy and Water Consumption', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
             border = 1,
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
    if water_plot is not None:
        water_plot.write_image(hcf_consump_buff)
        # Plot the historical water data
        pdf.image(hcf_consump_buff,
                  w = pdf.epw,
                  h = (pdf.eph / 2) * 0.9)
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
             txt = 'Source EUI and Energy Star Score', 
             new_x = 'LEFT',
             new_y = 'NEXT',
             align = 'C', 
             border = 1,
             fill = True)

    # Add the monthly Source Energy Use Intensity plot
    seui_buff = io.BytesIO()
    monthly_seui_plot = graph_seui(monthly_energy)
    monthly_seui_plot.write_image(seui_buff)
    pdf.image(seui_buff, 
              w = pdf.epw, 
              h = (pdf.eph / 2) * 0.9)

    # Add the monthly energy star score
    es_score_buff = io.BytesIO()
    monthly_es_plot = graph_es_score(monthly_energy)
    if monthly_es_plot is not None:
        monthly_es_plot.write_image(es_score_buff)
        pdf.image(es_score_buff, 
                  w = pdf.epw, 
                  h = (pdf.eph / 2) * 0.9)

    else:
        pdf.set_font('helvetica', '', 20)
        pdf.cell(w = 0, 
                 h = None,
                 txt = 'This Property does not qualify for an Energy Star Score.', 
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
             border = 1,
             fill = True)

    # Add the monthly consumption by electric meter
    e_meter_buff = io.BytesIO()
    monthly_e_meters = graph_e_meters_overlay(monthly_energy)
    if monthly_e_meters is not None:
        monthly_e_meters.write_image(e_meter_buff)
        pdf.image(e_meter_buff, 
                  w = pdf.epw, 
                  h = (pdf.eph / 2) * 0.9)
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
    if monthly_g_meters is not None:
        monthly_g_meters.write_image(g_meter_buff)
        pdf.image(g_meter_buff, 
                  w = pdf.epw, 
                  h = (pdf.eph / 2) * 0.9)
    else:
        pdf.set_font('helvetica', '', 20)
        pdf.cell(w = 0, 
                 h = None,
                 txt = 'This Property does not contain a gas meter.', 
                 border = 0, 
                 align = 'C')

    return bytes(pdf.output())