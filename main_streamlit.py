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

stations_real_time = route_streamlit.get_stations()

if __name__ == "__main__":
    st.sidebar.title("BiciMAD-worker")
    st.title("This is the recommended route for your district:")
    number_district_sidebar = st.sidebar.selectbox("What district have you been assigned today?", list(range(1, 22)), index=0)
    s_sidebar = st.sidebar.text_input('If this is your initial route, enter "Yes". If else, enter your actual coordinates between []', 'Yes')
    van_sidebar = st.sidebar.selectbox("Is your van empty or full?", ["Empty", "Full"], index=0)
    route_map = route_streamlit.get_route_map(stations_real_time, number_district_sidebar, s_sidebar, van_sidebar)
    st_data = folium_static(route_map)
    st.success('Map successfully created!')