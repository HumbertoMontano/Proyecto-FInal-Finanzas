import streamlit as st
from lxml import etree
from dataclasses import dataclass, asdict
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


@dataclass
class Factura:
    nombre: str
    rfc_emisor: str
    nombre_emisor: str
    concepto: tuple
    total: float
    fecha: str
    impuesto: float
    uso_cfdi: str

    def __eq__(self, other):
        return isinstance(other, Factura) and self.nombre == other.nombre and self.total == other.total

    def __hash__(self):
        return hash((self.nombre, self.total))


def generar_pdf(
    totales_anio,
    totales_mes,
    impuestos_anio,
    impuestos_mes,
    rfc_anio_mes,
    concepto_anio_mes,
    uso_anio_mes
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elementos = []
    estilos = getSampleStyleSheet()

    titulo = Paragraph("Reporte de gastos", estilos["Title"])
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Totales por año", estilos["Heading2"]))
    datos_anio = [list(totales_anio.columns)] + totales_anio.values.tolist()
    tabla_anio = Table(datos_anio)
    tabla_anio.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabla_anio)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Totales por mes (año/mes)", estilos["Heading2"]))
    datos_mes = [list(totales_mes.columns)] + totales_mes.values.tolist()
    tabla_mes = Table(datos_mes)
    tabla_mes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabla_mes)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Impuestos pagados por año", estilos["Heading2"]))
    datos_imp_anio = [list(impuestos_anio.columns)] + impuestos_anio.values.tolist()
    tabla_imp_anio = Table(datos_imp_anio)
    tabla_imp_anio.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabla_imp_anio)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Impuestos pagados por mes (año/mes)", estilos["Heading2"]))
    datos_imp_mes = [list(impuestos_mes.columns)] + impuestos_mes.values.tolist()
    tabla_imp_mes = Table(datos_imp_mes)
    tabla_imp_mes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabla_imp_mes)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Totales e impuestos por año y mes por RFC emisor", estilos["Heading2"]))
    datos_rfc = [list(rfc_anio_mes.columns)] + rfc_anio_mes.values.tolist()
    tabla_rfc = Table(datos_rfc)
    tabla_rfc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabla_rfc)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Totales e impuestos por año y mes por concepto", estilos["Heading2"]))
    datos_concepto = [list(concepto_anio_mes.columns)] + concepto_anio_mes.values.tolist()
    tabla_concepto = Table(datos_concepto)
    tabla_concepto.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabla_concepto)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Totales e impuestos por año y mes por uso de CFDI", estilos["Heading2"]))
    datos_uso = [list(uso_anio_mes.columns)] + uso_anio_mes.values.tolist()
    tabla_uso = Table(datos_uso)
    tabla_uso.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabla_uso)

    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


