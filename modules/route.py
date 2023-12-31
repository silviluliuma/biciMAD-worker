#Imports 

import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
import folium
import openrouteservice as ors
from geopy.distance import great_circle
from folium.features import DivIcon

def get_token():
    load_dotenv('../.env')
    email = os.environ.get("email")
    password = os.environ.get("password")
    url = "https://openapi.emtmadrid.es/v3/mobilitylabs/user/login/"
    headers = {"email": email, "password" : password}
    response = requests.get(url, headers=headers)
    return response.content

def get_stations():
    load_dotenv('./.env')
    token = os.environ.get("access_token")
    url = "https://openapi.emtmadrid.es/v3/transport/bicimad/stations/"
    headers = {"accessToken" : token}
    response = requests.get(url, headers = headers).json()
    stations_real_time = pd.DataFrame(response["data"])
    stations_real_time[["longitude", "latitude"]] = stations_real_time["geometry"].apply(lambda x: pd.Series(x["coordinates"]))
    stations_real_time = stations_real_time.drop(["geofence", "activate", "geometry", "integrator", "reservations_count", "no_available", "tipo_estacionPBSC", "virtualDelete", "virtual_bikes", "virtual_bikes_num", "code_suburb", "geofenced_capacity", "bikesGo"], axis=1)
    stations_real_time['coordinates'] = list(zip(stations_real_time['longitude'], stations_real_time['latitude']))
    return stations_real_time

def get_district(df, district_number):
    result = df[df["code_district"] == str(district_number)]
    return result

def get_light1(df):
    df_light1 = df[df["light"]==1]
    return df_light1

def get_light0(df):
    df_light0 = df[df["light"]==0]
    return df_light0

def find_nearest_to_coords(df, coords):
    station_coordinates = df['coordinates'].tolist()
    nearest_station = min(station_coordinates, key=lambda coord: great_circle(coord, coords).meters)
    return nearest_station

def create_route(client, start_coords, end_coords):
    return client.directions(
        coordinates=[start_coords, end_coords],
        profile='driving-car',
        format='geojson'
    )

def number_DivIcon(color,number):
    icon = DivIcon(
            icon_size=(150,36),
            icon_anchor=(20,40),
            html = """<span class="fa-stack" style="font-size: 12pt; display: inline-block; position: relative;">
    <span class="fa fa-circle-o fa-stack-2x" style="color: {:s};"></span>
    <strong class="fa-stack-1x" style="line-height: 36px; color: black; position: absolute; width: 100%; text-align: center;">{:02d}</strong>
</span>""".format(color, number))
    return icon

def get_route_map(stations_real_time, number_district):
    load_dotenv('../.env')
    client = ors.Client(key=os.environ.get("openroute_api_key"))
    s = input("Is this your initial route? If not, enter your actual coordinates: ")
    if s == "yes":
        vehicle_start = [-3.6823731969472644, 40.46209827032537]
    else:
        vehicle_start = [eval(s)[1], eval(s)[0]]
    m = folium.Map(location=[vehicle_start[1], vehicle_start[0]], zoom_start=12)
    folium.Marker(location=[vehicle_start[1], vehicle_start[0]], popup='INICIO DE LA RUTA', icon=folium.Icon(color='purple')).add_to(m)
    distrito_low= get_light0(get_district(stations_real_time, number_district)).copy()
    distrito_high= get_light1(get_district(stations_real_time, number_district)).copy()
    distrito_low["visited"] = False
    distrito_high["visited"] = False
    current_coords = vehicle_start
    van = input("Is your van empty or full? ")
    coords_list = [current_coords]
    stop_counter = 1 
    for i in range(100):
        if van == "empty":
            current_coords = coords_list[-1]
            if not distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)].empty:
                nearest_station = find_nearest_to_coords(distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)], current_coords)
                coords_list.append(nearest_station)
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'visited'] = True
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'light'] = 2
                route = create_route(client, coords_list[-2], coords_list[-1])
                van = "full"
                folium.Marker(
                                location=[nearest_station[1], nearest_station[0]],
                                popup = [nearest_station[1], nearest_station[0]],
                                icon=folium.Icon(color='orange',icon_color='orange'),
                            ).add_to(m)
                folium.Marker(location=[nearest_station[1], nearest_station[0]],
                            icon= number_DivIcon("#C55A11", stop_counter)).add_to(m)
                stop_counter += 1
                folium.PolyLine(locations=[coord[::-1] for coord in route['features'][0]['geometry']['coordinates']],
                                color='red').add_to(m)
        elif van == "full":
            current_coords = coords_list[-1]
            if not distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)].empty:
                nearest_station = find_nearest_to_coords(distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)], current_coords)
                coords_list.append(nearest_station)
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'visited'] = True
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'light'] = 2
                route = create_route(client, coords_list[-2], coords_list[-1])
                van = "empty"
                folium.Marker(location=[nearest_station[1], nearest_station[0]],
                              popup = [nearest_station[1], nearest_station[0]],
                            icon=folium.Icon(color='darkgreen', icon_color='green')).add_to(m)
                folium.Marker(location=[nearest_station[1], nearest_station[0]],
                              icon = number_DivIcon("#12A14B", stop_counter)).add_to(m)
                legend_html = '''
                <div style="position: fixed; 
                bottom: 40px; left: 70px; width: 280px; height: 250 px; 
                border: 2px solid grey; z-index: 9999; font-size: 14px;
                background-color: white; padding: 10px; margin-left: 20px;">
                    <b>Instrucciones de reparto biciMAD</b> <br>
                    1. Por favor, recoja las bicicletas en las estaciones naranjas. &nbsp; <i class="fa fa-map-marker" style="color:orange"></i><br>
                    2. Descárguelas en las estaciones verdes. &nbsp; <i class="fa fa-map-marker" style="color:green"></i><br>
                    3. Si todavía queda tiempo en su jornada laboral, reinicie la aplicación en la última estación e introduzca sus nuevas coordenadas.<br>
                    4. Conduzca con cuidado y que tenga un buen turno. &nbsp; <i class="fa fa-smile-o" style="color:blue"></i><br>
                    En caso de incidente, no olvide contactar con su gerente. Buen trabajo.
                </div>
                        '''
                m.get_root().html.add_child(folium.Element(legend_html))
                stop_counter += 1
                folium.PolyLine(locations=[coord[::-1] for coord in route['features'][0]['geometry']['coordinates']],
                                color='red').add_to(m)
    vehicle_start = [-3.6823731969472644, 40.46209827032537]
    final_route = create_route(client, coords_list[-1], vehicle_start)
    folium.Marker(location=[vehicle_start[1], vehicle_start[0]], popup='CENTRAL EMT', icon=folium.Icon(color='purple')).add_to(m)
    folium.PolyLine(locations=[coord[::-1] for coord in final_route['features'][0]['geometry']['coordinates']],
                                color='red').add_to(m)

    return m   