
from flask import Flask, render_template, request, send_file
import webbrowser
from threading import Timer 
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib import cm
import io
import base64
from werkzeug.utils import secure_filename
from data import data_processing
from generar_informe import generar_informe

app = Flask(__name__)

# Configuración de carpeta de subida
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)  # Crear carpeta si no existe
ALLOWED_EXTENSIONS = {"xls", "xlsx"}  # Extensiones permitidas


# Configurar estilos globales de Matplotlib
plt.style.use("ggplot")

# Variable global para almacenar las imágenes de KPI
kpi_images_global = None
kpi_images_global_1 = None

@app.route("/", methods=["GET", "POST"])
def dashboard():
    global kpi_images_global
    global kpi_images_global_1

    file_path = "data/SIERRA_GORDA.xlsx"  # Archivo predeterminado
    start_date = pd.Timestamp("2001-01-01")  # Rango inicial por defecto
    end_date = pd.Timestamp("today")  # Fecha final por defecto

    if request.method == "POST":
        # Verificar si se subió un archivo
        if "file" in request.files:
            file = request.files["file"]
            if file and allowed_file(file.filename):
                uploaded_file = secure_filename(file.filename)
                upload_path = os.path.join(app.config["UPLOAD_FOLDER"], uploaded_file)
                file.save(upload_path)
                file_path = upload_path  # Sobrescribir con el archivo subido

        # Obtener fechas del formulario si están disponibles
        if "filter_all" in request.form:  # Si se presiona el botón "Mostrar Todo"
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
        data = data_processing.procesar_data(file_path)
        data_1 = data_processing.procesar_data_modulos(file_path)

        # Convertir y filtrar las fechas
        data["Fecha"] = pd.to_datetime(data["Fecha"], errors="coerce")
        filtered_data = data[(data["Fecha"] >= start_date) & (data["Fecha"] <= end_date)]

        data_1["FECHA DESPACHO"] = pd.to_datetime(data_1["FECHA DESPACHO"], errors="coerce")
        filtered_data_1 = data_1[(data_1["FECHA DESPACHO"] >= start_date) & (data_1["FECHA DESPACHO"] <= end_date)]

        # Generar gráficos de KPI
        kpi_images_global = generar_kpi_graficos(filtered_data)
        kpi_images_global_1 = generar_kpi_graficos_1(filtered_data_1, data_1)

    except Exception as e:
        return render_template("error.html", message=f"Error al procesar o filtrar los datos: {str(e)}")

    return render_template(
        "dashboard.html",
        filtered_table=filtered_data.to_html(classes="table table-striped", index=False) if not filtered_data.empty else None,
        kpi_images=kpi_images_global,
        filtered_table_1=filtered_data_1.to_html(classes="table table-striped", index=False) if not filtered_data_1.empty else None,
        kpi_images_1=kpi_images_global_1,
    )