st.set_page_config(
    page_title="Mi App",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("Reporte de gastos")
uploaded_files = st.sidebar.file_uploader(
    "Sube facturas", type="xml", accept_multiple_files=True
)

filtro_rfc = st.sidebar.text_input("Filtrar por RFC emisor:")

st.title("Reporte de facturas")

if "facturas" not in st.session_state:
    st.session_state.facturas = []

if uploaded_files:
    lista_facturas = []

    for uploaded_file in uploaded_files:
        xml_bytes = uploaded_file.read()

        try:
            tree = etree.fromstring(xml_bytes)
            ns = {"cfdi": "http://www.sat.gob.mx/cfd/4"}

            total = tree.xpath("//cfdi:Comprobante/@Total", namespaces=ns)
            rfc_emisor = tree.xpath("//cfdi:Comprobante/cfdi:Emisor/@Rfc", namespaces=ns)
            nombre_emisor = tree.xpath("//cfdi:Comprobante/cfdi:Emisor/@Nombre", namespaces=ns)
            fecha = tree.xpath("//cfdi:Comprobante/@Fecha", namespaces=ns)
            concepto = tree.xpath("//cfdi:Comprobante/cfdi:Conceptos/cfdi:Concepto/@Descripcion", namespaces=ns)
            uso_cfdi = tree.xpath("//cfdi:Comprobante/cfdi:Receptor/@UsoCFDI", namespaces=ns)
            impuestos = tree.xpath(
                "//cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@Importe",
                namespaces=ns
            )

            st.write(f"Archivo leído correctamente: {uploaded_file.name}")

            factura = Factura(
                nombre=uploaded_file.name,
                rfc_emisor=rfc_emisor[0] if rfc_emisor else "",
                nombre_emisor=nombre_emisor[0] if nombre_emisor else "",
                concepto=tuple(concepto),
                total=float(total[0]) if total else 0.0,
                fecha=fecha[0] if fecha else "",
                impuesto=float(impuestos[0]) if impuestos else 0.0,
                uso_cfdi=uso_cfdi[0] if uso_cfdi else ""
            )

            lista_facturas.append(factura)

        except Exception as e:
            st.error(f"Error al leer {uploaded_file.name}: {e}")

    st.session_state.facturas = list(set(lista_facturas))

else:
    st.write("seleccione sus facturas XML")
    st.session_state.facturas = []


if len(st.session_state.facturas) > 0:
    df = pd.DataFrame([asdict(f) for f in st.session_state.facturas])

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month

    if filtro_rfc:
        df = df[df["rfc_emisor"].str.contains(filtro_rfc, case=False, na=False)]

    st.subheader("Facturas cargadas")
    st.dataframe(df)

    st.subheader("calcular totales por año")
    totales_anio = df.groupby("anio")["total"].sum().reset_index()
    st.dataframe(totales_anio)

    st.subheader("calcular totales por mes")
    totales_mes = df.groupby(["anio", "mes"])["total"].sum().reset_index()
    st.dataframe(totales_mes)

    st.subheader("calcular impuestos pagados por año")
    impuestos_anio = df.groupby("anio")["impuesto"].sum().reset_index()
    st.dataframe(impuestos_anio)

    st.subheader("calcular impuestos pagados por mes")
    impuestos_mes = df.groupby(["anio", "mes"])["impuesto"].sum().reset_index()
    st.dataframe(impuestos_mes)

    st.subheader("calcular totales e impuestos por año y mes por RFC emisor")
    rfc_anio_mes = (
        df.groupby(["rfc_emisor", "anio", "mes"])[["total", "impuesto"]]
        .sum()
        .reset_index()
    )
    st.dataframe(rfc_anio_mes)

    st.subheader("calcular totales e impuestos por año y mes por concepto")
    df["concepto_texto"] = df["concepto"].apply(
        lambda c: ", ".join(c) if isinstance(c, tuple) else str(c)
    )
    concepto_anio_mes = (
        df.groupby(["concepto_texto", "anio", "mes"])[["total", "impuesto"]]
        .sum()
        .reset_index()
    )
    st.dataframe(concepto_anio_mes)

    st.subheader("calcular totales e impuestos por año y mes por uso de CFDI")
    uso_anio_mes = (
        df.groupby(["uso_cfdi", "anio", "mes"])[["total", "impuesto"]]
        .sum()
        .reset_index()
    )
    st.dataframe(uso_anio_mes)

    st.title("Gráfico de gastos por mes de los conceptos anteriores")
    totales_mes["anio_mes"] = (
        totales_mes["anio"].astype(str)
        + "-"
        + totales_mes["mes"].astype(str).str.zfill(2)
    )
    grafico_df = totales_mes.set_index("anio_mes")[["total"]]
    st.line_chart(grafico_df)

    pdf_bytes = generar_pdf(
        totales_anio,
        totales_mes,
        impuestos_anio,
        impuestos_mes,
        rfc_anio_mes,
        concepto_anio_mes,
        uso_anio_mes
    )

    st.download_button(
        label="Descargar reporte en PDF",
        data=pdf_bytes,
        file_name="reporte_gastos.pdf",
        mime="application/pdf"
    )
else:
    st.info("No hay facturas cargadas")

        
