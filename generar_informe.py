from fpdf import FPDF
import pandas as pd
import os
import base64

def generar_informe(data, kpi_images, output_path="informe.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # Título principal
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Informe de Transporte - Proyecto Centinela", ln=True, align="C")
    pdf.ln(10)

    # Insertar gráficos (opcional)
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

    # Insertar resumen estadístico
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resumen de Datos:", ln=True)
    pdf.ln(5)
    resumen = data.describe()
    pdf.set_font("Arial", "", 10)
    for col in resumen.columns[:4]:
        pdf.cell(40, 10, col, 1)
    pdf.ln()
    for index, row in resumen.iterrows():
        for col in resumen.columns[:4]:
            pdf.cell(40, 10, f"{row[col]:.2f}", 1)
        pdf.ln()

    pdf.output(output_path)
    print(f"Informe guardado en: {output_path}")
