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
    lights_df_sum["problematic_stations"] = lights_df_sum[0] +lights_df_sum[1]
    lights_df_sum_sorted = lights_df_sum.sort_values(by="problematic_stations", ascending=False)
    return lights_df_sum_sorted

def get_heatmap():
    plt.figure(figsize=(10, 6))
    sns.heatmap(get_problematic_stations(), cmap='YlGnBu', annot=True, fmt='g', linewidths=.5)
    plt.title('Estaciones problemáticas por distrito')
    plt.xlabel('Luz')
    plt.ylabel('Distrito')
    st.pyplot()

db_params = {
    "dbname": "bicimad_worker",
    "user": st.secrets["google_cloud_user"],
    "password": st.secrets["google_cloud_pass"],
    "host": st.secrets["google_cloud_ip"],
    "port": 5432  # El puerto predeterminado para PostgreSQL es 5432
}

def get_underpopulated_districts():

    # Conexión a mi base de datos
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    # Definir la consulta SQL
    query_ratio_0 = """
        WITH TotalStations AS (
            SELECT e.code_district, COUNT(e.id) AS total_stations
            FROM disponibilidad d
            INNER JOIN estaciones e ON d.id = e.id
            GROUP BY e.code_district
        )

        SELECT e.code_district, 
            COUNT(e.id) AS count_light_0, 
            ts.total_stations,
            COUNT(e.id)::float / ts.total_stations AS ratio_light_0
        FROM disponibilidad d
        INNER JOIN estaciones e ON d.id = e.id
        INNER JOIN TotalStations ts ON e.code_district = ts.code_district
        WHERE d.light = '0'
        GROUP BY e.code_district, ts.total_stations
        ORDER BY e.code_district;
    """

    cursor.execute(query_ratio_0)

   
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    districts = [result[0] for result in results]
    light_counts = [result[1] for result in results]

    plt.figure(figsize=(10, 6))
    plt.bar(districts, light_counts, color='skyblue')
    plt.xlabel('Distrito')
    plt.ylabel('Estaciones con falta de bicicletas')
    plt.title('Ratio de estaciones infrapobladas según distrito de Madrid')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt) 

def get_overpopulated_districts():
    # Conexión a mi base de datos
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    # Definir la consulta SQL
    query_ratio_1 = """
    WITH TotalStations AS (
        SELECT e.code_district, COUNT(e.id) AS total_stations
        FROM disponibilidad d
        INNER JOIN estaciones e ON d.id = e.id
        GROUP BY e.code_district
    )

    SELECT e.code_district, 
        COUNT(e.id) AS count_light_1, 
        ts.total_stations,
        COUNT(e.id)::float / ts.total_stations AS ratio_light_1
    FROM disponibilidad d
    INNER JOIN estaciones e ON d.id = e.id
    INNER JOIN TotalStations ts ON e.code_district = ts.code_district
    WHERE d.light = '1'
    GROUP BY e.code_district, ts.total_stations
    ORDER BY e.code_district;"""

    cursor.execute(query_ratio_1)

   
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    districts = [result[0] for result in results]
    light_counts = [result[1] for result in results]

    plt.figure(figsize=(10, 6))
    plt.bar(districts, light_counts, color='skyblue')
    plt.xlabel('Distrito')
    plt.ylabel('Estaciones con falta de bicicletas')
    plt.title('Cantidad estaciones súperpobladas según distrito de Madrid')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
    st.pyplot(plt) 

#MAIN
    
if __name__ == "__main__":
    if st.sidebar.button("Actualizar datos"):
        st.session_state.heatmap = get_stations()
    st.write("Heatmap de estaciones problemáticas por distrito")
    heatmap = get_heatmap()
    select_box_query = st.sidebar.selectbox("Seleccione el gráfico que desea visualizar", ["Estaciones infrapobladas", "Estaciones sobrepobladas"], index=0)
    if select_box_query == "Estaciones infrapobladas":
        st.write("Distritos con falta de bicicletas en las estaciones")
        get_underpopulated_districts()
    elif select_box_query == "Estaciones sobrepobladas":
        st.write("Distritos con exceso de bicicletas en las estaciones")
        get_overpopulated_districts()