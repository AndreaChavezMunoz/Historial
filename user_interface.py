import streamlit as st
from buscar_productos import  search_file, open_productos_cotizados
import pandas as pd
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import streamlit as st
import  streamlit_toggle as tog
import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect
from datetime import date

@st.cache_data
def leer_base_de_datos():
    df = open_productos_cotizados()
    return df

# Transform to xlswriter
def convert_to_df(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.close()
    processed_data = output.getvalue()

    return processed_data

st.title(":mag_right: Busqueda rapida de historial")

url = "https://docs.google.com/presentation/d/e/2PACX-1vRxIH1g79XGMuPjjbGYqschgNEZjBJwznruzzvwNypR_HGJvzDyt2QEOKcAn5UI98Jt6RqotL2vTXyv/pub?start=false&loop=false&delayms=5000"
st.write("Mira el tutorial aqui [aqui](%s)" % url)

# Buscar datos
file_path = st.file_uploader("Sube los datos de planilla", ['xlsx','xls'])

if file_path is not None:

    productos_cotizados = leer_base_de_datos()
    resultados_trazas = search_file(file_path, productos_cotizados)

    st.dataframe(resultados_trazas)


    # Download file
    xlsx = convert_to_df(resultados_trazas)
    try:
        name = file_path.name.split("--")[1]
        name = name.split("Planilla")[0]
    except:
        name = "Productos_encontrados"

    st.download_button(
    "Descargar productos de historial encontrados",
    xlsx,
    f"ProductosHistorial_{name}.xlsx",
    "text/xlsx",
    key='download-csv'
    )

