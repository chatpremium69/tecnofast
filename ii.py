from flask import Flask, render_template, request, send_file
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
import io
import base64
from werkzeug.utils import secure_filename
from data import data_processing
from generar_informe import generar_informe

app = Flask(__name__)

# Configurar carpeta para cargar archivos
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)  # Crear carpeta si no existe

# Configurar estilos globales de Matplotlib
plt.style.use("ggplot")

# Variables globales para KPIs
global_kpi_images = None
global_kpi_images_1 = None

@app.route("/", methods=["GET", "POST"])
def dashboard():
    global global_kpi_images
    global global_kpi_images_1

    # Archivo predeterminado
    default_file_path = "data/SIERRA_GORDA.xlsx"
    file_path = default_file_path

    # Procesar datos iniciales
    try:
        data = data_processing.procesar_data(file_path)
        data_1 = data_processing.procesar_data_modulos(file_path)
    except Exception as e:
        return render_template("error.html", message=f"Error al procesar el archivo: {str(e)}")

    filtered_data = None
    filtered_data_1 = None
    global_kpi_images = None
    global_kpi_images_1 = None

    # Valores predeterminados para fechas
    start_date = pd.Timestamp("2001-01-01")
    end_date = pd.Timestamp("today")

    if request.method == "POST":
        # Manejo de carga de archivo
        if "file" in request.files:
            file = request.files["file"]
            if file.filename:
                upload_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
                file.save(upload_path)
                file_path = upload_path  # Usar el archivo subido

        # Manejo de fechas
        if "filter_all" in request.form:
            start_date = pd.Timestamp("2001-01-01")
            end_date = pd.Timestamp("today")
        else:
            form_start_date = request.form.get("start_date")
            form_end_date = request.form.get("end_date")
            if form_start_date and form_end_date:
                start_date = pd.to_datetime(form_start_date)
                end_date = pd.to_datetime(form_end_date)

        try:
            # Procesar datos con el archivo actualizado
            data = data_processing.procesar_data(file_path)
            data_1 = data_processing.procesar_data_modulos(file_path)

            # Filtrar datos
            data["Fecha"] = pd.to_datetime(data["Fecha"])
            filtered_data = data[(data["Fecha"] >= start_date) & (data["Fecha"] <= end_date)]

            data_1["FECHA DESPACHO"] = pd.to_datetime(data_1["FECHA DESPACHO"])
            filtered_data_1 = data_1[(data_1["FECHA DESPACHO"] >= start_date) & (data_1["FECHA DESPACHO"] <= end_date)]

            # Generar KPIs
            global_kpi_images = generar_kpi_graficos(filtered_data)
            global_kpi_images_1 = generar_kpi_graficos_1(filtered_data_1, data_1)
        except Exception as e:
            return render_template("error.html", message=f"Error al filtrar los datos: {str(e)}")

    return render_template(
        "dashboard.html",
        filtered_table=filtered_data.to_html(classes="table table-striped", index=False) if filtered_data is not None else None,
        kpi_images=global_kpi_images,
        filtered_table_1=filtered_data_1.to_html(classes="table table-striped", index=False) if filtered_data_1 is not None else None,
        kpi_images_1=global_kpi_images_1
    )

@app.route("/descargar_informe", methods=["POST"])
def descargar_informe():
    global global_kpi_images
    global global_kpi_images_1
    informe_path = "static/informe_transporte.pdf"

    try:
        if global_kpi_images is None or global_kpi_images_1 is None:
            return "No se han generado gráficos. Por favor filtra los datos primero.", 400

        data = data_processing.procesar_data("data/SIERRA_GORDA.xlsx")
        generar_informe(data, global_kpi_images, global_kpi_images_1, output_path=informe_path)

        return send_file(informe_path, as_attachment=True)
    except Exception as e:
        return f"Error al generar el informe: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
