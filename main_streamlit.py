#Imports 
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
import folium
import openrouteservice as ors
from geopy.distance import great_circle
from modules import route_streamlit
#from modules import argparse
import streamlit as st
from streamlit_folium import folium_static
from folium.features import DivIcon

stations_real_time = route_streamlit.get_stations()

if __name__ == "__main__":
    st.sidebar.title("BiciMAD-worker")
    st.title("Esta es la ruta recomendada para su distrito:")
    number_district_sidebar = st.sidebar.selectbox("¿A qué distrito se le ha asignado hoy?", ["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21"], index=0)
    s_sidebar = st.sidebar.text_input('Si esta es su ruta inicial, introduzca "Yes". En caso contrario, introduzca sus coordenadas entre corchetes ([])', 'Yes')
    van_sidebar = st.sidebar.selectbox("¿Su furgoneta está vacía o llena?", ["Empty", "Full"], index=0)
    route_map = route_streamlit.get_route_map(stations_real_time, number_district_sidebar, s_sidebar, van_sidebar)
    st_data = folium_static(route_map)
    st.text("""Instrucciones de reparto BiciMAD-worker: 
    1. Por favor, recoja las bicicletas en las estaciones naranjas.
    2. Descárguelas en las estaciones verdes.
    3. Si todavía queda tiempo en su jornada laboral, reinicie la aplicación e introduzca sus nuevas coordenadas.
    4. Conduzca con cuidado y que tenga un buen turno.""")
    st.success('Map successfully created!')