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

st.set_option('deprecation.showPyplotGlobalUse', False)

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

stations_real_time = get_stations()

def get_problematic_stations():
    lights_df_sum = stations_real_time.pivot_table(index='code_district', columns='light', aggfunc='size', fill_value=0)
    lights_df_sum = lights_df_sum.drop([2, 3], axis=1)
    lights_df_sum["Total"] = lights_df_sum[0] +lights_df_sum[1]
    lights_df_sum_sorted = lights_df_sum.sort_values(by="problematic_stations", ascending=False)
    return lights_df_sum_sorted

def get_heatmap():
    plt.figure(figsize=(10, 6))
    custom_palette = sns.light_palette("orange", as_cmap=True)
    sns.heatmap(get_problematic_stations(), cmap=custom_palette, annot=True, fmt='g', linewidths=.5)
    plt.title('Estaciones problemáticas por distrito')
    plt.xlabel('Luz')
    plt.ylabel('Distrito')
    st.pyplot()

if __name__ == "__main__":
    if st.sidebar.button("Actualizar datos"):
        st.session_state.heatmap = get_stations()
    heatmap = get_heatmap()