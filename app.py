
from flask import Flask, render_template, request, send_file
import webbrowser
from threading import Timer 
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib
import io
import base64
from werkzeug.utils import secure_filename
from data import data_processing
from generar_informe import generar_informe
matplotlib.use("Agg")  # Configura el backend para evitar errores de GUI
import traceback

app = Flask(__name__)

# Configurar estilos globales de Matplotlib
plt.style.use("ggplot")

# Variable global para almacenar las imágenes de KPI
kpi_images_global = None
kpi_images_global_1 = None

@app.route("/", methods=["GET", "POST"])
def dashboard():
    global kpi_images_global
    global kpi_images_global_1

    file_path = "1Kl_5ufWDBFkhiyfvKOLpEtuCRlVMO5FEnU3WRX0PGQ8"
    start_date = pd.Timestamp("2001-01-01")  # Rango inicial por defecto
    end_date = pd.Timestamp("today")  # Fecha final por defecto

    filtered_data = pd.DataFrame()  # DataFrame vacío para inicializar
    filtered_data_1 = pd.DataFrame()

    if request.method == "POST":
        if "filter_all" in request.form:  # Si se presiona "Mostrar Todo"
            start_date = pd.Timestamp("2001-01-01")
            end_date = pd.Timestamp("today")
        else:
            form_start_date = request.form.get("start_date")
            form_end_date = request.form.get("end_date")
            if form_start_date and form_end_date:
                try:
                    start_date = pd.to_datetime(form_start_date)
                    end_date = pd.to_datetime(form_end_date)
                except Exception as e:
                    return render_template("error.html", message=f"Error en las fechas: {str(e)}")

    try:
        # Procesar los datos
        data = data_processing.procesar_data_google_sheets(file_path)
        data_1 = data_processing.procesar_data_modulos_google_sheets(file_path)

        # Validar la existencia de las columnas de fechas antes de filtrar
        if "Fecha" in data.columns:
            data["Fecha"] = pd.to_datetime(data["Fecha"], errors="coerce")
            if not data["Fecha"].isna().all():
                filtered_data = data.loc[
                    (data["Fecha"] >= start_date) & (data["Fecha"] <= end_date)
                ]
                print(filtered_data)
                filtered_data.dropna(subset = ["CLP $", "N° Etp"])
                filtered_data = filtered_data[filtered_data["CLP $"].astype(str).str.strip() != ""]
                filtered_data = filtered_data[filtered_data["N° Etp"].astype(str).str.strip() != ""]
                print(filtered_data)

        if "FECHA DESPACHO" in data_1.columns:
            data_1["FECHA DESPACHO"] = pd.to_datetime(data_1["FECHA DESPACHO"], errors="coerce")
            if not data_1["FECHA DESPACHO"].isna().all():
                filtered_data_1 = data_1.loc[
                    (data_1["FECHA DESPACHO"] >= start_date) & (data_1["FECHA DESPACHO"] <= end_date)
                ]
                print(filtered_data_1)
                print(filtered_data_1.empty)

        # Validar si los DataFrames tienen datos válidos
        if filtered_data.empty and filtered_data_1.empty:
            return render_template(
                "error.html",
                message="No hay datos disponibles para el rango de fechas seleccionado.",
            )

        # Limpiar datos adicionales en filtered_data_1 si existen
        if not filtered_data_1.empty and "N° EDP" in filtered_data_1.columns:
            print(filtered_data_1)
            filtered_data_1 = filtered_data_1.dropna(subset=["N° EDP"])
            filtered_data_1 = filtered_data_1[filtered_data_1["N° EDP"].astype(str).str.strip() != ""]
            print(filtered_data_1)

        # Generar gráficos condicionalmente

        kpi_images_global = generar_kpi_graficos(filtered_data) if not filtered_data.empty else None
        kpi_images_global_1 = generar_kpi_graficos_1(filtered_data_1, data_1) if not filtered_data_1.empty else None

    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", message=f"Error al procesar o filtrar los datos: {str(e)}")



    # Renderizar solo los datos disponibles
    return render_template(
        "dashboard.html",
        filtered_table=filtered_data.to_html(classes="table table-striped", index=False) if not filtered_data.empty else None,
        kpi_images=kpi_images_global if not filtered_data.empty else None,
        filtered_table_1=filtered_data_1.to_html(classes="table table-striped", index=False) if not filtered_data_1.empty else None,
        kpi_images_1=kpi_images_global_1 if not filtered_data_1.empty else None,
    )





