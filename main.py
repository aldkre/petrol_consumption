import streamlit as st
import pandas as pd
import datetime as dt
import time
import numpy as np

from services.file_loader import load_csv
from services.converters import convert_numeric, detect_datetime_columns, merge_datetime
from services.fuel_preparation import prepare_fuel_data
from services.utils import value_separator


# -------------------------------------------------
# KONFIGURACJA STRONY
# -------------------------------------------------
st.set_page_config(
    page_title="Konwerter pliku zużycia paliwa",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={}
)

# STYLE
st.markdown(
    """
<style>
.title {
    font-size: 50px;
    color: #A04747;
    font-weight: 900;
    font-style: normal;
    text-align: center;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# NAGŁÓWEK
# -------------------------------------------------
logo, space, name = st.columns([2, 1, 4])
with name:
    st.markdown('<p class="title">Transport drogowy</p>', unsafe_allow_html=True)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    on = st.toggle("Kalendarz")
    if on:
        current_day = st.date_input("", dt.datetime.today())
        first_day_in_year = dt.date(dt.datetime.today().year, 1, 1)
        days_counter = (current_day - first_day_in_year)
        st.write(
            "Dzisiaj jest {} dzień roku".format(
                str(days_counter).split(",")[0].split(" ")[0]
            )
        )

# -------------------------------------------------
# GŁÓWNA ZAKŁADKA
# -------------------------------------------------
(fuel_consumption,) = st.tabs(["Analiza zużycia paliwa"])

with fuel_consumption:
    popover, empty, sample_data_col, description = st.columns([2, 1, 1, 2])
    with popover:
        with st.popover("opis funkcjonalności"):
            st.markdown(
                '<div style="text-align: justify; color: #FFF1DB">'
                "Zakładka służy do automatycznej konwersji plików .csv oraz wizualizacji zawartych w nich danych. "
                "Masz do dyspozycji sformatowane dane, ich wizualizację w postaci wykresów i tabel, "
                "z którymi możesz wchodzić w interakcję albo - w razie potrzeby - zapisywać do pliku.\n"
                "Plik powinien posiadać co najmniej takie dane jak: identyfikator pojazdu, określenie czasu tankowania, "
                "stan licznika podczas operacji tankowania oraz ilość zatankowanego paliwa."
                "</div>",
                unsafe_allow_html=True,
            )
    with sample_data_col:
        sample_data_on = st.toggle("Załaduj przykładowe dane")
    with description:
        st.markdown(
            '<div style="text-align: justify; color: #FFF1DB">'
            "Jeżeli chcesz sprawdzić działanie aplikacji bez konieczności posiadania pliku z danymi, "
            'skorzystaj z opcji "Załaduj przykładowe dane"'
            "</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # -------------------------------------------------
    # WYBÓR PLIKU / SAMPLE DATA
    # -------------------------------------------------
    if sample_data_on:
        file = None
        sample_data = True
        source_data_provider = "nie"
    else:
        file = st.file_uploader(
            "Załaduj plik do konwersji",
            accept_multiple_files=False,
            type=["csv"],
        )
        sample_data = False

    # -------------------------------------------------
    # ZAKŁADKA KONWERSJI
    # -------------------------------------------------
    (konwerter,) = st.tabs(["konwersja pliku"])
    with konwerter:
        if not sample_data_on:
            source_data_provider = st.radio(
                "Czy plik źródłowy zawiera pole obliczeniowe z wartością zużycia paliwa?",
                options=["tak", "nie"],
                index=1,
                horizontal=True,
            )
            st.caption(
                "Wybór opcji \"nie\" wiąże się z koniecznością wskazania w dalszych krokach nazw kolumn, "
                "zgodnie z którymi wartość zużycia paliwa zostanie wyliczona automatycznie."
            )
            st.caption(
                "Jeśli występuje potrzeba przeanalizowania innego parametru niż zużycie paliwa, "
                "proszę wybrać \"tak\" i wybrać kolumnę z parametrem do przeanalizowania w miejsce wartości zużycia paliwa."
            )

        # -----------------------------
        # WCZYTANIE I KONWERSJA DANYCH
        # -----------------------------
        if file is not None or sample_data:
            st.session_state["is_file"] = True

            # 1. wczytanie
            temp_data = load_csv(file, sample_data=sample_data)

            # 2. konwersja liczb
            temp_data = convert_numeric(temp_data)

            # 3. wykrycie kolumn dat/czasu
            detect_datetime_columns(temp_data)

            # 4. złożenie datetime
            temp_data = merge_datetime(temp_data)

            st.session_state["upload_data"] = temp_data
            st.session_state["converted_df_with_datetime"] = temp_data

            with st.expander("Poglądowe dane załadowanej tabeli"):
                sample_size = min(10, len(temp_data))
                st.write(temp_data.sample(sample_size))

        else:
            st.session_state["is_file"] = False

        # -------------------------------------------------
        # FORMULARZ WYBORU KOLUMN
        # -------------------------------------------------
        if st.session_state.get("is_file", False):
            with st.form("modifying_df_form"):
                st.divider()

                pick_col, info_col = st.columns(2)
                df_conv = st.session_state["converted_df_with_datetime"]

                with pick_col:
                    # licznik km
                    fuel_consumption_cols_km = st.selectbox(
                        "Wybierz kolumnę przedstawiającą licznik kilometrów",
                        options=df_conv.columns,
                        index=2 if sample_data_on else None,
                        placeholder="Wybierz pole",
                        key="km_column",
                    )
                    if fuel_consumption_cols_km is not None:
                        st.info(
                            f"Przykładowe wartości wybranej kolumny: "
                            f"{', '.join(df_conv.loc[0:3, fuel_consumption_cols_km].astype(str))}",
                            icon="ℹ️",
                        )

                    # pojazd
                    fuel_consumption_cols_vehicle = st.selectbox(
                        "Wybierz kolumnę identyfikującą pojazd",
                        options=df_conv.columns,
                        index=4 if sample_data_on else None,
                        placeholder="Wybierz pole",
                        key="vehicle_column",
                    )
                    if fuel_consumption_cols_vehicle is not None:
                        st.info(
                            f"Przykładowe wartości wybranej kolumny: "
                            f"{', '.join(df_conv.loc[0:3, fuel_consumption_cols_vehicle].astype(str))}",
                            icon="ℹ️",
                        )

                    # paliwo
                    fuel_consumption_cols_fuel = st.selectbox(
                        "Wybierz kolumnę przedstawiającą ilość zatankowanego paliwa",
                        options=df_conv.columns,
                        index=9 if sample_data_on else None,
                        placeholder="Wybierz pole",
                        key="fuel_column",
                    )
                    if fuel_consumption_cols_fuel is not None:
                        st.info(
                            f"Przykładowe wartości wybranej kolumny: "
                            f"{', '.join(df_conv.loc[0:3, fuel_consumption_cols_fuel].astype(str))}",
                            icon="ℹ️",
                        )

                with info_col:
                    if source_data_provider == "nie" and not sample_data_on:
                        st.info(
                            "W pierwszym kroku wskazano konieczność uzupełnienia danych o wartość zużycia paliwa. "
                            "Niezbędne dane do przeprowadzenia odpowiednich kalkulacji to pola zawierające dane "
                            "identyfikujące pojazd, stan licznika, ilość zatankowanego paliwa.",
                            icon="ℹ️",
                        )
                    elif source_data_provider == "tak" and not sample_data_on:
                        st.info(
                            "Nie wskazano w pierwszym kroku konieczności uzupełnienia danych o wartość zużycia paliwa. "
                            "Przyjęto, że tabela źródłowa zawiera pole z wartością zużycia paliwa.",
                            icon="ℹ️",
                        )
                        fuel_consumption_cols_consumption = st.selectbox(
                            "Wybierz kolumnę przedstawiającą zużycie paliwa (lub inną kolumnę liczbową do analizy)",
                            options=df_conv.columns,
                            index=None,
                            placeholder="Wybierz pole",
                            key="consumption_column",
                        )
                    else:
                        fuel_consumption_cols_consumption = None

                st.divider()
                st.warning(
                    "Pamiętaj, że w przypadku, gdy plik zawiera więcej niż jedno tankowanie przyporządkowane do pojazdu w skali dnia, "
                    "czas zdarzenia powinien być wyrażony w sposób jednoznaczny, uniemożliwiający wystąpienie w tabeli danych więcej niż jednego zdarzenia "
                    "odpowiadającego pojazdowi w określonym czasie (godzinie / minucie), tj. czas zdarzenia powinien zawierać zarówno datę jak i czas wystąpienia.",
                    icon="🔥",
                )
                st.form_submit_button("Zatwierdź zmiany")

        # -------------------------------------------------
        # KONWERSJA PLIKU -> PRZYGOTOWANIE DANYCH
        # -------------------------------------------------
        km = st.session_state.get("km_column")
        veh = st.session_state.get("vehicle_column")
        fuel = st.session_state.get("fuel_column")
        cons = st.session_state.get("consumption_column")

        if source_data_provider == "nie":
            st.session_state.ready_to_analyze = all([km, veh, fuel])

        elif source_data_provider == "tak":
            st.session_state.ready_to_analyze = all([km, veh, fuel, cons])

        else:
            st.session_state.ready_to_analyze = False

        try:
            if st.session_state.get("is_file", False) and st.session_state.ready_to_analyze:
                df_conv = st.session_state["converted_df_with_datetime"]
                df_analize = prepare_fuel_data(
                    df_conv,
                    source_data_provider,
                )

                with st.status("Podgląd procesu i danych końcowych"):
                    st.write("Dane po przeprowadzonej konwersji:")
                    time.sleep(0.1)
                    st.write(df_analize)
            else:
                st.warning("Nie wybrano żadnego pliku bądź nie uzupełniono wszystkich wymaganych pól.", icon="⚠️")

            # -------------------------------------------------
            # ANALIZA DANYCH
            # -------------------------------------------------
            if (
                "analize_data" in st.session_state
                and "analize" in st.session_state
                and st.session_state.analize is True
            ):
                temp_data = pd.DataFrame(data=st.session_state.analize_data)
                start_date = temp_data["Czas zdarzenia"].min()
                stop_date = temp_data["Czas zdarzenia"].max()
                lower_limit = temp_data.Spalanie.replace(np.inf, None).dropna().min()
                upper_limit = temp_data.Spalanie.replace(np.inf, None).dropna().max()

                st.header("Analiza zużycia paliwa")
                st.write("Badany okres obejmuje czas od ", start_date, " do ", stop_date)
                st.divider()

                # -----------------------------
                # FILTROWANIE POJAZDU
                # -----------------------------
                st.subheader("Wyodrębnienie danych pojazdu")
                st.markdown(
                    "W celu odfiltrowania danych konkretnego pojazdu, proszę o wybranie go z listy rozwijanej dostępnej poniżej."
                )
                st.selectbox(
                    "Wybierz nazwę składnika do odfiltrowania",
                    options=temp_data[st.session_state.vehicle_column].unique(),
                    index=None,
                    placeholder="Wybierz pole",
                    key="selected",
                )
                df_vehicle = temp_data[
                    temp_data[st.session_state.vehicle_column] == st.session_state.selected
                ]
                st.write(df_vehicle)

                file_out_name = st.text_input(
                    "Nazwa pliku wyjściowego",
                    st.session_state.selected,
                    max_chars=50,
                )

                save_btn = st.download_button(
                    label="Zapisz do pliku",
                    data=df_vehicle.to_csv().encode("windows-1250"),
                    file_name=f"{file_out_name}.csv",
                    mime="text/csv",
                )
                if save_btn:
                    st.success("Plik został zapisany", icon="✅")

                st.markdown(
                    '<div style="text-align: justify; color: #DAD4B5">'
                    "Plik zawiera wszystkie dane odpowiadające wybranemu pojazdowi "
                    "/ nie uwzględnia filtrowania danych spoza wyznaczonego zakresu wartości spalania, "
                    "którego przedział można określić w kolejnym kroku (poniżej)"
                    "</div>",
                    unsafe_allow_html=True,
                )

                st.divider()

                # -----------------------------
                # ANALIZA GŁÓWNA
                # -----------------------------
                st.subheader("Podstawowe dane zużycia paliwa w badanym okresie")

                desc, slider = st.columns(2, gap="large")
                with desc:
                    st.info(
                        "W celu eliminacji wartości nieprawidłowych należy zawęzić zakres poziomu zużycia paliwa, "
                        "używając suwaka znajdującego się po prawej stronie. "
                        "Dane spoza zakresu zostaną odseparowane i przedstawione w dodatkowej tabeli celem identyfikacji przyczyny błędu.",
                        icon="ℹ️",
                    )

                manual_true = False
                with slider:
                    if lower_limit == upper_limit:
                        st.info("Zakres danych: tylko jedna wartość")
                        st.session_state["param_limits"] = (lower_limit, upper_limit)
                        st.session_state['one_record'] = True
                    else:
                        st.session_state['one_record'] = False
                        st.slider(
                            "Uwzględnij dane z zakresu",
                            min_value=lower_limit,
                            max_value=upper_limit,
                            step=0.1,
                            value=(lower_limit, upper_limit),
                            key="param_limits",
                        )
                        manual_true = st.toggle("Ustaw ręcznie")
                        if manual_true:
                            min_col, max_col = st.columns(2, gap="large")
                            with min_col:
                                manual_min = st.number_input(
                                    "Wprowadź wartość minimalną", key="manual_min"
                                )
                            with max_col:
                                manual_max = st.number_input(
                                    "Wprowadź wartość maksymalną", key="manual_max"
                                )

                if manual_true:
                    out_of_range = temp_data[
                        (temp_data["Spalanie"] < st.session_state.manual_min)
                        | (temp_data["Spalanie"] > manual_max)
                    ]
                    temp_data = temp_data[
                        (temp_data["Spalanie"] >= st.session_state.manual_min)
                        & (temp_data["Spalanie"] <= st.session_state.manual_max)
                    ]
                elif "param_limits" in st.session_state:
                    out_of_range = temp_data[
                        (temp_data["Spalanie"] < st.session_state.param_limits[0])
                        | (temp_data["Spalanie"] > st.session_state.param_limits[1])
                    ]
                    temp_data = temp_data[
                        (temp_data["Spalanie"] >= st.session_state.param_limits[0])
                        & (temp_data["Spalanie"] <= st.session_state.param_limits[1])
                    ]

                temp_data_mean = temp_data.groupby(st.session_state.vehicle_column)[
                    "Spalanie"
                ].mean()
                temp_data = temp_data.merge(
                    temp_data_mean.rename("Spalanie średnia"),
                    left_on=st.session_state.vehicle_column,
                    right_index=True,
                    how="left",
                )
                temp_data["Spalanie średnia +/-"] = (
                    temp_data["Spalanie średnia"] - temp_data.Spalanie
                )

                true_value, stats, false_value = st.columns(3)
                with true_value:
                    st.caption("Tabela z danymi odfiltrowanymi")
                    if len(temp_data) > 0:
                        grouped = temp_data.groupby(st.session_state.vehicle_column)
                        st.session_state.one_record = (grouped.size().min() == 1 and grouped.size().max() == 1)

                        if source_data_provider == "tak":
                            st.write(
                                grouped[st.session_state.consumption_column].describe()
                            )
                        else:
                            st.write(
                                grouped["Spalanie"].describe()
                            )
                    filtered_file_name = st.text_input(
                        "Wprowadź nazwę pliku", value="Dane z zakresu"
                    )
                    st.download_button(
                        label="Zapisz do pliku",
                        data=temp_data.to_csv().encode("windows-1250"),
                        file_name=f"{filtered_file_name}.csv",
                        mime="text/csv",
                    )

                with false_value:
                    st.caption("Tabela z danymi spoza zakresu")
                    st.write(out_of_range)

                    correction_file_out_name = st.text_input(
                        "Wprowadź nazwę pliku", value="Dane spoza zakresu"
                    )
                    st.download_button(
                        label="Zapisz do pliku",
                        data=out_of_range.to_csv().encode("windows-1250"),
                        file_name=f"{correction_file_out_name}.csv",
                        mime="text/csv",
                    )

                if len(temp_data) > 0:
                    with stats:
                        if manual_true or "param_limits" in st.session_state:
                            veh_col = st.session_state.vehicle_column
                            km_sum = temp_data.groupby(veh_col)["Kilometry"].sum()
                            fuel_sum = temp_data.groupby(veh_col)[
                                st.session_state.fuel_column
                            ].sum()

                            id_max_km = km_sum.idxmax()
                            max_km = km_sum.max()
                            id_min_km = km_sum.idxmin()
                            min_km = km_sum.min()

                            id_max_l = fuel_sum.idxmax()
                            max_l = fuel_sum.max()
                            id_min_l = fuel_sum.idxmin()
                            min_l = fuel_sum.min()

                            st.metric(
                                label=f"Kilometry zrealizowane [max] {id_max_km}",
                                value=f"{value_separator(max_km)} km",
                                delta=f"{value_separator(max_km - min_km)} km",
                            )
                            st.metric(
                                label=f"Kilometry zrealizowane [min] {id_min_km}",
                                value=f"{value_separator(min_km)} km",
                                delta=f"{value_separator(min_km - max_km)} km",
                            )
                            st.metric(
                                label=f"Litry zatankowane [max] {id_max_l}",
                                value=f"{value_separator(max_l)} l",
                                delta=f"{value_separator(max_l - min_l)} l",
                            )
                            st.metric(
                                label=f"Litry zatankowane [min] {id_min_l}",
                                value=f"{value_separator(min_l)} l",
                                delta=f"{value_separator(min_l - max_l)} l",
                            )

                # -----------------------------
                # NORMY
                # -----------------------------

                st.divider()

                info, before_section, after_section = st.columns([3, 2, 6])
                with info:
                    st.text("")
                    st.info(
                        "Jeżeli chcesz uwzględnić wyznaczone przez Ciebie normy spalania dla poszczególnych pojazdów, "
                        "określ je, wpisując w miejsce średniej wyliczonej z dostępnych i odfiltrowanych danych znajdujących się w tabeli poniżej. "
                        "W przypadku uzupełnienia wartości przyjętej normy dla pojazdu w kolumnie 'Spalanie średnia/norma +/-' pojawi się różnica między poziomem zużycia paliwa a przyjętą normą, "
                        "natomiast w przypadku, gdy dla danego pojazdu norma taka nie została określona, w kolumnie znajdzie się różnica między poziomem zużycia paliwa a średnią poziomu spalania z badanego okresu.",
                        icon="ℹ️",
                    )
                with before_section:
                    norms_table = temp_data_mean.copy()
                    st.caption("Tabela norm spalania")
                    st.data_editor(norms_table, key="new_norms")
                    v_no = norms_table.reset_index()[st.session_state.vehicle_column]

                    vehicle_norm = {}
                    for key in st.session_state.new_norms["edited_rows"]:
                        v = v_no[int(key)]
                        vehicle_norm[v] = st.session_state.new_norms["edited_rows"][key][
                            "Spalanie"
                        ]
                    st.write(vehicle_norm)

                    apply_new_norm = st.button("Zatwierdzam zmiany")
                    if apply_new_norm:
                        temp_data_norm = pd.DataFrame.from_dict(
                            data={
                                st.session_state.vehicle_column: [
                                    key for key in vehicle_norm.keys()
                                ],
                                "Norma": [value for value in vehicle_norm.values()],
                            }
                        )
                        temp_data = temp_data.merge(
                            temp_data_norm,
                            how="left",
                            on=st.session_state.vehicle_column,
                        )
                        temp_data["Spalanie średnia/norma +/-"] = temp_data.apply(
                            lambda row: row.Norma - row.Spalanie
                            if row.Norma > 0
                            else row["Spalanie średnia +/-"],
                            axis=1,
                        )

                with after_section:
                    if apply_new_norm:
                        st.session_state["data_set_norms"] = temp_data
                    if "data_set_norms" in st.session_state:
                        st.caption(
                            "Tabela zawiera dodatkowe kolumny określające przyjęte normy i różnice między nimi a poziomem zużycia paliwa"
                        )
                        st.write(temp_data)

                if "data_set_norms" in st.session_state:
                    temp_data = st.session_state.data_set_norms

                st.divider()

                # -----------------------------
                # WIZUALIZACJA
                # -----------------------------
                if st.session_state.one_record == False:
                    st.subheader("Wizualizacja podstawowych danych z wybranego zakresu danych")
                    st.caption("Nie uwzględnia danych wyłączonych z analizy")

                    n_col, sort_col = st.columns(2, gap="medium")
                    with n_col:
                        n_item = st.slider(
                            label="Ogranicz widoczność do n pozycji",
                            min_value=1,
                            max_value=temp_data[st.session_state.vehicle_column].nunique(),
                            value=5,
                        )
                    with sort_col:
                        sort_type_label = st.select_slider(
                            label="Typ sortowania",
                            options=["rosnąco", "malejąco"],
                            key="sorting_type",
                        )
                    if sort_type_label == "rosnąco":
                        sort_type = True
                        color_type = "#387478"
                    else:
                        sort_type = False
                        color_type = "#A04747"

                    if manual_true or "param_limits" in st.session_state:

                        sections = {
                            "Poziom zużycia paliwa": st.session_state.consumption_column,
                            "Ilość zrealizowanych wozokilometrów": "Kilometry",
                            "Ilość zatankowanych litrów paliwa": st.session_state.fuel_column,
                        }

                        metrics = [
                            ("Średnia", "mean", color_type),
                            ("Wartość minimalna", "min", color_type),
                            ("Wartość maksymalna", "max", color_type),
                            ("Odchylenie standardowe", "std", "#FEFFA7"),
                        ]

                        for section_title, value_col in sections.items():
                            st.subheader(section_title)
                            col_mean, col_min, col_max, col_std = st.columns(4, gap="medium")

                            for (metric_title, agg_func, bar_color), container in zip(
                                    metrics, [col_mean, col_min, col_max, col_std]
                            ):
                                with container:
                                    st.write(f"{metric_title} w okresie")
                                    st.bar_chart(
                                        data=temp_data.groupby(st.session_state.vehicle_column)[value_col]
                                        .agg(agg_func)
                                        .sort_values(ascending=sort_type)
                                        .head(n_item),
                                        color=bar_color,
                                    )

                st.data_editor(
                        temp_data,
                        column_order=[
                            "Czas zdarzenia",
                            "Dni rozliczeniowe",
                            st.session_state.vehicle_column,
                            st.session_state.km_column,
                            st.session_state.fuel_column,
                            "Kilometry",
                            "Spalanie",
                            "Spalanie średnia",
                            "Spalanie średnia +/-",
                            "Norma",
                            "Spalanie średnia/norma +/-",
                        ],
                        column_config={
                            "Czas zdarzenia": st.column_config.DateColumn(
                                "Czas zdarzenia",
                                help="Czas rejestrowanego zdarzenia, najczęściej procesu tankowania pojazdu",
                                format="D MMM YYYY, h:mm a",
                            ),
                            "Kilometry": st.column_config.NumberColumn(
                                "Wozokilometry",
                                help="Zrealizowane wozokilometry w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                                format="%d wzkm",
                            ),
                            "Spalanie": st.column_config.NumberColumn(
                                "Spalanie",
                                help="Poziom zużycia paliwa w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                                format="%.2f l / 100 wzkm",
                            ),
                            "Spalanie średnia": st.column_config.ProgressColumn(
                                "Spalanie średnia",
                                help="Średnia zużycia paliwa w okresie",
                                format="%.2f l / 100 wzkm",
                                min_value=0,
                                max_value=temp_data["Spalanie średnia"].max(),
                            ),
                            "Spalanie średnia +/-": st.column_config.NumberColumn(
                                "Spalanie średnia +/-",
                                help="Różnica między poziomem zużycia paliwa a średnią zużycia paliwa w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                                format="%.2f l / 100 wzkm",
                            ),
                        },
                    )

                st.divider()

                if manual_true or "param_limits" in st.session_state:

                    st.subheader("Wizualizacja podstawowych danych wybranego zakresu i pojazdu")

                    selected_vehicle = st.selectbox(
                        label="Wybierz pojazd do analizy parametrów",
                        options=temp_data[st.session_state.vehicle_column].unique()
                    )

                    # filtr danych dla pojazdu
                    df_v = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index(
                        "Czas zdarzenia")

                    # konfiguracja sekcji
                    sections = {
                        "Poziom zużycia paliwa": st.session_state.consumption_column,
                        "Liczba zatankowanego paliwa": st.session_state.fuel_column,
                        "Liczba zrealizowanych kilometrów": "Kilometry",
                    }

                    cols = st.columns(3, gap="medium")

                    for (title, col_name), container in zip(sections.items(), cols):
                        with container:
                            # wartości statystyczne
                            id_max = df_v[col_name].idxmax()
                            max_val = df_v[col_name].max()
                            id_min = df_v[col_name].idxmin()
                            min_val = df_v[col_name].min()

                            # wykres
                            st.line_chart(df_v[col_name])

                            # opis
                            st.write(f"{title} pojazdu {selected_vehicle}")

                            # metryki
                            st.metric(
                                label=f"Maksymalna wartość wystąpiła {id_max}",
                                value=value_separator(max_val),
                                delta=value_separator(max_val - min_val)
                            )
                            st.metric(
                                label=f"Minimalna wartość wystąpiła {id_min}",
                                value=value_separator(min_val),
                                delta=value_separator(min_val - max_val)
                            )

                    # tabela końcowa
                    st.data_editor(
                        df_v.reset_index(),
                        column_order=[
                            'Czas zdarzenia', 'Dni rozliczeniowe',
                            st.session_state.vehicle_column, st.session_state.km_column,
                            st.session_state.fuel_column,
                            'Kilometry', 'Spalanie', 'Spalanie średnia',
                            'Spalanie średnia +/-', 'Norma', 'Spalanie średnia/norma +/-'
                        ],
                        hide_index=True
                    )

        except Exception as e:
            st.error(
                "❌ Wystąpił błąd podczas analizy danych. "
                "Najprawdopodobniej wybrano nieprawidłowe kolumny lub dane nie spełniają wymagań.",
            )
