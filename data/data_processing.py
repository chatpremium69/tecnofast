import pandas as pd
import os
import openpyxl

# Construir ruta al archivo Excel
file_path = 'Control y registro de misceláneos proyecto Centinela.xlsx'

# Lista de títulos esperados
column_names = [
    "Item", "Fecha", "CC", "Ruta", "Proyecto", "Origen", "Destino", "Tipo de Carga", 
    "Detalle", "Transportista", "Chofer", "Rut", "N° Contacto", "P-Camion", 
    "N° Guia Tecno Fast", "N° Guias Proveedor", "Comentarios", "%Ocupación", 
    "CLP $", "N° Etp", "N° OC", "Wip"
]

def procesar_data(file_path):
    # Especificar las hojas relevantes
    sheet_relevant = ["Movimientos internos", "Fletes Subcontratos", "Fletes TF"]

    # Crear una lista para almacenar los DataFrames
    combined_data = []

    # Procesar cada hoja
    for sheet in sheet_relevant:
        df = pd.read_excel(file_path, sheet_name=sheet, skiprows=10, usecols="A:V", names=column_names,engine="openpyxl" )
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Agregar columna con el nombre de la hoja
        df["Hoja"] = sheet
        
        # Agregar al conjunto combinado
        combined_data.append(df)

    # Combinar los DataFrames en uno solo
    final_dataframe = pd.concat(combined_data, ignore_index=True)
    return final_dataframe

def procesar_data_modulos(file_path):
    column_names = [
        "N° DE SERIE",
        "EDIFICIO",
        "PISO",
        "TRAMO",
        "TRANSPORTISTA",
        "CONDUCTOR",
        "P-CAMION",
        "N° DE GUIA",
        "FECHA DESPACHO",
        "VALOR FLETE",
        "N° EDP",
        "N° OC",
        "Observación"
    ]
    # Especificar las hojas relevantes
    sheet_relevant = ["MODULOS"]

    # Crear una lista para almacenar los DataFrames
    combined_data = []

    # Procesar cada hoja
    for sheet in sheet_relevant:
        df = pd.read_excel(file_path, sheet_name=sheet, skiprows=9, usecols="A:M", names=column_names, engine="openpyxl")
        
        # Limpiar y convertir la columna "N° DE SERIE" a string para evitar problemas
        df["N° DE SERIE"] = df["N° DE SERIE"].astype(str).str.strip()

        # Eliminar filas donde "N° DE SERIE" sea vacío o nulo
        df = df[df["N° DE SERIE"] != ""]
        df = df.dropna(subset=["N° DE SERIE"])

        # Agregar columna con el nombre de la hoja
        df["Hoja"] = sheet

        # Agregar al conjunto combinado
        combined_data.append(df)

    # Combinar los DataFrames en uno solo
    final_dataframe = pd.concat(combined_data, ignore_index=True)
    return final_dataframe



