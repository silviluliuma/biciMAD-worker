#Imports 
import requests
import json
import os
import pandas as pd
import folium
import openrouteservice as ors
from geopy.distance import great_circle
import streamlit as st
from streamlit_folium import folium_static
from folium.features import DivIcon
import webbrowser
from dotenv import load_dotenv

def get_token():
    email = st.secrets["email"]
    password = st.secrets["password"]
    st.write(email, password)
    url = "https://openapi.emtmadrid.es/v3/mobilitylabs/user/login/"
    headers = {"email": email, "password" : password}
    response = requests.get(url, headers=headers)
    return response.content

def get_stations():
    #token = os.environ.get("access_token")
    token = st.secrets["access_token"]
    url = "https://openapi.emtmadrid.es/v3/transport/bicimad/stations/"
    headers = {"accessToken" : token}
    response = requests.get(url, headers = headers)
    json_data = response.json()
    stations_real_time = pd.DataFrame(json_data["data"])
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

def get_route_map(stations_real_time, number_district_sidebar, s_sidebar, van_sidebar):
    client = ors.Client(key=st.secrets["openroute_api_key"])
    if s_sidebar == "Yes":
        vehicle_start = [-3.6823731969472644, 40.46209827032537]
    else:
        vehicle_start = [eval(s_sidebar)[1], eval(s_sidebar)[0]]
    
    distrito_low = get_light0(get_district(stations_real_time, number_district_sidebar)).copy()
    distrito_high = get_light1(get_district(stations_real_time, number_district_sidebar)).copy()
    distrito_low["visited"] = False
    distrito_high["visited"] = False
    current_coords = vehicle_start
    coords_list = [current_coords]
    stop_counter = 1 
    
    for i in range(100):
        if van_sidebar == "Empty":
            current_coords = coords_list[-1]
            if not distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)].empty:
                nearest_station = find_nearest_to_coords(distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)], current_coords)
                coords_list.append(nearest_station)
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'visited'] = True
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'light'] = 2
                van_sidebar = "Full"
                stop_counter += 1
        elif van_sidebar == "Full":
            current_coords = coords_list[-1]
            if not distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)].empty:
                nearest_station = find_nearest_to_coords(distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)], current_coords)
                coords_list.append(nearest_station)
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'visited'] = True
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'light'] = 2
                van_sidebar = "Empty"
                stop_counter += 1
    
    vehicle_start = [-3.6823731969472644, 40.46209827032537]
    final_route = create_route(client, coords_list[-1], vehicle_start)
    waypoints = "|".join([f"{coord[1]},{coord[0]}" for coord in coords_list])
    route_url = f"https://www.google.com/maps/dir/?api=1&origin={vehicle_start[1]},{vehicle_start[0]}&destination={coords_list[-1]}&waypoints={waypoints}"
    st.markdown(f"[Ver ruta en Google Maps]({route_url})")

def get_route_map_google(stations_real_time, number_district_sidebar, s_sidebar, van_sidebar):
    client = ors.Client(key=st.secrets["openroute_api_key"])
    if s_sidebar == "Yes":
        vehicle_start = [-3.6823731969472644, 40.46209827032537]
    else:
        vehicle_start = [eval(s_sidebar)[1], eval(s_sidebar)[0]]
    
    distrito_low = get_light0(get_district(stations_real_time, number_district_sidebar)).copy()
    distrito_high = get_light1(get_district(stations_real_time, number_district_sidebar)).copy()
    distrito_low["visited"] = False
    distrito_high["visited"] = False
    current_coords = vehicle_start
    coords_list = [current_coords]
    stop_counter = 1 
    
    for i in range(100):
        if van_sidebar == "Empty":
            current_coords = coords_list[-1]
            if not distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)].empty:
                nearest_station = find_nearest_to_coords(distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)], current_coords)
                coords_list.append(nearest_station)
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'visited'] = True
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'light'] = 2
                van_sidebar = "Full"
                stop_counter += 1
        elif van_sidebar == "Full":
            current_coords = coords_list[-1]
            if not distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)].empty:
                nearest_station = find_nearest_to_coords(distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)], current_coords)
                coords_list.append(nearest_station)
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'visited'] = True
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'light'] = 2
                van_sidebar = "Empty"
                stop_counter += 1
    
    vehicle_start = [-3.6823731969472644, 40.46209827032537]
    final_route = create_route(client, coords_list[-1], vehicle_start)
    waypoints_list = [f"{coord[1]},{coord[0]}" if isinstance(coord, tuple) else f"{coord[1]},{coord[0]}" for coord in coords_list[1:-1]]
    waypoints = "|".join(waypoints_list)
    destination_coords = f"{coords_list[-1][1]},{coords_list[-1][0]}"
    route_url = f"https://www.google.com/maps/dir/?api=1&origin={vehicle_start[1]},{vehicle_start[0]}&destination={destination_coords}&waypoints={waypoints}"
    st.markdown(f"[Ver ruta en Google Maps]({route_url})")

stations_real_time = get_stations()

stations_streamlit = stations_real_time[(stations_real_time["light"] == 1) | (stations_real_time["light"] == 0)]

def invert_coordinates(coordinates):
    lon, lat = coordinates
    return f"[{lat}, {lon}]"
stations_streamlit["coordinates"] = stations_streamlit["coordinates"].apply(invert_coordinates)

if __name__ == "__main__":
    st.sidebar.title("BiciMAD-worker")
    st.title("Esta es la ruta recomendada para su distrito:")
    number_district_sidebar = st.sidebar.selectbox("¿A qué distrito se le ha asignado hoy?", ["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21"], index=0)
    s_sidebar = st.sidebar.text_input('Si esta es su ruta inicial, introduzca "Yes". En caso contrario, introduzca sus coordenadas entre corchetes ([])', 'Yes')
    van_sidebar = st.sidebar.selectbox("¿Su furgoneta está vacía ('Empty') o llena ('Full')?", ["Empty", "Full"], index=0)
    route_map = get_route_map_google(stations_real_time, number_district_sidebar, s_sidebar, van_sidebar)
    st.text("""Instrucciones de reparto BiciMAD-worker: 
    1. Por favor, recoja las bicicletas en las estaciones naranjas.
    2. Descárguelas en las estaciones verdes.
    3. Si todavía queda tiempo en su jornada laboral, reinicie la aplicación e introduzca sus nuevas coordenadas.
    4. Conduzca con cuidado y que tenga un buen turno.""")
    st.write(get_district(stations_streamlit, number_district_sidebar)[["address", "coordinates"]])