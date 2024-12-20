import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
import os
ruta_credenciales = os.path.join(os.path.dirname(__file__), "credentials.json")

# Configurar la autenticación con Google Sheets API
def autenticar_cliente():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(ruta_credenciales, scopes=scope)
    client = gspread.authorize(creds)
    return client

# Obtener datos ajustados para una hoja específica
def obtener_datos_google_sheets(spreadsheet_id, sheet_name, skiprows, usecols, column_names):
    client = autenticar_cliente()
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Obtener todos los valores como lista de listas
        rows = worksheet.get_all_values()
        
        # Aplicar skiprows
        rows = rows[skiprows:]

        # Crear DataFrame con encabezados personalizados
        df = pd.DataFrame(rows, columns=column_names[:len(rows[0])])

        # Filtrar columnas relevantes
        df = df[usecols]

        # Eliminar filas completamente vacías
        df = df.dropna(how='all')

        # Agregar nombre de la hoja
        df["Hoja"] = sheet_name

        print(f"Datos procesados exitosamente de la hoja: {sheet_name}")
        return df
    except Exception as e:
        print(f"Error al procesar la hoja '{sheet_name}': {e}")
        return None

# Procesar datos de múltiples hojas relevantes
def procesar_data_google_sheets(spreadsheet_id):
    # Columnas y configuraciones para hojas específicas
    sheet_config = {
        "Movimientos internos": {
            "skiprows": 10,
            "usecols": column_names,
            "column_names": column_names,
        },
        "Fletes Subcontratos": {
            "skiprows": 10,
            "usecols": column_names,
            "column_names": column_names,
        },
        "Fletes TF": {
            "skiprows": 10,
            "usecols": column_names,
            "column_names": column_names,
        },
    }

    combined_data = []

    for sheet_name, config in sheet_config.items():
        df = obtener_datos_google_sheets(
            spreadsheet_id,
            sheet_name,
            skiprows=config["skiprows"],
            usecols=config["usecols"],
            column_names=config["column_names"],
        )
        if df is not None:
            combined_data.append(df)

    # Combinar los DataFrames en uno solo
    final_dataframe = pd.concat(combined_data, ignore_index=True)

    final_dataframe["CLP $"] = (
        final_dataframe["CLP $"]
        .replace("", np.nan)  # Reemplazar valores vacíos con NaN
        .str.replace("[$,]", "", regex=True)  # Eliminar símbolos de moneda y separadores
        .astype(float)  # Convertir a tipo float
    )
    # Asegúrate de que todas las fechas estén en el formato correcto
    return final_dataframe

# Procesar datos específicos de la hoja "MODULOS"
def procesar_data_modulos_google_sheets(spreadsheet_id):
    column_names_modulos = [
        "N° DE SERIE",
        "EDIFICIO",
        "TIPO",
        "PISO",
        "TRAMO",
        "TRANSPORTISTA",
        "CONDUCTOR",
        "P-CAMION",
        "TIPO RAMPLA",
        "N° DE GUIA",
        "FECHA DESPACHO",
        "VALOR FLETE",
        "N° EDP",
        "N° OC",
        "Despacho",
        "Observación"
    ]

    try:
        df_modulos = obtener_datos_google_sheets(
            spreadsheet_id,
            "MODULOS",
            skiprows=5,
            usecols=column_names_modulos,
            column_names=column_names_modulos,
        )

        # Limpiar "N° DE SERIE"
        df_modulos["N° DE SERIE"] = df_modulos["N° DE SERIE"].astype(str).str.strip()
        df_modulos = df_modulos[df_modulos["N° DE SERIE"] != ""]
        df_modulos = df_modulos.dropna(subset=["N° DE SERIE"])
        df_modulos["VALOR FLETE"] = (
            df_modulos["VALOR FLETE"]
            .replace("", np.nan)  # Reemplazar valores vacíos con NaN
            .str.replace("[$,]", "", regex=True)  # Eliminar símbolos de moneda y separadores
            .astype(float)  # Convertir a tipo float
        )
        print("Datos de la hoja 'MODULOS' procesados exitosamente.")
        return df_modulos
    except Exception as e:
        print(f"Error al procesar la hoja 'MODULOS': {e}")
        return None

# Configuración del ID del Google Sheet
spreadsheet_id = "1Kl_5ufWDBFkhiyfvKOLpEtuCRlVMO5FEnU3WRX0PGQ8"

# Configuración de columnas esperadas
column_names = [
    "Item", "Fecha", "CC", "Ruta", "Proyecto", "Origen", "Destino", "Tipo de Carga", 
    "Detalle", "Transportista", "Chofer", "Rut", "N° Contacto", "P-CAMION", 
    "N° Guia Tecno Fast", "N° Guias Proveedor", "Comentarios",
    "CLP $", "N° Etp", "N° OC", "Wip"
]

data_general = procesar_data_google_sheets(spreadsheet_id)
data_modulos = procesar_data_modulos_google_sheets(spreadsheet_id)
data_general.head()



