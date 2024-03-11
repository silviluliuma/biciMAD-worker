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
        SELECT light, no_available, reservations_count
        FROM disponibilidad
        WHERE id = %s;
    """
    cursor.execute(query, (station_id,))
    light_counts = {0: 0, 1: 0, 2: 0}
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
    st.write(f"Estación: {address} (ID: {station_id})")
    st.write("Veces con luz 0 (falta de bicicletas):", light_counts[0])
    st.write("Veces con luz 1 (exceso de bicicletas):", light_counts[1])
    st.write("Veces con luz 2 (número correcto de bicicletas):", light_counts[2])
    st.write("Veces no disponible:", no_available_count)
    st.write("Veces con reservas:", reservations_count_)

def data_no_change():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    query ="""
    SELECT 
    CASE 
        WHEN COUNT(DISTINCT activate) = 1 THEN 'activate'
        ELSE NULL
    END AS activate,
    CASE 
        WHEN COUNT(DISTINCT dock_bikes) = 1 THEN 'dock_bikes'
        ELSE NULL
    END AS dock_bikes,
    CASE 
        WHEN COUNT(DISTINCT free_bases) = 1 THEN 'free_bases'
        ELSE NULL
    END AS free_bases,
    CASE 
        WHEN COUNT(DISTINCT id) = 1 THEN 'id'
        ELSE NULL
    END AS id,
    CASE 
        WHEN COUNT(DISTINCT light) = 1 THEN 'light'
        ELSE NULL
    END AS light,
    CASE 
        WHEN COUNT(DISTINCT no_available) = 1 THEN 'no_available'
        ELSE NULL
    END AS no_available,
    CASE 
        WHEN COUNT(DISTINCT reservations_count) = 1 THEN 'reservations_count'
        ELSE NULL
    END AS reservations_count,
    CASE 
        WHEN COUNT(DISTINCT last_updated) = 1 THEN 'last_updated'
        ELSE NULL
    END AS last_updated
    FROM 
        disponibilidad;"""
    
    cursor.execute(query)
    results = cursor.fetchall()

    columns_unchanged = []
    for column in results:
        if column is not None:
            columns_unchanged.append(column)
    if columns_unchanged:
        columns_str = ', '.join(columns_unchanged)
        print(f"Las columnas {columns_str} no han cambiado en ningún momento.")
    else:
        print("No hay columnas que no hayan cambiado en ningún momento.")

# MAIN

if __name__ == "__main__":
    selectbox_station = st.sidebar.selectbox("Selecciona una estación", list(address_id_dict.keys()))
    analysis_station(selectbox_station)
    data_no_change()