# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import pandas as pd
import requests
import streamlit as st
from tqdm import tqdm
from io import BytesIO

# Configuración inicial y credenciales desde variables de entorno
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')
GRANT_TYPE = 'password'
TOKEN_URL = 'https://ruesapi.rues.org.co/Token'

# Verificar que las credenciales están configuradas
if not USERNAME or not PASSWORD:
    st.error("Las variables de entorno 'API_USERNAME' y 'API_PASSWORD' no están configuradas.")
    st.stop()

# Función para obtener el token
def obtener_token():
    data = {
        'username': USERNAME,
        'password': PASSWORD,
        'grant_type': GRANT_TYPE,
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_info = response.json()
        return token_info.get('access_token')
    else:
        st.error("Error al obtener el token. Verifica las credenciales.")
        return None

# Función para realizar la consulta por NIT
def consultar_nits(file_path, access_token):
    NITS = pd.read_excel(file_path)

    # Verificar que el archivo tiene la columna esperada
    if 'NIT sin digito' not in NITS.columns:
        st.error("El archivo debe contener una columna llamada 'NIT sin digito'.")
        return pd.DataFrame()

    resultados_temporales = []

    for _, row in tqdm(NITS.iterrows(), total=NITS.shape[0]):
        try:
            nit_a_consultar = int(row['NIT sin digito'])
            consulta_url = f"https://ruesapi.rues.org.co/api/consultasRUES/ConsultaNIT?usuario=pruebas&nit={nit_a_consultar}"
            headers = {'Authorization': f'Bearer {access_token}'}

            consulta_response = requests.post(consulta_url, headers=headers)
            if consulta_response.status_code == 200:
                json_data = consulta_response.json()
                registros = json_data.get('registros', [])
                df = pd.json_normalize(registros)
                resultados_temporales.append(df)
            else:
                st.warning(f"Error al consultar el NIT {nit_a_consultar}: {consulta_response.status_code}")
        except Exception as e:
            st.warning(f"Error con el NIT {nit_a_consultar}: {e}")

    if resultados_temporales:
        return pd.concat(resultados_temporales, axis=0, ignore_index=True)
    else:
        return pd.DataFrame()

# Interfaz de Streamlit
st.title("Consulta de NITs desde Excel")

uploaded_file = st.file_uploader("Cargar archivo Excel con NITs a Consultar", type=["xlsx"])
if uploaded_file is not None:
    access_token = obtener_token()
    if access_token:
        df = consultar_nits(uploaded_file, access_token)
        if not df.empty:
            st.write(df)

            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.download_button(
                label="Descargar archivo procesado",
                data=output,
                file_name="archivo_procesado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
