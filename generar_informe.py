from fpdf import FPDF
import os
import base64

class PDF(FPDF):
    def header(self):
        """Encabezado con fondo de color y título centrado"""
        self.set_fill_color(41, 128, 185)  # Color de fondo: Azul
        self.rect(0, 0, 210, 20, 'F')  # Fondo completo del ancho de la página
        self.set_font("Arial", "B", 16)
        self.set_text_color(255, 255, 255)  # Texto blanco
        self.cell(0, 10, "Informe de Logística", align="C", ln=True)
        self.ln(5)

    def footer(self):
        """Pie de página con número de página"""
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(128)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def agregar_titulo_seccion(self, titulo):
        """Formato de títulos de sección"""
        self.set_font("Arial", "B", 14)
        self.set_text_color(44, 62, 80)  # Azul oscuro
        self.cell(0, 10, titulo, ln=True, align="L")
        self.ln(5)

    def agregar_imagen_base64(self, img_base64, titulo):
        """Agrega una imagen desde una cadena Base64 con título"""
        try:
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, titulo, ln=True)
            self.ln(5)
            # Guardar imagen temporalmente
            img_path = f"temp_{titulo}.png"
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(img_base64))
            self.image(img_path, x=10, w=190)
        except Exception as e:
            self.set_font("Arial", "I", 12)
            self.set_text_color(200, 0, 0)  # Texto rojo para errores
            self.cell(0, 10, f"Error al agregar la imagen: {titulo} - {e}", ln=True)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)
        self.ln(10)

def generar_informe(kpi_images, kpi_images2, output_path="informe.pdf"):
    """Genera un informe en PDF con datos y gráficos en formato Base64.

    Args:
        data (dict): Información relevante para el informe.
        kpi_images (dict): Imágenes Base64 para la sección de Indicadores Generales.
        kpi_images2 (dict): Imágenes Base64 para la sección de Indicadores de Módulos.
        output_path (str): Ruta de salida para el PDF generado.
    """
    pdf = PDF()
    pdf.add_page()

    # Agregar logo (si existe)
    logo_path = "static/logo.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=10, w=30)  # Ajusta el tamaño y posición según tus necesidades

    # Título principal
    pdf.set_font("Arial", "B", 18)
    pdf.set_y(30)
    pdf.cell(0, 10, "Resumen Ejecutivo de Indicadores Clave", ln=True, align="C")
    pdf.ln(10)

    # Agregar breve análisis
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, (
        "Este informe presenta los principales indicadores de rendimiento (KPIs) del proceso logístico, "
        "incluyendo datos relevantes como el progreso de módulos y la distribución de costos. "
        "Se destacan visualizaciones claras y concisas para facilitar el análisis."
    ))
    pdf.ln(10)

    # Primera sección: KPI's Misceláneos
    pdf.agregar_titulo_seccion("Indicadores Generales")
    for titulo, img_base64 in kpi_images.items():
        pdf.agregar_imagen_base64(img_base64, titulo.replace('_', ' ').title())

    # Segunda sección: KPI's Módulos
    pdf.agregar_titulo_seccion("Indicadores de Módulos")
    for titulo, img_base64 in kpi_images2.items():
        pdf.agregar_imagen_base64(img_base64, titulo.replace('_', ' ').title())

    # Guardar el PDF
    try:
        pdf.output(output_path)
        print(f"Informe guardado exitosamente en: {output_path}")
    except Exception as e:
        print(f"Error al guardar el informe: {e}")
