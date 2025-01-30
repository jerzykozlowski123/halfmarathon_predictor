import streamlit as st
import pandas as pd
import json
import os
from dotenv import load_dotenv
from langfuse.decorators import observe
from langfuse.openai import OpenAI
import boto3

st.set_page_config("Szklana kula AI", menu_items={"About": "Szklana kula AI - Półmaraton by JK"})
st.title('Szklana Kula AI - Półmaraton')

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    endpoint_url=os.getenv("AWS_ENDPOINT_URL_S3"),
)
BUCKET_NAME="jurek"

@st.cache_resource
@observe(name="dane_biegacza")
def generate_description(opis):
    """
    AI generuje parametry dla biegacza
    """
    try:
        messages = [
            {
                "role": "system",
                "content": """ 
                    Wyłuskaj z tekstu: płeć ('K' dla kobiety, 'M' dla mężczyzny), wiek (liczba) oraz poziom sportowy (1-10). 
                    Brakujące informacje podaj jako 'None'. 
                    Odpowiedź w formacie JSON, wzór: {"plec": "K", "wiek": None, "poziom": 5}. 
                    Jeśli poziom sportowy jest opisowy, przypisz wartość 1-10 (1 - nie biega, 10 - zawodowiec). 
                    Jeśli podany wiek jest niższy niż 16 lat lub wyższy niż 100 lat - zwróć None. 
                """
            },
            {"role": "user", "content": opis},
        ]
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0,
        )
        result = json.loads(response.choices[0].message.content)
        return {
                "plec": result.get("plec", None),
                "wiek": result.get("wiek", None),
                "poziom": result.get("poziom", None),
        }
    except Exception:
            return {"plec": None, "wiek": None, "poziom": None}

# Sprawdzanie, czy przycisk został naciśnięty
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

def on_button_click():
    st.session_state.submitted = True

@st.cache_resource
def get_data():
    df = pd.read_csv(f"s3://{BUCKET_NAME}/halfmarathons/dane_biegaczy.csv", sep=";")
    return df

df = get_data()

st.session_state['opis'] = st.text_area("Przedstaw się i powiedz jaka jest twoja płeć, wiek i poziom sportowy lub doświadczenie biegowe:", max_chars=500)

biegacze_grupy = {
    10: {"nazwa": "Mistrzem", "opis": "Biegacze, którzy osiągają doskonałe wyniki. Trenują intensywnie i regularnie, przechodząc przez zaawansowane techniki treningowe. Ich czas na półmaratonie jest naprawdę imponujący, a każdy bieg to dla nich wyzwanie na najwyższym poziomie."},
    9: {"nazwa": "Zaawansowanym", "opis": "Osoby, które biegają na bardzo wysokim poziomie, trenują z planem ich wyniki są bliskie czołowej części stawki. Wiedzą, jak osiągać swoje cele treningowe i mają doświadczenie w rywalizacji na różnych dystansach."},
    8: {"nazwa": "Treningowcem", "opis": "Biegacze, którzy osiągają solidne wyniki, regularnie biegają, trenują w systemie i podchodzą do półmaratonu z odpowiednią motywacją. Mają duże doświadczenie, choć jeszcze nie są w ścisłej czołówce."},
    7: {"nazwa": "Ambitnym Biegaczem", "opis": "Ci, którzy traktują bieganie jako ważną część swojego życia. Trenują regularnie, choć niekoniecznie w pełni profesjonalnie. Zawsze dążą do poprawy swoich wyników i cieszą się z osiągnięć."},
    6: {"nazwa": "Zaawansowanym Amatorem", "opis": "Biegacze, którzy systematycznie pracują nad poprawą wyników, ale nie są zawodowcami. Ich treningi mają na celu poprawę kondycji i wytrzymałości, z uwagą na szczegóły."},
    5: {"nazwa": "Zdeterminowany", "opis": "Ci, którzy traktują półmaraton jako duże wyzwanie. Często biegają, ale ich treningi mogą być mniej regularne. Niezależnie od wyników, mają silną wolę i dążą do samodoskonalenia."},
    4: {"nazwa": "Biegaczem Na Start", "opis": "Amatorzy, którzy rozpoczęli swoją biegową przygodę. Ich treningi są wciąż na etapie budowania bazy, ale wytrwale pracują nad poprawą wyników. Ich celem jest ukończenie półmaratonu w dobrym czasie."},
    3: {"nazwa": "Mocnym Pod Prąd", "opis": "Osoby, które traktują każdy bieg jako osobne wyzwanie. Często stawiają na treningi, ale ich wyniki jeszcze nie są imponujące. Mają silną wolę i nie boją się trudności."},
    2: {"nazwa": "Nowym Biegaczem", "opis": "Ci, którzy dopiero zaczynają swoją przygodę z bieganiem. Ich treningi są sporadyczne, ale ich zaangażowanie jest duże. Cieszą się z każdego przebiegniętego kilometra i dążą do ukończenia biegu."},
    1: {"nazwa": "Wychodzącym z Strefy Komfortu", "opis": "Biegacze, którzy zaczynają biegać zaledwie od kilku miesięcy. Trenują na początku, próbując pokonać swoje słabości. Są na etapie budowania kondycji i nie spodziewają się jeszcze rewelacyjnych wyników, ale dążą do pokonania własnych granic."},
}