def generar_kpi_graficos(filtered_data):
    """Genera gráficos mejorados y devuelve imágenes en formato base64."""
    kpi_images = {}

    # 1. Gráfico de Barras: Costo Total CLP $ por Proyecto
    if not filtered_data.empty:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
        ax = filtered_data.groupby("Proyecto")["CLP $"].sum().sort_values().plot(
            kind="bar", color="#dc3545", edgecolor="white", width=0.7
        )
        ax.set_title("Costo Total de Transporte por Proyecto", fontsize=14, color="white")
        ax.set_ylabel("CLP $", fontsize=12, color="white")
        ax.tick_params(colors="white")
        plt.xticks(rotation=45, color="white")

        # Mostrar valores sobre las barras
        for p in ax.patches:
            ax.annotate(f"{p.get_height():,.0f}", 
                        (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha="center", va="center", fontsize=10, color="white", xytext=(0, 8),
                        textcoords="offset points")

        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")

        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["costo_proyecto"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()

    # 2. Gráfico de Líneas: Evolución de Costos Totales en el Tiempo
    if "Fecha" in filtered_data.columns:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
        ax = filtered_data.groupby("Fecha")["CLP $"].sum().plot(
            kind="line", marker="o", linestyle="-", color="#66b3ff", linewidth=2, markersize=6
        )
        ax.set_title("Evolución de Costos Totales en el Tiempo", fontsize=14, color="white")
        ax.set_ylabel("CLP $", fontsize=12, color="white")
        ax.set_xlabel("Fecha", fontsize=12, color="white")
        ax.tick_params(colors="white")
        plt.xticks(rotation=45, color="white")

        # Resaltar puntos de picos
        max_point = filtered_data.groupby("Fecha")["CLP $"].sum().max()
        ax.annotate(f"Máximo: {max_point:,.0f}", xy=(filtered_data["Fecha"].iloc[-1], max_point),
                    xytext=(0, 20), textcoords="offset points", ha="center",
                    fontsize=10, color="white")

        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")

        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["costo_tiempo"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()

    # 3. Gráfico Circular: Distribución por Tipo de Carga
    if "Tipo de Carga" in filtered_data.columns:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")
        data = filtered_data["Tipo de Carga"].value_counts()
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

    #4 Gráfico por Hoja (Cantidad de registros o Suma de CLP $)
    if "Hoja" in filtered_data.columns:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")

        # Agrupar por Hoja y contar registros
        data_por_hoja = filtered_data["Hoja"].value_counts()

        # Crear el gráfico de barras
        ax = data_por_hoja.plot(kind="bar", color=["#FF6F61", "#6A5ACD", "#4CAF50"], edgecolor="white")
        ax.set_title("Cantidad de Registros por Hoja", fontsize=14, color="white")
        ax.set_xlabel("Hojas", fontsize=12, color="white")
        ax.set_ylabel("Cantidad de Registros", fontsize=12, color="white")
        ax.tick_params(colors="white")
        plt.xticks(rotation=45, color="white")
        plt.yticks(color="white")

        # Estética
        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")

        # Guardar el gráfico en base64
        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["registros_por_hoja"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()

    #5 Gráfico por Hoja (Suma de CLP $)
    if "Hoja" in filtered_data.columns and "CLP $" in filtered_data.columns:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")

        # Agrupar por "Hoja" y sumar CLP $
        data_por_hoja = filtered_data.groupby("Hoja")["CLP $"].sum()


        # Crear el gráfico de barras
        ax = data_por_hoja.plot(kind="bar", color=["#FF6F61", "#6A5ACD", "#4CAF50"], edgecolor="white")
        ax.set_title("Costo Total (CLP $) por Hoja", fontsize=14, color="white")
        ax.set_xlabel("Hojas", fontsize=12, color="white")
        ax.set_ylabel("CLP $ Total", fontsize=12, color="white")
        ax.tick_params(colors="white")
        plt.xticks(rotation=45, color="white")
        plt.yticks(color="white")

        # Estética del gráfico
        plt.tight_layout()
        plt.gca().set_facecolor("#1e1e1e")

        # Guardar el gráfico como base64
        img = io.BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight", facecolor="#1e1e1e")
        img.seek(0)
        kpi_images["clp_por_hoja"] = base64.b64encode(img.getvalue()).decode("utf8")
        plt.close()

    # Gráfico Circular: Suma de CLP $ por Tipo de Carga
    if "Tipo de Carga" in filtered_data.columns and "CLP $" in filtered_data.columns:
        plt.figure(figsize=(8, 6), facecolor="#1e1e1e")

        # Agrupar por Tipo de Carga y sumar CLP $
        data = filtered_data.groupby("Tipo de Carga")["CLP $"].sum()

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
    file_path = "data/SIERRA_GORDA.xlsx"
    informe_path = "static/informe_transporte.pdf"

    try:
        # Verificar si hay gráficos generados
        if kpi_images_global is None or kpi_images_global_1 is None :
            return "No se han generado gráficos. Por favor filtra los datos primero.", 400
        
        # Generar informe PDF
        data = data_processing.procesar_data(file_path)
        generar_informe(data, kpi_images_global, kpi_images_global_1, output_path=informe_path)
        
        return send_file(informe_path, as_attachment=True)
    except Exception as e:
        return f"Error al generar el informe: {str(e)}", 500


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



if __name__ == "__main__":
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/")  # Abrir la URL principal

    # Verificar si el servidor está iniciando por primera vez (no en el proceso de recarga)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()  # Abre el navegador solo en el primer inicio

    app.run(debug=True)
