from fpdf import FPDF
import pandas as pd
import os
import base64

class PDF(FPDF):
    def header(self):
        # Encabezado con fondo y título
        self.set_fill_color(255, 99, 71)  # Color de fondo: Tomate
        self.rect(0, 0, 210, 20, 'F')
        self.set_font("Arial", "B", 16)
        self.set_text_color(255, 255, 255)  # Texto blanco
        self.cell(0, 10, "Informe de Logística", align="C", ln=True)
        self.ln(5)

    def footer(self):
        # Pie de página
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(128)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

from fpdf import FPDF
import base64

def generar_informe(data, kpi_images, kpi_images2, output_path="informe.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # Agregar logo en la parte superior
    logo_path = "static/logo.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=10, w=30)  # Ajusta la posición y tamaño del logo

    # Título principal
    pdf.set_font("Arial", "B", 16)
    pdf.set_y(20)  # Mover texto debajo del logo
    pdf.cell(200, 10, "Informe de Logística", ln=True, align="C")
    pdf.ln(10)

    # Sección de KPI's Misceláneos
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "KPI's Misceláneos", ln=True, align="C")
    pdf.ln(5)

    for titulo, img_base64 in kpi_images.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, titulo.replace('_', ' ').title(), ln=True)
        pdf.ln(5)
        img_path = f"temp_{titulo}.png"
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(img_base64))
        pdf.image(img_path, x=10, w=190)
        pdf.ln(10)
        os.remove(img_path)

    # Sección de KPI's Módulos
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "KPI's Módulos", ln=True, align="C")
    pdf.ln(5)

    for titulo, img_base64 in kpi_images2.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, titulo.replace('_', ' ').title(), ln=True)
        pdf.ln(5)
        img_path = f"temp_{titulo}.png"
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(img_base64))
        pdf.image(img_path, x=10, w=190)
        pdf.ln(10)
        os.remove(img_path)

    pdf.output(output_path)
    print(f"Informe guardado en: {output_path}")

