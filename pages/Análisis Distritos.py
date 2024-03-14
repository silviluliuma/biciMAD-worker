#Imports 
import requests
import json
import os
import pandas as pd
import openrouteservice as ors
from geopy.distance import great_circle
import streamlit as st
from streamlit_js_eval import get_geolocation
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
import seaborn as sns
import pg8000.native
from sqlalchemy import text
import sqlalchemy
from folium.plugins import HeatMap
import folium
from streamlit_folium import folium_static

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
    stations_real_time = stations_real_time.drop(["geofence", 
                                                  "activate", 
                                                  "geometry", 
                                                  "integrator", 
                                                  "reservations_count", 
                                                  "no_available", 
                                                  "tipo_estacionPBSC", 
                                                  "virtualDelete", 
                                                  "virtual_bikes", 
                                                  "virtual_bikes_num", 
                                                  "code_suburb", 
                                                  "geofenced_capacity", 
                                                  "bikesGo"],
                                                axis=1)
    stations_real_time['coordinates'] = list(zip(stations_real_time['longitude'], stations_real_time['latitude']))
    return stations_real_time

stations_real_time = get_stations()

db_params = {
    "dbname": "bicimad_worker",
    "user": st.secrets["google_cloud_user"],
    "password": st.secrets["google_cloud_pass"],
    "host": st.secrets["google_cloud_ip"],
    "port": 5432  # El puerto predeterminado para PostgreSQL es 5432
}

district_dict = {
    '01': 'Centro', '02': 'Arganzuela', '03': 'Retiro', '04': 'Salamanca', '05': 'Chamartín',
    '06': 'Tetuán', '07': 'Chamberí', '08': 'Fuencarral-El Pardo', '09': 'Moncloa-Aravaca',
    '10': 'Latina', '11': 'Carabanchel', '12': 'Usera', '13': 'Puente de Vallecas',
    '14': 'Moratalaz', '15': 'Ciudad Lineal', '16': 'Hortaleza', '17': 'Villaverde',
    '18': 'Villa de Vallecas', '19': 'Vicálvaro', '20': 'San Blas-Canillejas', '21': 'Barajas'
}

def stations_per_district():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    query = """SELECT
    code_district,
    COUNT(*) AS num_stations
    FROM
        estaciones
    GROUP BY
        code_district
    ORDER BY num_stations;"""
    
    cursor.execute(query)
    results = cursor.fetchall()
    results_mapped = [(district_dict[code], num_stations) for code, num_stations in results]
    cursor.close()
    conn.close()
    df = pd.DataFrame(results_mapped, columns=['Distrito', 'Número de estaciones'])

    st.write("Número de Estaciones por Distrito")
    plt.figure(figsize=(10, 6))
    plt.bar(df['Distrito'], df['Número de estaciones'], color='skyblue')
    plt.xlabel("Distrito")
    plt.ylabel("Número de Estaciones")
    plt.title("Número de Estaciones por Distrito")
    st.pyplot(plt)

def get_districts(light, period):
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    query = """
        WITH TotalStations AS (
            SELECT e.code_district, COUNT(e.id) AS total_stations
            FROM disponibilidad d
            INNER JOIN estaciones e ON d.id = e.id
            WHERE TO_TIMESTAMP(d.last_updated, 'YYYY-MM-DD HH24:MI:SS') >= NOW() - INTERVAL '{}'
            GROUP BY e.code_district
        )
        SELECT e.code_district, 
            COUNT(e.id) AS count_light_{}, 
            ts.total_stations,
            COUNT(e.id)::float / ts.total_stations AS ratio_light_{}
        FROM disponibilidad d
        INNER JOIN estaciones e ON d.id = e.id
        INNER JOIN TotalStations ts ON e.code_district = ts.code_district
        WHERE d.light = '{}'
            AND TO_TIMESTAMP(d.last_updated, 'YYYY-MM-DD HH24:MI:SS') >= NOW() - INTERVAL '{}'
        GROUP BY e.code_district, ts.total_stations
        ORDER BY ratio_light_{} DESC;
    """
    if light == 0:
        light_value = '0'
    elif light == 1:
        light_value = '1'
    else:
        light_value = '2'

    if period == 1:
        interval = '24 HOURS'
    elif period == 2:
        interval = '48 HOURS'
    elif period == 7:
        interval = '7 DAYS'
    else:
        interval = '100 DAYS'

    query = query.format(interval, light, light, light_value, interval, light_value)

    cursor.execute(query)
    results = cursor.fetchall()
    results_mapped = [(district_dict[code], num_stations) for code, num_stations in results]
    cursor.close()
    conn.close()
    districts = [result[0] for result in results_mapped]
    light_counts = [result[3] for result in results_mapped]
    plt.figure(figsize=(10, 6))
    plt.bar(districts, light_counts, color='skyblue')
    plt.xlabel('Distrito')
    if light == 0:
        plt.ylabel('Estaciones con falta de bicicletas')
        plt.title('Estaciones con falta de bicicletas según distrito de Madrid')
    elif light == 1:
        plt.ylabel('Estaciones con exceso de bicicletas')
        plt.title('Estaciones con exceso de bicicletas según distrito de Madrid')
    else:
        plt.ylabel('Estaciones con un número óptimo de bicicletas')
        plt.title('Estaciones con un nivel adecuado de bicicletas según distrito de Madrid')
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout()
    st.pyplot(plt) 
    
#MAIN
    
if __name__ == "__main__":
    if st.sidebar.button("Actualizar datos"):
        st.session_state.heatmap = get_stations()
    stations_per_district()
    select_box_query = st.sidebar.selectbox("Seleccione el gráfico que desea visualizar", ["Estaciones con falta de bicicletas", "Estaciones con exceso de bicicletas", "Estaciones con un nivel adecuado de bicicletas"], index=0)
    select_box_period = st.sidebar.selectbox("Seleccione el período a analizar", ["1 Día", "2 Días", "Semana", "Histórico"])
    period_mapping = {
    "1 Día": 1,
    "2 Días": 2,
    "Semana": 7,
    "Histórico": 100
    }
    if select_box_query == "Estaciones con falta de bicicletas":
        light = 0
    elif select_box_query == "Estaciones con exceso de bicicletas":
        light = 1
    else:
        light = 2
    period_hours = period_mapping[select_box_period]
    get_districts(light, period_hours)