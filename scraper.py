# %%
import os, sys
from bs4 import BeautifulSoup
from selenium import webdriver
import csv
import requests
import pandas as pd
import numpy as np
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Initialise driver
driver = webdriver.Safari()

# %%
def room_schedule_header() -> list:

    weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa']
    quarters = ['00', '15', '30', '45']
    hours = ['07', '08', '09']+[str(i) for i in range(10, 25)]

    labels = []

    for hour in hours:
        for quarter in quarters:
            for weekday in weekdays:
                labels.append('{}_{}_{}'.format(hour, quarter, weekday))

            if hour == '24':
                break

    return labels

# %%
def room_details_header(soup : BeautifulSoup) -> list:
    '''
    Collects Overview names (Building, Floor/Room, etc.)
    '''
    header = [row.text.strip() for row in soup.find_all('th')]

    return header[2:]

# %%
def retrieve_room_details(room_details_link, header) -> list:
    '''
    Returns `list` containing room details
    '''

    for i in range(3): print()
    print(f'URL: {room_details_link}')
    # Accesses room-link
    driver.get(room_details_link)

    # Wait until the page is fully loaded
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'table-matrix')))

    # Searches for the first table-matrix, containing the room overview
    room_detail_tables = driver.find_elements_by_css_selector('.table-matrix')
    #print(room_detail_tables)
    overview_table = room_detail_tables[0].get_attribute('innerHTML')
    overview_table_soup = BeautifulSoup(overview_table, 'html.parser')

    all_details = overview_table_soup.find_all('td')

    # Since the the features are not always the same, we keep track only of the needed features and enter nan values for the rest
    room_detail = [np.nan for i in range(len(header))]
    overview_points = [point.text.strip() for point in overview_table_soup.find_all('th')[2:]]

    for i, point in enumerate(overview_points):
        if '\xad' in point:
            overview_points[i] = point.replace('\xad', '')


    set_header = set(header)
    set_overview_points = set(overview_points)


    intersection = set_header.intersection(set_overview_points)
    intersection_indeces = [i for i, x in enumerate(overview_points) if x in intersection]


    index = 0

    for i in range(len(header)):
        if not header[i] in intersection:
            continue 

        room_detail[i] = all_details[intersection_indeces[index]].text.strip()
        index += 1

    return room_detail

# %%
def retrieve_room_schedule(room_url:str) -> list:
    '''
    Returns schedule of room
    '''
    
    
    room_schedule = room_schedule_header()
    schedule = {}
    for i in room_schedule:
        schedule[i] = np.nan
        

    # If there is no schedule!
    if room_url == '':
        return list(schedule.values())

    driver.get(room_url)

    # Wait until the page is fully loaded
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'scrollarea-content')))

    schedule_html = driver.find_elements_by_css_selector('.scrollarea-content')[0].get_attribute('innerHTML')

    room_soup = BeautifulSoup(schedule_html, 'html.parser')

    table = room_soup.find('tbody')

    # Needed to match event with correct day
    days_translation = {'Monday':'mo', 'Tuesday':'tu', 'Wednesday':'we', 'Thursday':'th', 'Friday':'fr', 'Saturday':'sa', 'Sunday':'su'}


    for row in table.find_all('tr'):

        for day in row.find_all('td'):
            if 'aria-label' in str(day):
                #schedule.append(schedule[-6])
                #continue
                label = day.get('aria-label')

                #print(f'day:{day}, label:{label}')

                # Filters out name of the event
                module_name = label.split(',')[0]


                # Filters out duration of event
                label_split = label.split(',')

                # Time_stamp not always in same slot
                time_stamp = None

                for i, label in enumerate(label_split):
                    if 'o\'clock' in label:
                        time_stamp = label
                        day_name = label_split[i-2][1:]
                        break
                
                if time_stamp == None:
                    continue
                
                pattern = r'(\d{2}:\d{2})  o\'clock to (\d{2}:\d{2})  o\'clock\)$'
                match = re.search(pattern, time_stamp)
                
                if match:
                    start_time = match.group(1)
                    end_time = match.group(2)


                start = start_time.replace(':', '_') + '_{}'.format(days_translation[day_name])
                end = end_time.replace(':', '_') + '_{}'.format(days_translation[day_name])


                for i in room_schedule[room_schedule.index(start):room_schedule.index(end)]:
                    if days_translation[day_name] in i:
                        schedule[i] = module_name                




                # Following code prone to errors as number of 'td' elements not constant

                # event_duration = int(end_time.replace(':', ''))-int(start_time.replace(':',''))
                # event_duration = event_duration//100 * 60
                
                # # Fills in remaining duration of event to list
                # for i in range(int(event_duration/15)):
                #     schedule[index + i*6] = module


    driver.back()

    return list(schedule.values())




# %%
def scrape(url:str='https://ethz.ch/staffnet/en/service/rooms-and-buildings/roominfo.html'):
    
    driver.get(url)

    # Driver displays all rooms
    # Button is an anchor element
    #button_display_all = soup.find('a', {'title': 'display all'})
    button_display_all = driver.find_element_by_css_selector('a[title="display all"]')


    #Click anchor element
    button_display_all.click()

    # Find all the 'tr' elements with class 'trSubtext'
    #rows = soup.find_all('tr', {'class':'trSubtext'})
    rows = driver.find_elements_by_css_selector('.trSubtext')

    #Open a CSV file for writing
    with open('room_information.csv', 'w', newline='') as csvfile:
        # Create a CSV writer
        writer = csv.writer(csvfile)

        #Area is the first emelent to be extracted
        header = ['Area', 'Building', 'Floor / Room', 'Room type', 'Seats', 'Seating', 'Floor area', 'Floor shape']
        header.extend(room_schedule_header())

        # Write the header row
        writer.writerow(header)
        

        for i, row in enumerate(rows):
            
            # if i < 45:
            #     continue
                
            # if i > 50:
            #     break

            #print(row)

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'room-overview')))

            row_html = row.get_attribute('innerHTML')

            # Create a BeautifulSoup object from the HTML string
            row_soup = BeautifulSoup(row_html, 'html.parser')

            # Collects the area of the room
            room_information = [row_soup.find_all('td')[1].text.strip()]

            
            # Gets link of room for further information retrieval
            room_details_link = 'https://ethz.ch' + row_soup.find('a', class_='eth-link').get('href')
            
        
            room_details = retrieve_room_details(room_details_link, header[1:8])


            # Add final information to room details
            room_information.extend(room_details)


            # Get room allocation link
            room_schedule_links = driver.find_elements_by_css_selector('.detail-links')
            room_schedule_links_soup = BeautifulSoup(room_schedule_links[0].get_attribute('innerHTML'), 'html.parser')

            for link in room_schedule_links_soup.find_all('a', class_='eth-link'):
                if 'allocation' in link.get('href'):
                    allocation_link = 'https://ethz.ch' + link.get('href')
                else:
                    allocation_link = ''
                
                
            room_schedule = retrieve_room_schedule(allocation_link)
            room_information.extend(room_schedule)

            # Write the information to the CSV file
            writer.writerow(room_information)

            driver.back()

    driver.quit()



