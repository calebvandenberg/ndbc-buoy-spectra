#!/usr/bin/python3

# import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup as bs
import csv
from decimal import Decimal
# from os import path

# loop = asyncio.get_event_loop()
async def get_data(url):
    session = ClientSession()
    async with session.get(url) as resp:
        data = await resp.text()
    session.close()
    return data


async def find_tag_text(tag='a', url='http://www.ndbc.noaa.gov/data/5day2', find_text='.spectral'):
    html = await get_data(url)
    soup = bs(html, "html.parser")
    links = soup.find_all(tag)
    found_texts = []
    for i in links:
        if find_text in i.text:
            found_texts.append(i.text.split('_')[0])
    return found_texts

async def metadata():
    fieldnames = "STATION_ID | OWNER | TTYPE | HULL | NAME | PAYLOAD | LOCATION | TIMEZONE | FORECAST | NOTE".split(' | ')
    csv.register_dialect('ndbc', delimiter='|', quoting=csv.QUOTE_NONE)
    # if local:
    #     csv_path = '/media/removable/UBOAT/scripts/async'
    #     filename = 'station_table.txt'
    # with open(path.join(csv_path, filename)) as f:
    found_texts = await find_tag_text()
    url = "http://www.ndbc.noaa.gov/data/stations/station_table.txt"
    f = await get_data(url)
    csvreader = csv.DictReader(f.splitlines(), fieldnames=fieldnames, dialect='ndbc')
    buoy_data = []
    timezone = None
    def test_csv(reader=csvreader):
        i = 0
        for r in reader:
            if i < 2:
                i += 1
                continue
            if r['STATION_ID']:
                print(r['STATION_ID'])

    for r in csvreader:
        if r['STATION_ID'] in found_texts:
            location = r['LOCATION'].split(' ')
            latitude = Decimal(location[0])
            longitude = Decimal(location[2])
            if location[1] is 'S':
                latitude *= -1
            if location[3] is 'W':
                longitude *= -1
            if r['TIMEZONE']:
                if r['TIMEZONE'] is 'E':
                    timezone = 'America/New_York'
                elif r['TIMEZONE'] is 'C':
                    timezone = 'America/Chicago'
                elif r['TIMEZONE'] is 'P':
                    timezone = 'America/Los_Angeles'
                elif r['TIMEZONE'] is 'H':
                    timezone = 'Pacific/Honolulu'
                elif r['TIMEZONE'] is 'A':
                    timezone = 'America/Anchorage'
                else:
                    timezone = 'GMT'  # defaults to GMT
            buoy_data.append({
                'id': r['STATION_ID'],
                'name': r['NAME'].title(),
                'latitude': latitude,
                'longitude': longitude,
                'timezone': timezone
                })
    return buoy_data



