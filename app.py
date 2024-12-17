from flask import Flask, render_template, request, send_file
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib import cm
import io
import base64
from data import data_processing
from generar_informe import generar_informe

app = Flask(__name__)

# Configurar estilos globales de Matplotlib
plt.style.use("ggplot")

# Variable global para almacenar las imágenes de KPI
kpi_images_global = None

@app.route("/", methods=["GET", "POST"])
def dashboard():
    global kpi_images_global  # Declarar variable global
    file_path = "data/Control y registro de misceláneos proyecto Centinela.xlsx"

    try:
        # Procesar los datos
        data = data_processing.procesar_data(file_path)
    except Exception as e:
        return render_template("error.html", message=f"Error al procesar el archivo: {str(e)}")
    
    filtered_data = None
    kpi_images_global = None  # Reiniciar variable global al cargar la página
    
    if request.method == "POST":
        # Obtener fechas del formulario
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        
        if start_date and end_date:
            try:
                # Convertir fechas y filtrar
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                data["Fecha"] = pd.to_datetime(data["Fecha"])
                filtered_data = data[(data["Fecha"] >= start_date) & (data["Fecha"] <= end_date)]
                
                # Generar gráficos de KPI y guardarlos en la variable global
                kpi_images_global = generar_kpi_graficos(filtered_data)
            except Exception as e:
                return render_template("error.html", message=f"Error al filtrar los datos: {str(e)}")

    # Determinar cuántas filas mostrar
    largo = len(filtered_data) if filtered_data is not None else 10
    
    return render_template(
        "dashboard.html", 
        filtered_table=filtered_data.head(largo).to_html(classes="table table-striped", index=False) if filtered_data is not None else None,
        kpi_images=kpi_images_global
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

def generar_colores(categorias):
    """Genera colores únicos para cada categoría usando colormap."""
    colormap = plt.colormaps["tab20"]  # Nueva sintaxis de matplotlib
    colores = [colormap(i / len(categorias)) for i in range(len(categorias))]
    return colores


@app.route("/descargar_informe", methods=["POST"])
def descargar_informe():
    global kpi_images_global
    file_path = "data/Control y registro de misceláneos proyecto Centinela.xlsx"
    informe_path = "static/informe_transporte.pdf"

    try:
        # Verificar si hay gráficos generados
        if kpi_images_global is None:
            return "No se han generado gráficos. Por favor filtra los datos primero.", 400
        
        # Generar informe PDF
        data = data_processing.procesar_data(file_path)
        generar_informe(data, kpi_images_global, output_path=informe_path)
        
        return send_file(informe_path, as_attachment=True)
    except Exception as e:
        return f"Error al generar el informe: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)
