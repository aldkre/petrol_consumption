import streamlit as st
import pandas as pd
import datetime as dt
import time
import re
import numpy as np


st.set_page_config(
    page_title="Konwerter pliku zużycia paliwa",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={}
)

#STYLE
st.markdown("""
<style>
.title {
    font-size: 50px;
    color: #A04747;
    font-weight: 900;
    font-style: normal;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


def value_separator(value):
    """
    Formatting number
    :param value: have to be a number
    :return: rounded value including a thousand separator
    """
    value = round(value,2)
    value = f'{value:,}'
    return value


def numbers_as_string_checker(df, objects_list):
    text_series = [df[col] for col in objects_list]
    numbers_series = []
    for ser in text_series:
        temp = [0 if (re.search("[a-zA-Z:\.]",row) == None and row != None) else 1 for row in ser.apply(str)]
        if sum(temp) == 0:
            numbers_series.append(ser.name)
    st.session_state["numbers_as_string"] = numbers_series


def numbers_as_string_changer(df, num_as_str_list):
    for item in num_as_str_list:
        df[item] = df[item].str.replace(',','.')
        df[item] = pd.to_numeric(df[item], errors='coerce')
    st.session_state["converted_df"] = df


def datetime_as_datetime_checker(df, objects_list):
    all_series = [df[col] for col in objects_list]
    date_signs = ['-', '/', '.']
    date_series = []
    time_series = []
    datetime_series = []
    for ser in all_series:
        temp = [0 if (row != None and len(row) == 10 and ((row[2] in date_signs) or (row[4] in date_signs))) else 1 for row in ser.apply(str)]
        if sum(temp) == 0:
            date_series.append(ser.name)
            st.session_state["date_columns"] = date_series
    for ser in all_series:
        temp = [0 if (row != None and len(row) == 8 and row[2] == ':' and row[5] == ':') else 1 for row in ser.apply(str)]
        if sum(temp) == 0:
            time_series.append(ser.name)
            st.session_state["time_columns"] = time_series
    for ser in all_series:
        temp = [0 if (row != None and (len(row) == 19 or len(row) == 17) and ':' in row) else 1 for row in ser.apply(str)]
        if sum(temp) == 0:
            datetime_series.append(ser.name)
            st.session_state["datetime_columns"] = datetime_series


def datetime_changer(df):
    if 'date_columns' in st.session_state and 'time_columns' in st.session_state:
        df['Czas zdarzenia'] = df[[st.session_state.date_columns[0], st.session_state.time_columns[0]]].apply(" ".join, axis=1)
    elif 'datetime_columns' in st.session_state:
        df['Czas zdarzenia'] = df[st.session_state['datetime_columns'][0]]
    df['Czas zdarzenia'] = pd.to_datetime(df['Czas zdarzenia'])
    st.session_state["converted_df_with_datetime"] = df


def upload_checker(file):
    if file is not None or sample_data == True:
        st.session_state['is_file'] = True
        if sample_data == False and 'csv' in file.type:
            try:
                temp_data = pd.read_csv(file, delimiter=';')
            except:
                temp_data = pd.read_csv(file, delimiter=',')
        elif sample_data == True:
            temp_data = pd.read_csv('sample.csv', delimiter=';')
        temp_data = temp_data.dropna(how='all', axis=1).dropna(how='all', axis=0)
        object_cols = [col for col in temp_data.columns if temp_data[col].dtype == object]
        st.session_state['upload_data'] = temp_data
        st.session_state['object_cols'] = object_cols

        numbers_as_string_checker(df=st.session_state.upload_data, objects_list=st.session_state.object_cols)
        datetime_as_datetime_checker(df=st.session_state.upload_data, objects_list=st.session_state.object_cols)

        numbers_as_string_changer(df=st.session_state.upload_data, num_as_str_list=st.session_state.numbers_as_string)
        datetime_changer(df=st.session_state.converted_df)

        with st.expander("Poglądowe dane załadowanej tabeli"):
            st.write(st.session_state.converted_df_with_datetime.sample(10))
    else:
        st.session_state['is_file'] = False


def prepare_df_to_analize(df):
    if source_data_provider == 'nie':
        if fuel_consumption_cols_km != None and fuel_consumption_cols_fuel != None and fuel_consumption_cols_vehicle != None:
                if (df[st.session_state.km_column].dtype) == 'int64' and (df[st.session_state.fuel_column].dtype) == 'float64':
                    df['Dni rozliczeniowe'] = df['Czas zdarzenia'] - (df.sort_values(by='Czas zdarzenia').groupby(st.session_state.vehicle_column)['Czas zdarzenia'].shift())
                    df['Kilometry'] = df[st.session_state.km_column] - (df.sort_values(by='Czas zdarzenia').groupby(st.session_state.vehicle_column)[st.session_state.km_column].shift())
                    df['Spalanie'] = df[st.session_state.fuel_column] / df.Kilometry * 100

                    st.session_state.consumption_column = "Spalanie"
                    st.session_state['analize'] = True
                else:
                    st.warning('Błędnie przyporządkowano nazwy kolumn do pól.', icon="⚠️")
                    st.session_state['analize'] = False
        else:
                st.warning('Nie uzupełniono wszystkich pozycji.', icon="⚠️")
                st.session_state['analize'] = False

    elif source_data_provider == 'tak':
        if fuel_consumption_cols_consumption == None:
            st.warning('Nie wskazano kolumny z zużyciem paliwa.', icon="⚠️")
            st.session_state['analize'] = False
        else:
            st.session_state['analize'] = True

    st.session_state['analize_data'] = df


#NAGŁÓWEK STRONY
logo, space, name = st.columns([2,1,4])
with name:
    st.markdown('<p class="title">Transport drogowy</p>', unsafe_allow_html=True)

#SIDEBAR
with st.sidebar:
    with st.container(height=550):
        #OPIS STRONY
        st.markdown('<div style="text-align: justify;">Aplikacja ułatwia zarządzanie podstawowymi sferami transportu drogowego i jest na bieżąco rozbudowywana o kolejne funkcjonalności.</div>', unsafe_allow_html=True)
        st.divider()

    on = st.toggle("Kalendarz")
    if on:
        current_day = st.date_input("", dt.datetime.today())
        first_day_in_year = dt.date(dt.datetime.today().year, 1, 1)
        days_counter = (current_day - first_day_in_year)
        st.write("Dzisiaj jest {} dzień roku".format(str(days_counter).split(',')[0].split(' ')[0]))

#PODZIAŁ GŁÓWNEJ STRONY NA NAGŁÓWKI
main_tab_4, main_tab_1, main_tab_2, main_tab_3 = st.tabs(['Analiza zużycia paliwa', 'Baza taboru', 'Eksploatacja taboru', 'Zarządzanie transportem'])

with main_tab_1:
    st.subheader("Strona w budowie")
with main_tab_2:
    st.subheader("Strona w budowie")
with main_tab_3:
    st.subheader("Strona w budowie")

#ZAKŁADKA ANALIZY PALIWA
with main_tab_4:
    popever, empty, sample_data, description = st.columns([2,1,1,2])
    with popever:
        with st.popover("opis funkcjonalności"):
            st.markdown('<div style="text-align: justify; color: #FFF1DB">Zakładka służy do automatycznej konwersji plików .csv oraz wizualizacji zawartych w nich danych. '
                        'Masz do dyspozycji sformatowane dane, ich wizualizację w postaci wykresów i tabel, z którymi możesz wchodzić w interakcję albo - w razie potrzeby - zapisywać do pliku.\n'
                        'W celu przeprowadzenia konwersji użyj zakładki "konwersja spoza schematów" bądź użyj gotowych schematów dla określonych dostawców. '
                        'Jeśli w schematach nie odnajdziesz odpowiedniego szablonu, prześlij formularz zgłoszeniowy wraz z przykładowym plikiem, do którego przygotujemy szablon. '
                        'Do tego czasu, prosimy o korzystanie z uniwersalnej wersji konwersji, tj. "konwersja spoza schematów".</div>', unsafe_allow_html=True)
    with sample_data:
        sample_data_on = st.toggle("Załaduj przykładowe dane")
    with description:
        st.markdown('<div style="text-align: justify; color: #FFF1DB">'
                    'Jeżeli chcesz sprawdzić działanie aplikacji bez konieczności posiadania pliku z danymi, '
                    'skorzystaj z opcji "Załaduj przykładowe dane"</div>',
            unsafe_allow_html=True)

    st.divider()

    # todo: FUNKCJA ŁĄCZENIA WIELU PLIKÓW
    if sample_data_on:
        file=None
        sample_data = True
        source_data_provider = 'nie'
    else:
        file = st.file_uploader("Załaduj plik do konwersji", accept_multiple_files=False, type=['csv'])
        sample_data = False

    #ZAKŁADKI WEWNĘTRZNE
    tab_1, tab_2 = st.tabs(['konwersja pliku spoza schematu', 'konwersja pliku - schemat'])
    with tab_1:

        #FORMULARZ NIE JEST WIDOCZNY PRZY SAMPLE DATA
        if not sample_data_on:
            source_data_provider = st.radio("Czy plik źródłowy zawiera pole obliczeniowe z wartością zużycia paliwa?", options=['tak', 'nie'],
                                            index=1, horizontal=True)
            st.caption('Wybór opcji "nie" wiąże się z koniecznością wskazania w dalszych krokach nazw kolumn, zgodnie z którymi wartość zużycia paliwa zostanie wyliczona automatycznie.')
            st.caption('Jeśli występuje potrzeba przeanalizowania innego parametru niż zużycie paliwa, proszę wybrać "tak" i wybrać kolumnę z parametrem do przeanalizowania w miejsce wartości zużycia paliwa.')

        upload_checker(file=file)

        #FORMULARZ RUCHOMY W DWÓCH WERSJACH, ZALEŻNY OD DOKONANEGO W POPRZEDNIM KROKU WYBORU
        if st.session_state.is_file == True:
            with st.form("modifying_df_form"):
                st.divider()

                pick_col, info_col  = st.columns(2)
                with pick_col:
                    if sample_data_on:
                        fuel_consumption_cols_km = st.selectbox("Wybierz kolumnę przedstawiającą licznik kilometrów",options=st.session_state.converted_df_with_datetime.columns,index=2, placeholder="Wybierz pole", key="km_column")
                    else:
                        fuel_consumption_cols_km = st.selectbox("Wybierz kolumnę przedstawiającą licznik kilometrów", options=st.session_state.converted_df_with_datetime.columns, index=None, placeholder="Wybierz pole", key="km_column")
                    if fuel_consumption_cols_km != None:
                        st.info(f"Przykładowa wartość wybranej kolumny: {st.session_state.converted_df_with_datetime.loc[0:3,fuel_consumption_cols_km].to_list()}", icon="ℹ️")

                    if sample_data_on:
                        fuel_consumption_cols_vehicle = st.selectbox("Wybierz kolumnę identyfikującą pojazd", options=st.session_state.converted_df_with_datetime.columns, index=4, placeholder="Wybierz pole", key="vehicle_column")
                    else:
                        fuel_consumption_cols_vehicle = st.selectbox("Wybierz kolumnę identyfikującą pojazd", options=st.session_state.converted_df_with_datetime.columns, index=None, placeholder="Wybierz pole", key="vehicle_column")
                    if fuel_consumption_cols_vehicle != None:
                        st.info(f"Przykładowa wartość wybranej kolumny: {st.session_state.converted_df_with_datetime.loc[0:3,fuel_consumption_cols_vehicle].to_list()}", icon="ℹ️")

                    if sample_data_on:
                        fuel_consumption_cols_fuel = st.selectbox("Wybierz kolumnę przedstawiającą ilość zatankowanego paliwa",options=st.session_state.converted_df_with_datetime.columns, index=9,placeholder="Wybierz pole", key="fuel_column")
                    else:
                        fuel_consumption_cols_fuel = st.selectbox("Wybierz kolumnę przedstawiającą ilość zatankowanego paliwa", options=st.session_state.converted_df_with_datetime.columns, index=None, placeholder="Wybierz pole", key="fuel_column")
                    if fuel_consumption_cols_fuel != None:
                        st.info(f"Przykładowa wartość wybranej kolumny: {st.session_state.converted_df_with_datetime.loc[0:3,fuel_consumption_cols_fuel].to_list()}", icon="ℹ️")

                with info_col:
                    if source_data_provider == 'nie':
                        st.info("W pierwszym kroku wskazano konieczność uzupełnienia danych o wartość zużycia paliwa. Niezbędne dane do przeprowadzenia odpowiednich kalkulacji to pola zawierające dane identyfikujące pojazd, stan licznika, ilość zatankowanego paliwa.", icon="ℹ️")
                    elif source_data_provider == 'tak':
                        st.info("Nie wskazano w pierwszym kroku konieczności uzupełnienia danych o wartość zużycia paliwa. Przyjeto, że tabela źródłowa zawiera pole z wartością zużycia paliwa.", icon="ℹ️")
                        if source_data_provider == 'tak':
                            fuel_consumption_cols_consumption = st.selectbox(
                                "Wybierz kolumnę przedstawiającą zużycie paliwa (lub inną kolumnę liczbową do analizy)",
                                options=st.session_state.converted_df_with_datetime.columns, index=None,
                                placeholder="Wybierz pole", key="consumption_column")
                st.divider()
                st.warning(
                    "Pamiętaj, że w przypadku, gdy plik zawiera więcej niż jedno tankowanie przyporządkowane do pojazdu w skali dnia, czas zdarzenia powinien być wyrażony w sposób jednoznaczny, uniemożliwiajacy wystąpienie w tabeli danych więcej niż jednego zdarzenia odpowiadającego pojazdowi w określonym czasie (godzinie / minucie), tj. czas zdarzenia powinien zawierać zarówno datę jak i czas wystąpienia.",
                    icon="🔥")
                st.form_submit_button("Zatwierdź zmiany")

        # KONWERSJA PLIKU
        if st.session_state.is_file is True:
            prepare_df_to_analize(df = st.session_state.converted_df_with_datetime)

            with st.status("Podgląd procesu i danych końcowych"):
                st.write("Dane po przeprowadzonej konwersji:")
                time.sleep(0.1)
                st.write(st.session_state.analize_data)

        else:
            st.warning('Nie wybrano żadnego pliku.', icon="⚠️")

    #ANALIZA DANYCH
    if "analize_data" in st.session_state and 'analize' in st.session_state and st.session_state.analize == True:

        #okreslenie zakresu danych
        temp_data = pd.DataFrame(data=st.session_state.analize_data)
        start_date = temp_data['Czas zdarzenia'].min()
        stop_date = temp_data['Czas zdarzenia'].max()
        lower_limit = temp_data.Spalanie.replace(np.inf, None).dropna().min()
        upper_limit = temp_data.Spalanie.replace(np.inf, None).dropna().max()

        st.header("Analiza zużycia paliwa")
        st.write("Badany okres obejmuje czas od ", start_date, " do ", stop_date)

        st.divider()

        #FILTROWANIE DANYCH
        st.subheader("Wyodrębnienie danych pojazdu")
        st.markdown("W celu odfiltrowania danych konkretnego pojazdu, proszę o wybranie go z listy rozwijanej dostępnej poniżej.")
        st.selectbox("Wybierz nazwę składnika do odfiltrowania", options=temp_data[st.session_state.vehicle_column].unique(), index=None, placeholder="Wybierz pole", key='selected')
        df = temp_data[temp_data[st.session_state.vehicle_column] == st.session_state.selected]
        st.write(df)
        file_out_name = st.text_input("Nazwa pliku wyjściowego", st.session_state.selected, max_chars=50)

        save_btn = st.download_button(
            label="Zapisz do pliku",
            data=df.to_csv().encode("windows-1250"),
            file_name=f"{file_out_name}.csv",
            mime="text/csv",
        )

        if save_btn:
            st.success('Plik został zapisany', icon="✅")

        st.markdown('<div style="text-align: justify; color: #DAD4B5">'
                    'Plik zawiera wszystkie dane odpowiadające wybranemu pojazdowi '
                    '/ nie uwzględnia filtrowania danych spoza wyznaczonego zakresu wartości spalania, '
                    'którego przedział można określić w kolejnym kroku (poniżej)</div>',
                    unsafe_allow_html=True)

        st.divider()

        #ANALIZA GŁÓWNA
        st.subheader("Podstawowe dane zużycia paliwa w badanym okresie")

        desc, slider = st.columns(2, gap="large")
        with desc:
            st.info("W celu eliminacji wartości nieprawidłowych należy zawęzić zakres poziomu zużycia paliwa, używając suwaka znajdującego się po prawej stronie. "
                        "Dane spoza zakresu zostaną odseparowane i przedstawione w dodatkowej tabeli celem identyfikacji przyczyny błędu.", icon="ℹ️")

        with slider:
            st.slider("Uwzględnij dane z zakresu", min_value= lower_limit,
                      max_value=upper_limit, step=.1,
                      value=(lower_limit, upper_limit), key="param_limits")
            manual_true = st.toggle("Ustaw ręcznie")
            if manual_true:
                min, max = st.columns(2, gap="large")
                with min:
                    manual_min = st.number_input("Wprowadź wartość minimalną", key="manual_min")
                with max:
                    manual_max = st.number_input("Wprowadź wartość maksymalną", key="manual_max")

        if manual_true:
            out_of_range = temp_data[(temp_data['Spalanie'] < st.session_state.manual_min) | (temp_data['Spalanie'] > manual_max)]
            temp_data = temp_data[(temp_data['Spalanie'] >= st.session_state.manual_min) & (temp_data['Spalanie'] <= st.session_state.manual_max)]
        elif "param_limits" in st.session_state:
            out_of_range = temp_data[(temp_data['Spalanie'] < st.session_state.param_limits[0]) | (temp_data['Spalanie'] > st.session_state.param_limits[1])]
            temp_data = temp_data[(temp_data['Spalanie'] >= st.session_state.param_limits[0]) & (temp_data['Spalanie'] <= st.session_state.param_limits[1])]

        temp_data_mean = temp_data.groupby(st.session_state.vehicle_column)['Spalanie'].mean()
        temp_data = temp_data.join(temp_data_mean, on=st.session_state.vehicle_column, how='left', rsuffix=' średnia')
        temp_data['Spalanie średnia +/-'] = temp_data['Spalanie średnia'] - temp_data.Spalanie


        # todo: FUNKCJA ŁĄCZENIA DANYCH Z BAZĄ TABORU

        true_value, stats, false_value = st.columns(3)
        with true_value:
            st.caption("Tabela z danymi odfiltrowanymi")
            if len(temp_data) > 0:
                if source_data_provider == 'tak':
                    st.write(temp_data.groupby(st.session_state.vehicle_column)[st.session_state.consumption_column].describe())

                elif source_data_provider == 'nie':
                    st.write(temp_data.groupby(st.session_state.vehicle_column)['Spalanie'].describe())

        with false_value:
            st.caption("Tabela z danymi spoza zakresu")
            st.write(out_of_range)
                # todo: FUNKCJA KOREKCJI BŁĘDÓW - DANYCH SPOZA ZAKRESU

            correction_file_out_name = st.text_input("Wprowadź nazwę pliku", value="Dane spoza zakresu")
            st.download_button(
            label="Zapisz do pliku",
            data=df.to_csv().encode("windows-1250"),
            file_name=f"{correction_file_out_name}.csv",
            mime="text/csv",
        )

        if len(temp_data) > 0:

            with stats:
                if (manual_true or "param_limits" in st.session_state):
                    id_max_km = temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].sum().idxmax()
                    max_km = temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].sum().max()
                    id_min_km = temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].sum().idxmin()
                    min_km = temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].sum().min()
                    id_max_l = temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].sum().idxmax()
                    max_l = temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].sum().max()
                    id_min_l = temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].sum().idxmin()
                    min_l = temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].sum().min()

                    st.metric(label= f"Kilometry zrealizowane [max] {id_max_km}", value= f"{value_separator(max_km)} km", delta=f"{value_separator(max_km-min_km)} km")
                    st.metric(label=f"Kilometry zrealizowane [min] {id_min_km}", value=f"{value_separator(min_km)} km", delta=f"{value_separator(min_km-max_km)} km")

                    st.metric(label=f"Litry zatankowane [max] {id_max_l}", value=f"{value_separator(max_l)} l", delta=f"{value_separator(max_l - min_l)} l")
                    st.metric(label=f"Litry zatankowane [min] {id_min_l}", value=f"{value_separator(min_l)} l", delta=f"{value_separator(min_l - max_l)} l")

            #zmiana norm
            st.text("")
            st.info(
            "Jeżeli chcesz uwzględnić wyznaczone przez Ciebie normy spalania dla poszczególnych pojazdów, określ je, wpisując w miejsce średniej wyliczonej z dostępnych i odfiltrowanych danych znajdujących się w tabeli poniżej. "
            "W przypadku uzupełnienia wartości przyjętej normy dla pojazdu w kolumnie 'Spalanie średnia/norma +/-' pojawi się różnica między poziomem zużycia paliwa a przyjętą normą,"
            " natomiast w przypadku, gdy dla danego pojazdu norma taka nie została określona, w kolumnie znajdzie się różnica między poziomem zużycia paliwa a średnią poziomu spalania z badanego okresu.",
            icon="ℹ️")

            before_section, after_section = st.columns([1,5])
            with before_section:
                norms_table = temp_data_mean.copy()
                st.caption("Tabela norm spalania")
                st.data_editor(norms_table, key='new_norms')
                v_no = norms_table.reset_index()[st.session_state.vehicle_column]

                vehicle_norm = {}
                for key in st.session_state.new_norms['edited_rows']:
                    v = v_no[int(key)]
                    vehicle_norm[v] = st.session_state.new_norms['edited_rows'][key]['Spalanie']
                st.write(vehicle_norm)

                apply_new_norm = st.button("Zatwierdzam zmiany")
                if apply_new_norm:
                    temp_data_norm = pd.DataFrame.from_dict(data={st.session_state.vehicle_column: [key for key in vehicle_norm.keys()], 'Norma': [value for value in vehicle_norm.values()]})
                    temp_data = temp_data.merge(temp_data_norm, how='left', on=st.session_state.vehicle_column)
                    temp_data['Spalanie średnia/norma +/-'] = temp_data.apply(lambda row: row.Norma - row.Spalanie if row.Norma > 0 else row['Spalanie średnia +/-'], axis=1)
            with after_section:
                if apply_new_norm:
                    st.session_state['data_set_norms'] = temp_data
                if 'data_set_norms' in st.session_state:
                    st.caption("Tabela zawiera dodatkowe kolumny określające przyjęte normy i różnice między nimi a poziomem zużycia paliwa")
                    st.write(temp_data)

            if 'data_set_norms' in st.session_state:
                temp_data = st.session_state.data_set_norms

            st.divider()

            st.subheader("Wizualizacja podstawowych danych z wybranego zakresu danych")
            st.caption("Nie uwzględnia danych wyłączonych z analizy")

            n_col, sort_col = st.columns(2, gap="medium")
            with n_col:
                n_item = st.slider(label="Ogranicz widoczność do n pozycji", min_value=1, max_value=temp_data[st.session_state.vehicle_column].nunique(), value=5)
            with sort_col:
                sort_type = st.select_slider(label="Typ sortowania", options=["rosnąco", "malejąco"], key="sorting_type")
            if st.session_state.sorting_type == "rosnąco":
                sort_type = True
                color_type = '#387478'
            elif st.session_state.sorting_type == "malejąco":
                sort_type = False
                color_type = '#A04747'

            if manual_true or "param_limits" in st.session_state:
                with st.container():
                    st.subheader("Poziom zużycia paliwa")
                    mean, min, max, std = st.columns(4, gap="medium")
                    with mean:
                        st.write("Średnia zużycia paliwa w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.consumption_column].mean().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with min:
                        st.write("Minimalne zużycia paliwa w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.consumption_column].min().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with max:
                        st.write("Maksymalne zużycia paliwa w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.consumption_column].max().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with std:
                        st.write("Odchylenie standardowe zużycia paliwa w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.consumption_column].std().sort_values(ascending=sort_type)[:n_item], color='#FEFFA7')

                with st.container():
                    st.subheader("Ilość zrealizowanych wozokilometrów")
                    mean, min, max, std = st.columns(4, gap="medium")
                    with mean:
                        st.write("Średnia zrealizowanych kilometrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].mean().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with min:
                        st.write("Minimalna wartość zrealizowanych kilometrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].min().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with max:
                        st.write("Maksymalna wartość zrealizowanych kilometrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].max().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with std:
                        st.write("Odchylenie standardowe kilometrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)['Kilometry'].std().sort_values(ascending=sort_type)[:n_item], color='#FEFFA7')

                with st.container():
                    st.subheader("Ilość zatankowanych litrów paliwa")
                    mean, min, max, std = st.columns(4, gap="medium")
                    with mean:
                        st.write("Średnia zatankowanych litrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].mean().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with min:
                        st.write("Minimalna ilość zatankowanych litrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].min().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with max:
                        st.write("Maksymalna ilość zatankowanych litrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].max().sort_values(ascending=sort_type)[:n_item], color=color_type)
                    with std:
                        st.write("Odchylenie standardowe litrów w okresie")
                        st.bar_chart(data=temp_data.groupby(st.session_state.vehicle_column)[st.session_state.fuel_column].std().sort_values(ascending=sort_type)[:n_item], color='#FEFFA7')

                st.data_editor(
                    temp_data,
                    column_order=['Czas zdarzenia', 'Dni rozliczeniowe',
                                  st.session_state.vehicle_column, st.session_state.km_column,
                                  st.session_state.fuel_column,
                                  'Kilometry', 'Spalanie', 'Spalanie średnia', 'Spalanie średnia +/-', 'Norma',
                                  'Spalanie średnia/norma +/-'],
                    column_config={
                        "Czas zdarzenia": st.column_config.DateColumn(
                            "Czas zdarzenia",
                            help="Czas rejestrowanego zdarzenia, najczęściej procesu tankowania pojazdu",
                            format="D MMM YYYY, h:mm a"
                        ),
                        "Kilometry": st.column_config.NumberColumn(
                            "Wozokilometry",
                            help="Zrealizowane wozokilometry w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%d wzkm"
                        ),
                        "Spalanie": st.column_config.NumberColumn(
                            "Spalanie",
                            help="Poziom zużycia paliwa w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%.2f l / 100 wzkm"
                        ),
                        "Spalanie średnia": st.column_config.ProgressColumn(
                            "Spalanie średnia",
                            help="Średnia zużycia paliwa w okresie",
                            format="%.2f l / 100 wzkm",
                            min_value=0,
                            max_value= temp_data['Spalanie średnia'].max()
                        ),
                        "Spalanie średnia +/-": st.column_config.NumberColumn(
                            "Spalanie średnia +/-",
                            help="Różnica między poziomem zużycia paliwa a średnią zużycia paliwa w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%.2f l / 100 wzkm"
                        ),
                        "Spalanie średnia/norma +/-": st.column_config.NumberColumn(
                            "Spalanie średnia/norma +/-",
                            help="Różnica między poziomem zużycia paliwa a wyznaczoną normą lub średnią zużycia paliwa jeśli norma nie została wyznaczona w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%.2f l / 100 wzkm"
                        ),
                        "Norma": st.column_config.NumberColumn(
                            "Norma spalania",
                            help="Norma zużycia paliwa wyznaczona w poprzednich krokach",
                            format="%.2f l / 100 wzkm"
                        ),
                        st.session_state.fuel_column: st.column_config.NumberColumn(
                            "Ilość paliwa",
                            help="Ilość paliwa zatankowanego podczas obecnie rejestrowanego zdarzenia",
                            format="%d l"
                        ),
                        st.session_state.vehicle_column: st.column_config.TextColumn(
                            "Pojazd",
                            help="Identyfikator pojazdu"
                        ),
                        st.session_state.km_column: st.column_config.NumberColumn(
                            "Stan licznika",
                            help="Stan licznika podczas obecnie rejestrowanego zdarzenia",
                        )
                    },
                    hide_index=True
                )

                st.divider()

                if manual_true or "param_limits" in st.session_state:
                    st.subheader("Wizualizacja podstawowych danych wybranego zakresu i pojazdu")
                    selected_vehicle = st.selectbox(label="Wybierz pojazd do analizy parametrów", options=temp_data[st.session_state.vehicle_column].unique())
                    consumption, fuel, km = st.columns(3, gap="medium")

                    with consumption:
                        id_max_consumption = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index(['Czas zdarzenia'])[st.session_state.consumption_column].idxmax()
                        max_consumption = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index('Czas zdarzenia')[st.session_state.consumption_column].max()
                        id_min_consumption = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index(['Czas zdarzenia'])[st.session_state.consumption_column].idxmin()
                        min_consumption = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index('Czas zdarzenia')[st.session_state.consumption_column].min()

                        st.line_chart(data=temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle], x = 'Czas zdarzenia', y = st.session_state.consumption_column)

                        st.write(f"Poziom zużycia paliwa pojazdu {selected_vehicle}")
                        st.metric(label = f"Maksymalny poziom zużycia paliwa wystąpił {id_max_consumption}",value = value_separator(max_consumption), delta=value_separator(max_consumption-min_consumption))
                        st.metric(label=f"Minimalny poziom zużycia paliwa wystąpił {id_min_consumption}",value=value_separator(min_consumption), delta=value_separator(min_consumption-max_consumption))

                    with fuel:
                        id_max_fuel = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index(['Czas zdarzenia'])[st.session_state.fuel_column].idxmax()
                        max_fuel = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index('Czas zdarzenia')[st.session_state.fuel_column].max()
                        id_min_fuel = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index(['Czas zdarzenia'])[st.session_state.fuel_column].idxmin()
                        min_fuel = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index('Czas zdarzenia')[st.session_state.fuel_column].min()

                        st.line_chart(data=temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle], x = 'Czas zdarzenia', y = st.session_state.fuel_column)

                        st.write(f"Liczba zatankowanego paliwa do pojazdu {selected_vehicle}")
                        st.metric(label=f"Maksymalna ilość zatankowanego paliwa wystąpiła {id_max_fuel}",value=value_separator(max_fuel), delta=value_separator(max_fuel-min_fuel))
                        st.metric(label=f"Minimalna ilość zatankowanego paliwa wystąpiła {id_min_fuel}",value=value_separator(min_fuel), delta=value_separator(min_fuel-max_fuel))

                    with km:
                        id_max_distance = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index(['Czas zdarzenia'])['Kilometry'].idxmax()
                        max_distance = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index('Czas zdarzenia')['Kilometry'].max()
                        id_min_distance = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index(['Czas zdarzenia'])['Kilometry'].idxmin()
                        min_distance = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle].set_index('Czas zdarzenia')['Kilometry'].min()

                        st.line_chart(data=temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle], x = 'Czas zdarzenia', y = 'Kilometry')

                        st.write(f"Liczba zrealizowanych kilometrów pojazdu {selected_vehicle}")
                        st.metric(label=f"Maksymalna ilość zrealizowanych kilometrów wystąpiła {id_max_distance}",
                        value=value_separator(max_distance), delta = value_separator(max_distance-min_distance))
                        st.metric(label=f"Minimalna ilość zrealizowanych kilometrów wystąpiła {id_min_distance}",
                        value=value_separator(min_distance), delta=value_separator(min_distance-max_distance))

                    data_df = temp_data[temp_data[st.session_state.vehicle_column] == selected_vehicle]
                    st.data_editor(
                        data_df,
                        column_order= ['Czas zdarzenia', 'Dni rozliczeniowe',
                                   st.session_state.vehicle_column, st.session_state.km_column, st.session_state.fuel_column,
                                   'Kilometry', 'Spalanie', 'Spalanie średnia', 'Spalanie średnia +/-', 'Norma', 'Spalanie średnia/norma +/-'],
                        column_config={
                        "Czas zdarzenia": st.column_config.DateColumn(
                            "Czas zdarzenia",
                            help="Czas rejestrowanego zdarzenia, najczęściej procesu tankowania pojazdu",
                            format="D MMM YYYY, h:mm a"
                        ),
                        "Kilometry": st.column_config.NumberColumn(
                            "Wozokilometry",
                            help="Zrealizowane wozokilometry w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%d wzkm"
                        ),
                        "Spalanie": st.column_config.NumberColumn(
                            "Spalanie",
                            help="Poziom zużycia paliwa w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%.2f l / 100 wzkm"
                        ),
                        "Spalanie średnia": st.column_config.NumberColumn(
                            "Spalanie średnia",
                            help="Średnia zużycia paliwa w okresie",
                            format="%.2f l / 100 wzkm"
                        ),
                        "Spalanie średnia +/-": st.column_config.NumberColumn(
                            "Spalanie średnia +/-",
                            help="Różnica między poziomem zużycia paliwa a średnią zużycia paliwa w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%.2f l / 100 wzkm"
                        ),
                        "Spalanie średnia/norma +/-": st.column_config.NumberColumn(
                            "Spalanie średnia/norma +/-",
                            help="Różnica między poziomem zużycia paliwa a wyznaczoną normą lub średnią zużycia paliwa jeśli norma nie została wyznaczona w okresie od poprzedniego zdarzenia do obecnie rejestrowanego",
                            format="%.2f l / 100 wzkm"
                        ),
                        "Norma": st.column_config.NumberColumn(
                            "Norma spalania",
                            help="Norma zużycia paliwa wyznaczona w poprzednich krokach",
                            format="%.2f l / 100 wzkm"
                        ),
                        st.session_state.fuel_column: st.column_config.NumberColumn(
                            "Ilość paliwa",
                            help="Ilość paliwa zatankowanego podczas obecnie rejestrowanego zdarzenia",
                            format="%d l"
                        ),
                        st.session_state.vehicle_column: st.column_config.TextColumn(
                            "Pojazd",
                            help="Identyfikator pojazdu"
                        ),
                        st.session_state.km_column: st.column_config.NumberColumn(
                            "Stan licznika",
                            help="Stan licznika podczas obecnie rejestrowanego zdarzenia",
                        )
                    },
                    hide_index=True
                )