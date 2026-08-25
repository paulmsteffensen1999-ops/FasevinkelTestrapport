import io
import math
import re

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def byg_koblingsgrupper():
    """Return common IEC winding combinations with their clock numbers."""
    lige_klokketal = range(0, 12, 2)
    ulige_klokketal = range(1, 12, 2)
    gruppefamilier = [
        ("Yy", lige_klokketal),
        ("Dd", lige_klokketal),
        ("Yd", ulige_klokketal),
        ("Dy", ulige_klokketal),
        ("Yz", ulige_klokketal),
        ("Dz", ulige_klokketal),
        ("YNyn", lige_klokketal),
        ("YNd", ulige_klokketal),
        ("Dyn", ulige_klokketal),
        ("YNzn", ulige_klokketal),
        ("Dzn", ulige_klokketal),
        ("Yzn", ulige_klokketal),
        ("Dynz", ulige_klokketal),
    ]
    standardgrupper = [
        f"{familie}{klokketal}"
        for familie, klokketal_liste in gruppefamilier
        for klokketal in klokketal_liste
    ]
    sammensatte_grupper = [
        "YNd11d11",
        "YNyn0 (d)",
        *[f"YNyn0+d{klokketal}" for klokketal in range(1, 12, 2)],
    ]
    return standardgrupper + sammensatte_grupper


def generer_pdf_bytes(
    station,
    trafo_id,
    kobling,
    primaer_maaleplacering,
    sekundaer_maaleplacering,
    pri_vinkler,
    sek_vinkler,
):
    """Build the phase-shift report and return its PDF bytes and chart."""
    er_koblingsgruppe_ikke_relevant = (
        kobling == "ikke relevant (Teoretisk: 0°)"
    )
    klokketal_match = re.search(r"\d{1,2}", kobling)
    if klokketal_match:
        uretal = int(klokketal_match.group())
    else:
        uretal = 0

    forventet_forskydning = (uretal * 30) % 360
    forskydninger = []
    status = []
    min_vinkel = (forventet_forskydning - 15) % 360
    max_vinkel = (forventet_forskydning + 15) % 360

    for primaer, sekundaer in zip(pri_vinkler, sek_vinkler):
        diff = (sekundaer - primaer) % 360
        forskydninger.append(round(diff, 1))
        er_indenfor_tolerance = (
            min_vinkel <= diff <= max_vinkel
            if min_vinkel <= max_vinkel
            else diff >= min_vinkel or diff <= max_vinkel
        )
        status.append(
            f"GODKENDT ({kobling})" if er_indenfor_tolerance else "AFVIGELSE"
        )

    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location("N")

    fase_farver = ["#2B6CB0", "#ECC94B", "#E53E3E"]
    fase_navne = ["L1", "L2", "L3"]

    for vinkel, farve, navn in zip(pri_vinkler, fase_farver, fase_navne):
        radianer = math.radians(vinkel)
        ax.annotate(
            "",
            xy=(radianer, 0.95),
            xytext=(0, 0),
            arrowprops=dict(
                arrowstyle="->", linestyle="--", color=farve, linewidth=2
            ),
        )
        ax.text(
            radianer,
            1.15,
            f"{navn} Pri",
            color=farve,
            fontweight="bold",
            ha="center",
            va="center",
        )

    for vinkel, farve, navn in zip(sek_vinkler, fase_farver, fase_navne):
        radianer = math.radians(vinkel)
        ax.annotate(
            "",
            xy=(radianer, 0.85),
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color=farve, linewidth=3.5),
        )
        ax.text(
            radianer,
            0.72,
            f"{navn} Sek",
            color=farve,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="square,pad=0.2",
                facecolor="white",
                edgecolor=farve,
                linewidth=1,
                alpha=0.8,
            ),
        )

    ax.set_ylim(0, 1.2)
    ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad(np.arange(0, 360, 30)))
    ax.set_xticklabels([f"{vinkel}°" for vinkel in range(0, 360, 30)])
    ax.grid(True, color="#CBD5E0", linestyle=":")

    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=200)
    img_buf.seek(0)

    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "T1",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=15,
    )
    meta_style = ParagraphStyle(
        "M1",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#4A5568"),
    )
    cell_style = ParagraphStyle(
        "C1", parent=styles["Normal"], fontSize=10, alignment=1
    )
    cell_hdr = ParagraphStyle(
        "CH",
        parent=styles["Normal"],
        fontSize=10,
        alignment=1,
        textColor=colors.white,
    )
    koblingsgruppe_rapport = (
        "<b>Transformer Koblingsgruppe:</b> Transformer Koblingsgruppe "
        "er ikke relevant da der ikke måles på tværs af en transformer<br/>"
        if er_koblingsgruppe_ikke_relevant
        else f"<b>Transformer Koblingsgruppe:</b> {kobling} "
        f"(Teoretisk: {forventet_forskydning}° lagging)<br/>"
    )

    story = [
        Paragraph("FASEVINKEL TESTRAPPORT", title_style),
        Paragraph(
            koblingsgruppe_rapport
            + f"<b>Station:</b> {station}<br/>"
            f"<b>Transformer ID:</b> {trafo_id}<br/>"
            f"<b>Primær måling udført ved:</b> {primaer_maaleplacering}<br/>"
            f"<b>Sekundær måling udført ved:</b> {sekundaer_maaleplacering}",
            meta_style,
        ),
        Spacer(1, 15),
    ]

    data = [
        [
            Paragraph("Fase", cell_hdr),
            Paragraph("Primær Vinkel", cell_hdr),
            Paragraph("Sekundær Vinkel", cell_hdr),
            Paragraph("Målt Forskydning", cell_hdr),
            Paragraph("Status", cell_hdr),
        ],
        *[
            [
                Paragraph(f"<b>{navn} ({farve_navn})</b>", cell_style),
                Paragraph(f"{primaer}°", cell_style),
                Paragraph(f"{sekundaer}°", cell_style),
                Paragraph(f"{forskydning}°", cell_style),
                Paragraph(f"<b>{fase_status}</b>", cell_style),
            ]
            for navn, farve_navn, primaer, sekundaer, forskydning, fase_status in zip(
                fase_navne,
                ["Blå", "Gul", "Rød"],
                pri_vinkler,
                sek_vinkler,
                forskydninger,
                status,
            )
        ],
    ]

    tabel = Table(data, colWidths=[80, 100, 100, 110, 130])
    tabel.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F7FAFC")),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#F7FAFC")),
            ]
        )
    )
    story.extend([tabel, Spacer(1, 20), KeepTogether([Image(img_buf, width=310, height=310)]), Spacer(1, 25)])

    sig_data = [
        [
            Paragraph("<b>Udført af:</b> _______________________", meta_style),
            Paragraph("<b>Dato:</b> ____/____ - 20__", meta_style),
        ],
        [
            Paragraph("<b>Godkendt af:</b> _______________________", meta_style),
            Paragraph("<b>Signatur:</b> _______________________", meta_style),
        ],
    ]
    story.append(Table(sig_data, colWidths=[260, 260]))

    doc.build(story)
    pdf_buf.seek(0)
    return pdf_buf.getvalue(), fig


