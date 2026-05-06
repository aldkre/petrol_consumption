import pandas as pd
import streamlit as st

def convert_numeric(df):
    object_cols = [c for c in df.columns if df[c].dtype == object]
    numeric_cols = []

    for col in object_cols:
        cleaned = (
            df[col].astype(str)
            .str.strip()
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        parsed = pd.to_numeric(cleaned, errors="coerce")
        if parsed.notna().all():
            df[col] = parsed
            numeric_cols.append(col)

    st.session_state["numbers_as_string"] = numeric_cols
    return df


def detect_datetime_columns(df):
    object_cols = [c for c in df.columns if df[c].dtype == object]
    date_cols, time_cols, datetime_cols = [], [], []

    for col in object_cols:
        parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
        if parsed.isna().all():
            continue
        if (parsed.dt.time == pd.to_datetime("00:00:00").time()).all():
            date_cols.append(col)
        elif parsed.dt.normalize().nunique() == 1:
            time_cols.append(col)
        else:
            datetime_cols.append(col)

    st.session_state["date_columns"] = date_cols
    st.session_state["time_columns"] = time_cols
    st.session_state["datetime_columns"] = datetime_cols


def merge_datetime(df):
    dc = st.session_state["date_columns"]
    tc = st.session_state["time_columns"]
    dtc = st.session_state["datetime_columns"]

    if dc and tc:
        df["Czas zdarzenia"] = df[[dc[0], tc[0]]].apply(" ".join, axis=1)
    elif dtc:
        df["Czas zdarzenia"] = df[dtc[0]]
    elif dc:
        df["Czas zdarzenia"] = df[dc[0]].astype(str) + " 00:00:00"
    else:
        raise ValueError("Brak kolumn daty/czasu")

    df["Czas zdarzenia"] = pd.to_datetime(df["Czas zdarzenia"], errors="coerce")
    return df
