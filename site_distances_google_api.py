"""
This module computes the driving distance between to a cluster using Bing Maps Distance Matrix API.
Required inputs:
    api_key: bing map api key
    cluster_csv_file_path: path to csv file containing all clusters data
    sites_csv_file_path: path to csv file containing sites data
    source_csv_file_path: path to csv file containing source information including, region, cluster, territories and origin coordinates
    outputs_folder: path to folder where the csv outputs for each region/territory will be saved. Ideally it should be empty to avoid conflicts
"""

import csv
import requests
import os
from dotenv import load_dotenv

subscription_key = os.getenv('SUBSCRIPTION_KEY')
api_key = os.getenv('API_KEY')
cluster_csv_file_path = r'C:\CCO\Fuel Allocation Model\data\cluster centroid\clusterCentroid.csv' #change PATH accordingly i.e r'{PATH}'
sites_csv_file_path = r'C:\CCO\Fuel Allocation Model\data\sites\sites.csv' #change PATH accordingly i.e r'{PATH}'
source_csv_file_path = r'C:\CCO\Fuel Allocation Model\V2\data\last_sources.csv' #change PATH accordingly i.e r'{PATH}'
outputs_folder = r'C:\CCO\Fuel Allocation Model\V2\outputs_intersite' #change PATH accordingly i.e r'{PATH}'


def append_to_csv(filename, data, column_names):
    """
    This function generates the output csv files. The files will be saved in the format: [Region_Territory.csv]
    """
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=column_names)
        if not file_exists:
            writer.writeheader()
        for row in data:
            writer.writerow(row)

def read_csv_to_dict_list(file_path):
    """
    This function reads the csv file containing cluster information
    """
    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None

def get_distance(origin: str, dest: str, key: str):
    """
    This functions return one way distance in km
    """
    url = f'https://maps.googleapis.com/maps/api/distancematrix/json?destinations={dest}&origins={origin}&key={key}&mode=driving'
    response = requests.get(url)
    print(response.json()['rows'][0]['elements'][0]['status'])
    if response.json()['rows'][0]['elements'][0]['status'] != 'OK':
        print(f'Error Occured status: {response.json()['rows'][0]['elements'][0]['status']}')
        return response.json()['rows'][0]['elements'][0]['status']
    return response.json()['rows'][0]['elements'][0]['distance']['text'].split()[0]

def Azure_get_distance(origin: str, dest: str, subscription_key: str):
    """
    This functions return one way distance in km
    """
    endpoint = f"https://atlas.microsoft.com/route/matrix/sync/json?subscription-key={subscription_key}&travelMode=car&api-version=1.0&routeType=shortest"
    origin = origin.split(',')
    dest = dest.split(',')
    payload = {
        "origins": {
        "type": "MultiPoint",
        "coordinates": [[ origin[1] , origin[0]]]
        },
        "destinations": {
        "type": "MultiPoint",
        "coordinates": [[ dest[1] , dest[0]]]
        }
    }
    response = requests.post(endpoint, json=payload)
    if response.status_code == 200:
        data = response.json()
        if data['matrix'][0][0]['statusCode'] == 200:
            distance = data['matrix'][0][0]['response']['routeSummary']['lengthInMeters']
            print(f"Distance: {distance * 0.001}")
            return distance * 0.001
        else:
            print(f'Cannot calculate distance Error {data['matrix'][0][0]['statusCode']}')
            return 'NOT_FOUND'
    else:
        print(f"Error: {response.status_code}")
        return 'NOT_FOUND'


clusters = read_csv_to_dict_list(cluster_csv_file_path)
sites = read_csv_to_dict_list(sites_csv_file_path)
sources = read_csv_to_dict_list(source_csv_file_path)

for source in sources:
    print(f'Starting to calculate distances for Region: {source['Region']}, Territory:{ source['Territory']}\n')
    origin = source['Origin_coordinate']
    territory_clusters = []
    filename = outputs_folder + '\\' f'{source['Region']}_{source['Territory']}.csv'
    column_names = ['Region', 'Territory', 'Cluster_of_origin', 'Origin_site_name', 'Origin_site_coordinate', 'Destination_cluster', 'Destination_site_name', 'Destination_site_coordinate', 'One_way_distance', 'Two_way_distance']
    _data = []
    for cluster in clusters:
        if cluster['REGION'].lower() == source['Region'].lower() and cluster['TERRITORY'].lower() == source['Territory'].lower():
            territory_clusters.append(cluster)
    territory_clusters.sort(key=lambda x: x['CLUSTER'])
    for _cluster in territory_clusters:
        for site in sites:
            if _cluster['REGION'].lower() == site['REGION'].lower() and _cluster['TERRITORY'].lower() == site['TERRITORY'].lower() and _cluster['CLUSTER'].lower() == site['CLUSTER'].lower():
                destination = site['LAT'] + ',' + site['LONGITUDE']
                distance = get_distance(origin, destination, api_key)
                #Added this section
                if distance == 'ZERO_RESULTS':
                    distance = Azure_get_distance(origin, destination, subscription_key)
                #Added this section
                print(distance)
                row_data = {'Region': source['Region'], 'Territory': source['Territory'], 'Cluster_of_origin': source['Cluster'], 'Origin_site_name': source['Origin_site'], 'Origin_site_coordinate': source['Origin_coordinate'], 'Destination_cluster': site['CLUSTER'], 'Destination_site_name': site['ATOLL_NAME'], 'Destination_site_coordinate': destination, 'One_way_distance': distance, 'Two_way_distance': distance * 2}
                print(row_data)
                _data.append(row_data)
    append_to_csv(filename, _data, column_names)
    print(f'Finished calculating distances for Region: {source['Region']}, Territory:{ source['Territory']}\n')
            