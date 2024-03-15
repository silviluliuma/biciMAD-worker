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

db_params = {
    "dbname": "bicimad_worker",
    "user": st.secrets["google_cloud_user"],
    "password": st.secrets["google_cloud_pass"],
    "host": st.secrets["google_cloud_ip"],
    "port": 5432  # El puerto predeterminado para PostgreSQL es 5432
}

def get_dictionary_stations():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    query = """
    SELECT DISTINCT address, id
    FROM estaciones;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    address_id_dict = {}
    for result in results:
        address_id_dict[result[0]] = result[1]
    cursor.close()
    conn.close()
    return address_id_dict

address_id_dict = get_dictionary_stations()

def analysis_station(address): #Análisis de las luces de esa estación, sus reservas y su funcionamiento
    address_id_dict = get_dictionary_stations()
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    station_id = address_id_dict[address]
    query = """
        SELECT light, 
        no_available,
        reservations_count
        FROM disponibilidad
        WHERE id = %s;
    """
    cursor.execute(query, (station_id,))
    light_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    no_available_count = 0
    reservations_count_ = 0
    results = cursor.fetchall()
    for result in results:
        light = result[0]
        no_available = result[1]
        reservations_count = result[2]
        light_counts[light] += 1
        if no_available:
            no_available_count += 1
        if reservations_count > 0:
            reservations_count_ += 1
    cursor.close()
    conn.close()

    data = {
        "Veces con falta de bicicletas": [light_counts[0]],
        "Veces con exceso de bicicletas": [light_counts[1]],
        "Veces con un número adecuado de bicicletas": [light_counts[2]],
        "Veces con un número desconocido de bicicletas": [light_counts[3]],
        "Veces no disponible": [no_available_count],
        "Veces con reservas": [reservations_count_]
    }
    df = pd.DataFrame(data)
    return df

def no_available():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    query = """
    SELECT 
        e.address AS estación, 
        COUNT(e.address) AS veces_registrada,
        SUM(d.no_available) AS veces_no_disponible, 
        e.code_district AS distrito
    FROM disponibilidad d
    JOIN estaciones e ON d.id = e.id 
    WHERE d.no_available = 1
    GROUP BY e.address, e.code_district"""
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    df = pd.DataFrame(results, columns=['Estación', 'Veces registrada', 'Veces No Disponible', 'Distrito'])
    return df

def reservation_count():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    query = """
    SELECT DISTINCT(reservations_count) AS reservas
    FROM disponibilidad
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    df = pd.DataFrame(results, columns=['Veces que se ha realizado una reserva de bicicletas'])
    return df

# MAIN

if __name__ == "__main__":
    selectbox_station = st.sidebar.selectbox("Selecciona una estación", list(address_id_dict.keys()))
    st.title("Datos sobre la estación seleccionada:")
    st.write(analysis_station(selectbox_station))
    st.title("Posibles problemas detectados gracias al análisis de los datos:")
    st.write("Estaciones no disponibles:")
    st.write(no_available())
    st.write("Los usuarios no reservan bicicletas (o, si lo hacen, no se está recogiendo adecuadamente)")
    st.write(reservation_count())