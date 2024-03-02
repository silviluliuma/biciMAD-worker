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
from streamlit_js_eval import get_geolocation
import matplotlib.pyplot as plt
import seaborn as sns

#Funciones

def get_token(): #Coger el token de la api de bicimad
    email = st.secrets["email"]
    password = st.secrets["password"]
    st.write(email, password)
    url = "https://openapi.emtmadrid.es/v3/mobilitylabs/user/login/"
    headers = {"email": email, "password" : password}
    response = requests.get(url, headers=headers)
    return response.content

def get_stations(): #Usar el token para acceder a la información en tiempo real sobre las estaciones
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

def get_district(df, district_number): #Selecciona únicamente las estaciones del distrito seleccionado
    result = df[df["code_district"] == str(district_number)]
    return result

def get_light1(df): #Selecciona las estaciones con nivel de ocupación alto (demasiadas bicicletas)
    df_light1 = df[df["light"]==1]
    return df_light1

def get_light0(df): #Selecciona las estaciones con déficit de bicicletas (nivel de ocupación bajo)
    df_light0 = df[df["light"]==0]
    return df_light0

def find_nearest_to_coords(df, coords): #Calcula la estación más cercana a la actual (será de ocupación alta si la actual es de ocupación baja o viceversa)
    station_coordinates = df['coordinates'].tolist()
    nearest_station = min(station_coordinates, key=lambda coord: great_circle(coord, coords).meters)
    return nearest_station

def create_route(client, start_coords, end_coords): #Crea una ruta entre las estaciones con openrouteservice
    return client.directions(
        coordinates=[start_coords, end_coords],
        profile='driving-car',
        format='geojson'
    )

def number_DivIcon(color,number): #Crea iconos numerados para las paradas que tiene que realizar el trabajador
    icon = DivIcon(
            icon_size=(150,36),
            icon_anchor=(20,40),
            html = """<span class="fa-stack" style="font-size: 12pt; display: inline-block; position: relative;">
    <span class="fa fa-circle-o fa-stack-2x" style="color: {:s};"></span>
    <strong class="fa-stack-1x" style="line-height: 36px; color: black; position: absolute; width: 100%; text-align: center;">{:02d}</strong>
</span>""".format(color, number))
    return icon

loc = get_geolocation()

def get_user_loc(loc):
    if loc is None:
        user_latitude = 40.46209827032537
        user_longitude = -3.6823731969472644
        print("Can't access user location, starting route from default location (EMT)")
    else:
        user_latitude = loc["coords"].get("latitude")
        user_longitude = loc["coords"].get("longitude")
    return [user_latitude, user_longitude]

if "client" not in st.session_state:
    st.session_state.client = ors.Client(key=st.secrets["openroute_api_key"])

