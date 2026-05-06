import pandas as pd
import streamlit as st

def prepare_fuel_data(df, source):
    if source == "nie":
        km = st.session_state.km_column
        fuel = st.session_state.fuel_column
        veh = st.session_state.vehicle_column

        df = df.sort_values("Czas zdarzenia")
        df["Kilometry"] = df.groupby(veh)[km].diff()
        df["Spalanie"] = df[fuel] / df["Kilometry"] * 100

        st.session_state.consumption_column = "Spalanie"
        st.session_state.analize = True

    else:
        st.session_state.analize = True

    st.session_state.analize_data = df
    return df
