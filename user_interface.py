import streamlit as st
from buscar_productos import  search_file
import pandas as pd
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import streamlit as st
import buscar_productos as bp
import  streamlit_toggle as tog
import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect


# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        'https://www.googleapis.com/auth/drive'
    ],
)

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

st.title("Busqueda rapida de historial")
toggle = tog.st_toggle_switch(label="Modo", 
                    key="Key1", 
                    default_value=False, 
                    label_after = False, 
                    inactive_color = '#D3D3D3', 
                    active_color="#11567f", 
                    track_color="#29B5E8"
                    )

if toggle:
    st.header(':mailbox: Actualizar base de datos')
    # Boton para actualizar datos 
    _ = st.file_uploader("Ingresa tus credenciales")

    if credentials is not None:
        run(credentials)
        st.write("Datos actualizados")

else:
    # Buscar datos
    st.header(':mag_right: Buscar productos cotizados')
    file_path = st.file_uploader("Sube los datos de planilla", ['xlsx','xls'])

    if file_path is not None:
        resultados_trazas = search_file(file_path)

        st.dataframe(resultados_trazas)


        # Download file
        xlsx = convert_df(resultados_trazas)
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

