from flask import Flask, render_template, request
import pandas as pd
import os
import matplotlib.pyplot as plt
import io
import base64
from data import data_processing

app = Flask(__name__)

# Configurar estilos globales de Matplotlib
plt.style.use("ggplot")

# Ruta para la página principal
@app.route("/", methods=["GET", "POST"])
def dashboard():
    # Cargar el archivo Excel
    file_path = "data/Control y registro de misceláneos proyecto Centinela.xlsx"
    
    try:
        # Procesar los datos
        data = data_processing.procesar_data(file_path)
    except Exception as e:
        return render_template("error.html", message=f"Error al procesar el archivo: {str(e)}")
    
    filtered_data = None
    kpi_images = None
    
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
                
                # Generar gráficos de KPI
                kpi_images = generar_kpi_graficos(filtered_data)
            except Exception as e:
                return render_template("error.html", message=f"Error al filtrar los datos: {str(e)}")
    if filtered_data is not None:
        largo = len(filtered_data)
    else:
        largo = 10
    return render_template("dashboard.html", 
                           filtered_table=filtered_data.head(largo).to_html(classes="table table-striped", index=False) if filtered_data is not None else None,
                           kpi_images=kpi_images)


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
        wedges, texts, autotexts = plt.pie(data, autopct="%1.1f%%", colors=["#ff9999", "#66b3ff", "#99ff99"],
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

    return kpi_images



if __name__ == "__main__":
    app.run(debug=True)
