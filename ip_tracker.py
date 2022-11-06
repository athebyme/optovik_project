import math
import random

from pyfiglet import Figlet
import requests
import folium


def get_info_by_ip(ip='127.0.0.1'):
    try:
        response = requests.get(url=f'http://ip-api.com/json/{ip}').json()
        data = {
            '[IP]': response.get('query'),
            '[Int prov]': response.get('isp'),
            '[Org]': response.get('org'),
            '[Region]': [response.get('country'),response.get('city')],
            '[Country Code]': response.get('countryCode'),
            '[TimeZone]': response.get('timezone'),
            '[Zip]': response.get('zip'),
            '[Lon]': response.get('lon'),
            '[Lat]': response.get('lat')
        }
        for k, v in data.items():
            print(f'{k}: {v}')

        area = folium.Map(location=[response.get('lat'),response.get('lon')])
        area.save(f'{response.get("query")}_{response.get("city")}.html')
    except requests.exceptions.ConnectionError:
        print('[!] Please check your connection')
def main():
    preview_text = Figlet(font = 'slant')
    print(preview_text.renderText('IP INFO'))
    ip = input('Please enter target IP: ')
    get_info_by_ip(ip)
import re
if __name__ == '__main__':
    main()