st.set_page_config(page_title="Fasevinkel Generator", layout="wide")
st.title("⚡ Fasevinkel Testrapport Generator")
st.subheader("Skabelon til NDB SPI-III (Lagging / Med uret)")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Stamdata")
    station_navn = st.text_input("Stationsnavn", "")
    trafo_navn = st.text_input("Transformer ID / Navn", "")
    primaer_maaleplacering = st.text_input(
        "Hvor/navn for primær måling", ""
    )
    sekundaer_maaleplacering = st.text_input(
        "Hvor/navn for sekundær måling", ""
    )
    koblingsgrupper = byg_koblingsgrupper()
    koblingsgruppe = st.selectbox(
        "Valg af Koblingsgruppe",
        ["", "ikke relevant (Teoretisk: 0°)"] + koblingsgrupper,
        index=0,
    )

    st.header("2. Måleresultater (Grader °)")
    c_l1, c_l2 = st.columns(2)
    with c_l1:
        p1 = st.number_input("L1 Primær", value=None, step=0.1)
        p2 = st.number_input("L2 Primær", value=None, step=0.1)
        p3 = st.number_input("L3 Primær", value=None, step=0.1)
    with c_l2:
        s1 = st.number_input("L1 Sekundær", value=None, step=0.1)
        s2 = st.number_input("L2 Sekundær", value=None, step=0.1)
        s3 = st.number_input("L3 Sekundær", value=None, step=0.1)

alle_maalinger = [p1, p2, p3, s1, s2, s3]
if koblingsgruppe and all(maaling is not None for maaling in alle_maalinger):
    pdf_data, diagram_fig = generer_pdf_bytes(
        station_navn,
        trafo_navn,
        koblingsgruppe,
        primaer_maaleplacering,
        sekundaer_maaleplacering,
        [p1, p2, p3],
        [s1, s2, s3],
    )
else:
    pdf_data = None
    diagram_fig = None

with col2:
    st.header("3. Live Vektordiagram")
    if diagram_fig is not None:
        st.pyplot(diagram_fig)
    else:
        st.info("Udfyld koblingsgruppe og alle måleresultater for at se diagrammet.")

    st.header("4. Eksport")
    if pdf_data is not None:
        st.download_button(
            label="📥 DOWNLOAD PDF RAPPORT",
            data=pdf_data,
            file_name=f"Fasevinkel_Rapport_{station_navn.replace(' ', '_')}.pdf",
            mime="application/pdf",
        )