def generar_kpi_graficos(filtered_data):
    """Genera gráficos mejorados y devuelve imágenes en formato base64."""
    kpi_images = {}
    print("0")



    # 1. Gráfico Circular: Distribución por Tipo de Carga
    if "Wip" in filtered_data.columns:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
        data = filtered_data["Wip"].value_counts()
        categorias = data.index

        # Generar colores dinámicamente
        colores = generar_colores(categorias)
        wedges, texts, autotexts = plt.pie(data, autopct="%1.1f%%", colors=colores,
                                          textprops=dict(color="white"), startangle=140)
        plt.title("Distribución de Transporte por Tipo de Carga", fontsize=14, color="white")

        # Ajustar etiquetas fuera del gráfico
        plt.legend(wedges, data.index, title="Tipos de Carga", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)

        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")

        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["tipo_carga"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()
        print("1")


    # 2. Gráfico Circular: Suma de CLP $ por Tipo de Carga
    if "Wip" in filtered_data.columns and "CLP $" in filtered_data.columns:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
        print(1.1)
        
        # Agrupar por Tipo de Carga y sumar CLP $
        data = filtered_data.groupby("Wip")["CLP $"].sum()
        
        categorias = data.index

        # Generar colores dinámicamente
        colores = generar_colores(categorias)

        # Crear el gráfico circular
        wedges, texts, autotexts = plt.pie(
            data, 
            autopct=lambda p: f'{p:.1f}%' if p > 0 else '',  # Solo muestra porcentajes mayores a 0
            colors=colores,
            textprops=dict(color="white"),
            startangle=140
        )

        # Agregar una leyenda
        plt.legend(wedges, data.index, title="Tipos de Carga", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

        # Títulos y formato
        plt.title("Distribución de CLP $ por Tipo de Carga", fontsize=14, color="white")
        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")  # Fondo oscuro

        # Guardar el gráfico en base64
        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["clp_por_tipo_carga"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()


        print("2")

    # grafico Wip 025
    print(2.1)
    if "Wip" in filtered_data.columns:
        # Filtrar solo WIP 40025
        filtered_data_025 = filtered_data[filtered_data["Wip"] == "40025"]

        # Diccionario de palabras clave para clasificar
        diccionario_palabras_clave = {
            "Misc": ["Misc"],
            "Jaula": ["Jaula"],
            "Fundaciones": ["Fundaciones"],
            "Estanque": ["Estanque"],
            "Escala": ["Escala"],
            "Acceso": ["Acceso"],
        }

        # Crear una nueva columna para clasificar las categorías
        filtered_data_025["Categoría"] = "Otros"

        for categoria, palabras in diccionario_palabras_clave.items():
            for palabra in palabras:
                filtered_data_025.loc[
                    filtered_data_025["Detalle"].str.contains(palabra, na=False, case=False), "Categoría"
                ] = categoria

        # Calcular la distribución
        data_distribucion = filtered_data_025.groupby("Categoría")["CLP $"].sum()
        categorias = data_distribucion.index
        valores = data_distribucion.values

        # Crear etiquetas personalizadas
        total_dinero = sum(valores)

        # Crear tabla de datos
        tabla_datos = [
            [categoria, f"{valor:,.0f} CLP", f"{(valor / total_dinero) * 100:.1f}%"]
            for categoria, valor in zip(categorias, valores)
        ]

        # Crear gráfico circular
        plt.figure(figsize=(8, 8), facecolor="#1e1e1e")
        colores = ["#FF6F61", "#4CAF50", "#66B3FF", "#FFC300", "#8E44AD"][:len(categorias)]

        wedges, texts, autotexts = plt.pie(
            data_distribucion, labels=None, autopct=lambda p: f'{p:.1f}%' if p > 0 else '', colors=colores, startangle=140,
            textprops=dict(color="white")
        )
        plt.legend(wedges, categorias, title="Detalle", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.title("Distribución de Costos WIP 40025", fontsize=14, color="white")
        plt.gca().set_facecolor("#1e1e1e")
        print("2.2")
        # Ajustar diseño
        # Añadir tabla con colores personalizados
        valores = data_distribucion.values

        # Crear etiquetas personalizadas
        total_dinero = sum(valores)
        tabla_datos = [
            [categoria, f"{valor:,.0f} CLP", f"{(valor / total_dinero) * 100:.1f}%"]
            for categoria, valor in zip(categorias, valores)
        ]
        tabla = plt.table(
            cellText=tabla_datos,
            colColours=["#FF6F61", "#FF6F61", "#FF6F61"],  # Colores en formato hexadecimal
            colLabels=["Categoría", "Valor CLP", "Porcentaje"],
            cellLoc="center",
            loc="bottom",
            bbox=[0.0, -0.5, 1.0, 0.4],  # Ajustar posición de la tabla
            edges="horizontal",
        )
        print("2.4")
        for key, cell in tabla.get_celld().items():
            cell.set_edgecolor("white")    # Bordes de las celdas en blanco
            cell.set_text_props(color="white")  # Texto en blanco
            cell.set_facecolor("#1e1e1e")  # Fondo oscuro para las celdas
        plt.tight_layout()

        # Guardar imagen como base64
        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["distribucion_con_tabla"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()

        print("3")


        #### 024 ####

        filtered_data_024 = filtered_data[filtered_data["Wip"] == "40024"]
        # Diccionario de palabras clave para clasificar
        diccionario_palabras_clave = {"Misc" : ["Misc", "Forro", "Malla"],
                                    "Equipamiento" : ["Equipamiento","Cama", "Closet", "Tv", "Colchon", "Cajon", "Sill"]

        }

        # Crear una nueva columna para clasificar las categorías
        filtered_data_024["Categoría"] = "Otros"

        for categoria, palabras in diccionario_palabras_clave.items():
            for palabra in palabras:
                filtered_data_024.loc[filtered_data_024["Detalle"].str.contains(palabra, na=False, case=False), "Categoría"] = categoria


        # Generar gráfico circular de distribución total
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
        data_distribucion = filtered_data_024.groupby("Categoría")["CLP $"].sum()
        categorias = data_distribucion.index

        colores = generar_colores(categorias)

        wedges, texts, autotexts = plt.pie(
            data_distribucion, labels=None, autopct="%1.1f%%", colors=colores,
            textprops=dict(color="white"), startangle=140
        )

        plt.title("Distribución de costos WIP 024", fontsize=14, color="white")
        plt.legend(wedges, categorias, title="Detalle", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")

        # Ajustar diseño
        # Añadir tabla con colores personalizados
        valores = data_distribucion.values

        # Crear etiquetas personalizadas
        total_dinero = sum(valores)
        tabla_datos = [
            [categoria, f"{valor:,.0f} CLP", f"{(valor / total_dinero) * 100:.1f}%"]
            for categoria, valor in zip(categorias, valores)
        ]
        tabla = plt.table(
            cellText=tabla_datos,
            colColours=["#FF6F61", "#FF6F61", "#FF6F61"],  # Colores en formato hexadecimal
            colLabels=["Categoría", "Valor CLP", "Porcentaje"],
            cellLoc="center",
            loc="bottom",
            bbox=[0.0, -0.5, 1.0, 0.4],  # Ajustar posición de la tabla
            edges="horizontal",
        )

        for key, cell in tabla.get_celld().items():
            cell.set_edgecolor("white")    # Bordes de las celdas en blanco
            cell.set_text_props(color="white")  # Texto en blanco
            cell.set_facecolor("#1e1e1e")  # Fondo oscuro para las celdas
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["DISTRIBUCION 40024"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()

        # Mostrar registros que se agrupan en "Otros"
        registros_otros = filtered_data_024[filtered_data_024["Categoría"] == "Otros"]["Detalle"].tolist()
        print("Registros clasificados como 'Otros':", registros_otros)
        print("4")

                #### 023 ####

        filtered_data_023 = filtered_data[filtered_data["Wip"] == "40023"]
        # Diccionario de palabras clave para clasificar
        diccionario_palabras_clave = {"ICG" : ["ICG"],
                                    "CR" : ["CR"],
                                    "Asap" : ["Asap"],
                                    "Pro Air" : ["Pro Air"]
        }

        # Crear una nueva columna para clasificar las categorías
        filtered_data_023["Categoría"] = "Otros"

        for categoria, palabras in diccionario_palabras_clave.items():
            for palabra in palabras:
                filtered_data_023.loc[filtered_data_023["Detalle"].str.contains(palabra, na=False, case=False), "Categoría"] = categoria


        # Generar gráfico circular de distribución total
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
        data_distribucion = filtered_data_023.groupby("Categoría")["CLP $"].sum()
        categorias = data_distribucion.index

        colores = generar_colores(categorias)

        wedges, texts, autotexts = plt.pie(
            data_distribucion, labels=None, autopct="%1.1f%%", colors=colores,
            textprops=dict(color="white"), startangle=140
        )

        plt.title("Distribución de costos WIP 023", fontsize=14, color="white")
        plt.legend(wedges, categorias, title="Detalle", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")
        # Ajustar diseño
        # Añadir tabla con colores personalizados
        valores = data_distribucion.values

        # Crear etiquetas personalizadas
        total_dinero = sum(valores)
        tabla_datos = [
            [categoria, f"{valor:,.0f} CLP", f"{(valor / total_dinero) * 100:.1f}%"]
            for categoria, valor in zip(categorias, valores)
        ]
        tabla = plt.table(
            cellText=tabla_datos,
            colColours=["#FF6F61", "#FF6F61", "#FF6F61"],  # Colores en formato hexadecimal
            colLabels=["Categoría", "Valor CLP", "Porcentaje"],
            cellLoc="center",
            loc="bottom",
            bbox=[0.0, -0.5, 1.0, 0.4],  # Ajustar posición de la tabla
            edges="horizontal",
        )

        for key, cell in tabla.get_celld().items():
            cell.set_edgecolor("white")    # Bordes de las celdas en blanco
            cell.set_text_props(color="white")  # Texto en blanco
            cell.set_facecolor("#1e1e1e")  # Fondo oscuro para las celdas
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["DISTRIBUCION 40023"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()

        # Mostrar registros que se agrupan en "Otros"
        registros_otros = filtered_data_023[filtered_data_023["Categoría"] == "Otros"]["Detalle"].tolist()
        print("Registros clasificados como 'Otros':", registros_otros)
        print("5")

    return kpi_images

def generar_kpi_graficos_1(filtered_data_1, data_1):
    """
    Genera gráficos circulares para:
    1. Porcentaje de N° de serie con N° EDP no vacío.
    2. Dinero gastado en N° de serie con N° OC no vacío.
    3. Estimación del dinero restante.
    """
    kpi_images = {}

    # 1. Porcentaje de N° DE SERIE con N° EDP no vacío
    series_con_edp = filtered_data_1['N° EDP'].notna().sum()
    porcentaje_con_edp = (series_con_edp / len(data_1)) * 100
    porcentaje_sin_edp = 100 - porcentaje_con_edp

    plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
    sizes = [porcentaje_sin_edp, porcentaje_con_edp]
    labels = ['Por Enviar', 'Enviado']
    colors = ['#FF6F61', '#4CAF50']

    wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      colors=colors, textprops={'fontsize': 12, 'color': 'white'})
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)

    plt.text(0, 0, f"{porcentaje_con_edp:.1f}%", ha='center', va='center', fontsize=28, 
             fontweight='bold', color="white")

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor="#1e1e1e")
    img.seek(0)
    kpi_images['PROGRESO PROYECTO'] = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # 2. Dinero gastado con N° OC no vacío
    con_oc = filtered_data_1[filtered_data_1['N° OC'].notna() & (filtered_data_1['N° OC'] != "")]
    sin_oc = filtered_data_1[filtered_data_1['N° OC'].isna() | (filtered_data_1['N° OC'] == "")]
    total_con_oc = con_oc['VALOR FLETE'].sum() if not con_oc.empty else 0
    total_sin_oc = sin_oc['VALOR FLETE'].sum() if not sin_oc.empty else 0
    total_dinero = total_con_oc + total_sin_oc

    plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
    sizes = [total_sin_oc, total_con_oc]
    labels = ['ENVIADO NO PAGADO', 'ENVIADO CON OC PAGADA']
    colors = ['#FF6F61', '#4FC3F7']

    wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      colors=colors, textprops={'fontsize': 12, 'color': 'white'})
    for autotext in autotexts:
        autotext.set_color('white')

    plt.text(-1, -0.5, f"${total_sin_oc:,.0f}", ha='center', va='center', fontsize=14, color="white")
    plt.text(1, -0.5, f"${total_con_oc:,.0f}", ha='center', va='center', fontsize=14, color="white")
    plt.text(0, 0, f"${total_dinero:,.0f}", ha='center', va='center', fontsize=28, fontweight='bold', color="white")

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor="#1e1e1e")
    img.seek(0)
    kpi_images['COSTOS ACTUALES'] = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # 3. Estimación del dinero restante
    plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
    sizes = [total_dinero, total_dinero * (porcentaje_sin_edp / porcentaje_con_edp)]
    labels = ['Dinero Actual', 'Estimación Dinero Restante']
    colors = ['#d34cd1', '#609262']

    wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      colors=colors, textprops={'fontsize': 12, 'color': 'white'})
    for autotext in autotexts:
        autotext.set_color('white')

    plt.text(-1, -0.5, f"${total_dinero:,.0f}", ha='center', va='center', fontsize=14, color="white")
    plt.text(1, -0.5, f"${total_dinero * (porcentaje_sin_edp / porcentaje_con_edp):,.0f}", 
             ha='center', va='center', fontsize=14, color="white")
    plt.text(0, 0, f"${total_dinero / (porcentaje_con_edp / 100):,.0f}", ha='center', 
             va='center', fontsize=24, fontweight='bold', color="white")

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor="#1e1e1e")
    img.seek(0)
    kpi_images['ESTIMACIONES COSTOS'] = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return kpi_images




def generar_colores(categorias):
    """Genera colores únicos para cada categoría usando colormap."""
    colormap = plt.colormaps["tab20"]  # Nueva sintaxis de matplotlib
    colores = [colormap(i / len(categorias)) for i in range(len(categorias))]
    return colores


@app.route("/descargar_informe", methods=["POST"])
def descargar_informe():
    global kpi_images_global
    global kpi_images_global_1
    file_path = "data/CENTINELA.xlsx"
    informe_path = "static/informe_transporte.pdf"

    try:

        generar_informe( kpi_images_global, kpi_images_global_1, output_path=informe_path)
        
        return send_file(informe_path, as_attachment=True)
    except Exception as e:
        return f"Error al generar el informe: {str(e)}", 500


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/")  # Abrir la URL principal

    # Verificar si el servidor está iniciando por primera vez (no en el proceso de recarga)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()  # Abre el navegador solo en el primer inicio

    app.run(debug=True)
