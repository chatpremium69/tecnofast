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
    sheet_relevant = ["Fletes TF"]

    # Crear una lista para almacenar los DataFrames
    combined_data = []

    # Procesar cada hoja
    for sheet in sheet_relevant:
        # Leer la hoja, comenzando desde la fila 11 (índice 10 en pandas) y solo columnas A-V
        df = pd.read_excel(file_path, sheet_name=sheet, skiprows=10, usecols="A:V", names=column_names)
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Agregar columna con el nombre de la hoja
        df["Hoja"] = sheet
        
        # Agregar al conjunto combinado
        combined_data.append(df)

    # Combinar los DataFrames en uno solo
    final_dataframe = pd.concat(combined_data, ignore_index=True)
    return final_dataframe