# Przycisk, który ustawia stan 'submitted'
st.button("Wyślij opis do AI", disabled=not st.session_state["opis"].strip(), on_click=on_button_click, use_container_width=True)

# Dalszy kod, który czeka na kliknięcie przycisku
if st.session_state['submitted']:
    opis = st.session_state["opis"]
    dane_biegacza = generate_description(opis)  # Przykładowa funkcja

    st.write(
        "Sztuczna inteligencja jest dosyć bystra, ale jeszcze nie potafi zgadnąć wszystkiego. "
        "Proszę sprawdź i popraw poniższe dane, a zobaczysz w jakim czasie możesz przebiec półmaraton."
        )

    # Użytkownik wybiera dane
    st.subheader("Sprawdź i popraw swoje dane:")

    wiek = st.number_input("Wiek:", min_value=16, max_value=100, step=1, value=dane_biegacza["wiek"] or 32)
    plec = st.selectbox("Płeć:", ["Kobieta", "Mężczyzna"], index=0 if dane_biegacza["plec"] == "K" else 1)
    poziom = st.slider("Poziom wytrenowania:", min_value=1, max_value=10, value=dane_biegacza["poziom"] or 5)

    if wiek < 20:
        user_category = "K20" if plec == "K" else "M20"
    else:
        user_category = f"K{wiek // 10 * 10}" if plec == "K" else f"M{wiek // 10 * 10}"

    user_data = df[(df['Kategoria wiekowa'] == user_category) & (df['Poziom wytrenowania'] == poziom)]

    # Wyniki dla użytkownika
    if len(user_data) > 0:
        avg_czas = user_data['Czas'].mean()
        avg_czas_h = int(avg_czas // 3600)
        avg_czas_m = int((avg_czas % 3600) // 60)
        avg_czas_s = int(avg_czas % 60)

        avg_5km = user_data['5 km Czas'].mean()
        avg_5km_h = int(avg_5km // 3600)
        avg_5km_m = int((avg_5km % 3600) // 60)
        avg_5km_s = int(avg_5km % 60)

        grupa = biegacze_grupy[poziom]
        st.subheader(f"Według AI jesteś {grupa['nazwa']}")
        st.write(grupa['opis'])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Przewidywany czas półmaratonu:")
            st.metric(label="Czas maratonu", label_visibility="collapsed", value=f"{avg_czas_h:02}:{avg_czas_m:02}:{avg_czas_s:02}")
        with col2:
            st.markdown("#### Średni czas na pierwszych 5 km:")
            st.metric(label="Czas na 5 km", label_visibility="collapsed", value=f"{avg_5km_h:02}:{avg_5km_m:02}:{avg_5km_s:02}")
    else:
        st.warning("Brak danych dla wybranego wieku, płci i poziomu wytrenowania.")
else:
    st.write("")

# Footer
footer_style = """
    <style>
        .footer {
            bottom: 0;
            left: 0;
            right: 0;
            background-color: transparent;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            border-top: 1px solid #e7e7e7;
            color: inherit;
        }
        body {
            padding-bottom: 50px;  /* Zapewnienie miejsca na stopkę */
        }
    </style>
"""

footer_html = """
<div class="footer">
    <p>Contact: Jerzy Kozlowski | <a href="mailto:jerzykozlowski@mailmix.pl">jerzykozlowski@mailmix.pl</a></p>
</div>
"""

st.markdown(footer_style, unsafe_allow_html=True)
st.markdown(footer_html, unsafe_allow_html=True)