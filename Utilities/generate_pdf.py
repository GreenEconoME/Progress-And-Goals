# Import dependencies
from fpdf import FPDF
import numpy as np
import copy
import io
from datetime import date
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
              name = 'Resources/NEW Green EconoME Logo.PNG', 
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

    for i in range(plot_metrics_df.shape[0]):
        pdf.set_xy(post_analytics_title_x, post_analytics_title_y + line_height * i)
        if i % 2 == 0:
            pdf.set_fill_color(93, 149, 119)
        else:
            pdf.set_fill_color(93, 129, 119)

        pdf.cell(w = pdf.epw, 
                 h = line_height, 
                 border = 1,
                 fill = True
            )

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

    if comp_periods[about_data['prop_la_id'][-1]] == int(year_ending):
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
    water_plot.write_image(hcf_consump_buff)
    # Plot the historical water data
    pdf.image(hcf_consump_buff,
              w = pdf.epw,
              h = (pdf.eph / 2) * 0.9)


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
             txt = 'Monthly Gas and Electric Consumption', 
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