def get_route_map_google(client, stations_real_time, number_district_sidebar, van_sidebar): #Hace display de la ruta del trabajador tanto en google maps como en un mapa folium
    vehicle_start = get_user_loc(loc)[1], get_user_loc(loc)[0]
    m = folium.Map(location=[vehicle_start[1], vehicle_start[0]], zoom_start=12)
    folium.Marker(location=[vehicle_start[1], vehicle_start[0]], popup='INICIO DE LA RUTA', icon=folium.Icon(color='purple')).add_to(m)
    
    distrito_low = get_light0(get_district(stations_real_time, number_district_sidebar)).copy()
    distrito_high = get_light1(get_district(stations_real_time, number_district_sidebar)).copy()
    distrito_low["visited"] = False
    distrito_high["visited"] = False
    
    current_coords = vehicle_start
    
    coords_list = [current_coords]
    stop_counter = 1 
    
    for i in range(30): #En el distrito 01 hay más estaciones pero el límite de la API es 40 por minuto. Para el resto de las estaciones sobra con 40
        if van_sidebar == "Empty":
            current_coords = coords_list[-1]
            if not distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)].empty:
                nearest_station = find_nearest_to_coords(distrito_high.loc[~distrito_high['visited'] & (distrito_high['light'] == 1)], current_coords)
                coords_list.append(nearest_station)
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'visited'] = True
                distrito_high.loc[distrito_high['coordinates'] == nearest_station, 'light'] = 2
                route = create_route(client, coords_list[-2], coords_list[-1])
                folium.Marker(
                                location=[nearest_station[1], nearest_station[0]],
                                popup = [nearest_station[1], nearest_station[0]],
                                icon=folium.Icon(color='orange',icon_color='orange'),
                            ).add_to(m)
                folium.Marker(location=[nearest_station[1], nearest_station[0]],
                            icon= number_DivIcon("#C55A11", stop_counter)).add_to(m)
    
                folium.PolyLine(locations=[coord[::-1] for coord in route['features'][0]['geometry']['coordinates']],
                                color='red').add_to(m)
                van_sidebar = "Full"
                stop_counter += 1
        elif van_sidebar == "Full":
            current_coords = coords_list[-1]
            if not distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)].empty:
                nearest_station = find_nearest_to_coords(distrito_low.loc[~distrito_low['visited'] & (distrito_low['light'] == 0)], current_coords)
                coords_list.append(nearest_station)
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'visited'] = True
                distrito_low.loc[distrito_low['coordinates'] == nearest_station, 'light'] = 2
                route = create_route(client, coords_list[-2], coords_list[-1])
                van_sidebar = "Empty"
                folium.Marker(location=[nearest_station[1], nearest_station[0]],
                              popup = [nearest_station[1], nearest_station[0]],
                            icon=folium.Icon(color='darkgreen', icon_color='green')).add_to(m)
                folium.Marker(location=[nearest_station[1], nearest_station[0]],
                              icon = number_DivIcon("#12A14B", stop_counter)).add_to(m)    
                stop_counter += 1
                folium.PolyLine(locations=[coord[::-1] for coord in route['features'][0]['geometry']['coordinates']],
                                color='red').add_to(m)
    
    folium.Marker(location=[vehicle_start[1], vehicle_start[0]], popup='UBICACIÓN ACTUAL', icon=folium.Icon(color='purple')).add_to(m)
    waypoints_list = [f"{coord[1]},{coord[0]}" if isinstance(coord, tuple) else f"{coord[1]},{coord[0]}" for coord in coords_list[1:-1]]
    waypoints = "|".join(waypoints_list)
    destination_coords = f"{coords_list[-1][1]},{coords_list[-1][0]}"
    route_url = f"https://www.google.com/maps/dir/?api=1&origin={get_user_loc(loc)[0]},{get_user_loc(loc)[1]}&destination={destination_coords}&waypoints={waypoints}"
    st.markdown(f"[Ver ruta en Google Maps]({route_url})")
    return m

if "stations_real_time" not in st.session_state:
    st.session_state.stations_real_time = get_stations()
if st.sidebar.button("Actualizar datos"):
    st.session_state.stations_real_time = get_stations()

stations_streamlit = st.session_state.stations_real_time[(st.session_state.stations_real_time["light"] == 1) | (st.session_state.stations_real_time["light"] == 0)] #Selecciona sólo las estaciones que nos interesan (las que tienen déficit o superávit) para mostrarlas en streamlit

def invert_coordinates(coordinates): #Invierte las coordenadas necesarias (openrouteservice y google maps toman en diferente posición la latitud y la longitud)
    lon, lat = coordinates
    return f"[{lat}, {lon}]"
#stations_streamlit["coordinates"] = stations_streamlit["coordinates"].apply(invert_coordinates)
stations_streamlit.loc[:, "coordinates"] = stations_streamlit["coordinates"].apply(invert_coordinates)


def get_problematic_stations():
    lights_df_sum = st.session_state.stations_real_time.pivot_table(index='code_district', columns='light', aggfunc='size', fill_value=0)
    lights_df_sum = lights_df_sum.drop([2, 3], axis=1)
    lights_df_sum["problematic_stations"] = lights_df_sum[0] +lights_df_sum[1]
    lights_df_sum_sorted = lights_df_sum.sort_values(by="problematic_stations", ascending=False)
    return lights_df_sum_sorted

if __name__ == "__main__":
    st.sidebar.title("BiciMAD-worker")
    st.title("Esta es la ruta recomendada para su distrito:")
    number_district_sidebar = st.sidebar.selectbox("Seleccione uno de los distritos con necesidad de redistribución", get_problematic_stations().index.tolist(), index=0)
    van_sidebar = st.sidebar.selectbox("¿Su furgoneta está vacía ('Empty') o llena ('Full')?", ["Empty", "Full"], index=0)
    route_map = get_route_map_google(st.session_state.client, st.session_state.stations_real_time, number_district_sidebar, van_sidebar)
    st_data = folium_static(route_map)
    