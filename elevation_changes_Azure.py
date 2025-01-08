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
import polyline
import pandas as pd

subscription_key = os.getenv('SUBSCRIPTION_KEY')
api_key = os.getenv('API_KEY')
bing_api = os.getenv('BING_API')
cluster_csv_file_path = r'C:\CCO\Fuel Allocation Model\data\cluster centroid\clusterCentroid.csv' #change PATH accordingly i.e r'{PATH}'
sites_csv_file_path = r'C:\CCO\Fuel Allocation Model\data\sites\sites.csv' #change PATH accordingly i.e r'{PATH}'
source_csv_file_path = r'C:\CCO\Fuel Allocation Model\V2\data\last_sources.csv' #change PATH accordingly i.e r'{PATH}'
outputs_folder = r'C:\CCO\Fuel Allocation Model\V2\intersite-centroid-elavation-outputs' #change PATH accordingly i.e r'{PATH}'


#Added this section

def get_route_Google(origin, destination, api_key):
    directions_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={api_key}&mode=driving"
    response = requests.get(directions_url, timeout=60)
    directions_data = response.json()
    
    if directions_data['status'] == 'OK':
        route = directions_data['routes'][0]['overview_polyline']['points']
        return route
    else:
        return None

def get_elevation_data_Google(api_key, path):
    elevation_url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={'|'.join([f'{lat},{lng}' for lat, lng in path])}&key={api_key}"
    response = requests.get(elevation_url, timeout=60)
    try:
        elevation_data = response.json()
        return elevation_data
    except Exception as e:
        return 'ZERO_RESULTS'

def decode_polyline(polyline_str):
    return polyline.decode(polyline_str)

def calculate_elevation_changes(elevations):
    elevation_changes = [j - i for i, j in zip(elevations[:-1], elevations[1:])]
    return elevation_changes

def calculate_aggregate_elevation_change(elevation_changes):
    return sum(change for change in elevation_changes)

def reduce_points(points, max_points=400):
    total_points = len(points)
    if total_points <= max_points:
        return points
    interval = total_points / max_points
    reduced_points = [points[int(i * interval)] for i in range(max_points)]
    return reduced_points

def get_route_Azure(subscription_key, origin, destination):
    route_url = f"https://atlas.microsoft.com/route/directions/json?subscription-key={subscription_key}&api-version=1.0&query={origin}:{destination}&mode=driving"
    response = requests.get(route_url)
    route_data = response.json()
    
    if response.status_code == 200 and route_data.get('routes'):
        points = route_data['routes'][0]['legs'][0]['points']
        route = [(point['latitude'], point['longitude']) for point in points]
        if len(route) > 400:
            route = reduce_points(route)
        return route
    else:
        return None

def get_route_bing_maps(bing_api, origin, destination):
    url = f'http://dev.virtualearth.net/REST/V1/Routes/Driving?o=json&wp.0={origin}&wp.1={destination}&avoid=minimizeTolls&key={bing_api}'
    response = requests.get(url)
    route_data = response.json()

    if response.status_code == 200 and route_data.get('resourceSets'):
        resources = route_data['resourceSets'][0].get('resources')
        if resources:
            points = resources[0]['routeLegs'][0]['itineraryItems']
            route = [(point['maneuverPoint']['coordinates'][0], point['maneuverPoint']['coordinates'][1]) for point in points]
            if len(route) > 400:
                route = reduce_points(route)
            return route
    else:
        return None

def get_elevation_data_Azure(bing_api, path):
    points = ','.join([f"{lat},{lng}" for lat, lng in path])
    elevation_url = f"http://dev.virtualearth.net/REST/v1/Elevation/List?points={points}&key={bing_api}"
    response = requests.get(elevation_url)
    try:
        elevation_data = response.json()
        if elevation_data.get('statusCode') == 200:
            return elevation_data
        else:
            return 'ZERO_RESULTS'
    except Exceptions as e:
        return 'ZERO_RESULTS'

def elevation_change_Azure():
    route_coordinates = get_route_bing_maps(bing_api, origin, destination)
    if route_coordinates:
        elevation_data = get_elevation_data_Azure(bing_api, route_coordinates)
        if 'resourceSets' in elevation_data and len(elevation_data['resourceSets'][0]['resources'][0]['elevations']) > 0:
            elevations = elevation_data['resourceSets'][0]['resources'][0]['elevations']
            elevation_changes = calculate_elevation_changes(elevations)  
            df = pd.DataFrame(route_coordinates, columns=['Latitude', 'Longitude'])
            df['Elevation'] = elevations
            df['Elevation_Change'] = [0] + elevation_changes
            aggregate_elevation_change = calculate_aggregate_elevation_change(elevation_changes)
            return aggregate_elevation_change
        else:
            return 'ZERO_RESULTS'
    else:
        return 'ZERO_RESULTS'

def elevation_change_Google():
    route_polyline = get_route_Google(origin, destination, api_key)
    if route_polyline:
        route_coordinates = decode_polyline(route_polyline)
        elevation_data = get_elevation_data_Google(api_key, route_coordinates)
        elevations = [result['elevation'] for result in elevation_data['results']]
        if len(elevations) == 0:
            return 'EMPTY_LIST'
        elevation_changes = calculate_elevation_changes(elevations)
        df = pd.DataFrame(route_coordinates, columns=['Latitude', 'Longitude'])
        df['Elevation'] = elevations
        df['Elevation_Change'] = [0] + elevation_changes
        aggregate_elevation_change = calculate_aggregate_elevation_change(elevation_changes)
        return aggregate_elevation_change
    else:
        return 'ZERO_RESULTS'

#Added this section


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
    print(f'Starting to calculate elevations for Region: {source['Region']}, Territory:{ source['Territory']}\n')
    origin = source['Origin_coordinate']
    territory_clusters = []
    filename = outputs_folder + '\\' f'{source['Region']}_{source['Territory']}.csv'
    column_names = ['Region', 'Territory', 'Cluster_of_origin', 'Origin_site_name', 'Origin_site_coordinate', 'Destination_cluster', 'Destination_site_name', 'Destination_site_coordinate', 'Elevation_change']
    _data = []
    for cluster in clusters:
        if cluster['REGION'].lower() == source['Region'].lower() and cluster['TERRITORY'].lower() == source['Territory'].lower():
            territory_clusters.append(cluster)
    territory_clusters.sort(key=lambda x: x['CLUSTER'])
    for _cluster in territory_clusters:
        for site in sites:
            if _cluster['REGION'].lower() == site['REGION'].lower() and _cluster['TERRITORY'].lower() == site['TERRITORY'].lower() and _cluster['CLUSTER'].lower() == site['CLUSTER'].lower():
                destination = site['LAT'] + ',' + site['LONGITUDE']
                #elevation = elevation_change_Google()
                elevation = elevation_change_Azure()
                #Added this section
                #if elevation == 'ZERO_RESULTS' or elevation == 'EMPTY_LIST':
                    #elevation = elevation_change_Azure()
                #Added this section
                print(elevation)
                row_data = {'Region': source['Region'], 'Territory': source['Territory'], 'Cluster_of_origin': source['Cluster'], 'Origin_site_name': source['Origin_site'], 'Origin_site_coordinate': source['Origin_coordinate'], 'Destination_cluster': site['CLUSTER'], 'Destination_site_name': site['ATOLL_NAME'], 'Destination_site_coordinate': destination, 'Elevation_change': elevation}
                print(row_data)
                _data.append(row_data)
    append_to_csv(filename, _data, column_names)
    print(f'Finished calculating elevations for Region: {source['Region']}, Territory:{ source['Territory']}\n')
            