"""
PDF Evidence Report Generator
Uses ReportLab to produce a legally-structured evidence document.
Called from the Streamlit dashboard when user clicks Export.
"""

import os
import hmac
import hashlib
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import api


HMAC_SECRET = b"digital_asset_protection_secret_2026"
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def _verify_hmac(entry: dict) -> bool:
    """Re-compute HMAC and check against stored signature."""
    fields = [
        entry["asset_id"], entry["event_type"],
        entry["recipient"], entry["notes"], entry["timestamp"]
    ]
    message = "|".join(str(f) for f in fields)
    expected = hmac.new(HMAC_SECRET, message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, entry.get("hmac_sig", ""))


def generate_report(asset_id: str, output_path: str = None) -> str:
    """
    Generate a full evidence report PDF for the given asset.
    Returns the path to the generated PDF file.
    """
    # Fetch data
    assets = api.get_asset_list()
    asset = next((a for a in assets if a["asset_id"] == asset_id), None)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found in registry.")

    trail = api.get_custody_trail(asset_id)

    # Prepare output path
    if not output_path:
        os.makedirs(REPORT_DIR, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_report_{asset_id}_{timestamp_str}.pdf"
        output_path = os.path.join(REPORT_DIR, filename)

    # Build document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=25*mm,
        bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=20,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#16213e"),
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        leading=14,
    )

    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#888888"),
    )

    elements = []

    # ---- Header ----
    elements.append(Paragraph("DIGITAL ASSET PROTECTION", title_style))
    elements.append(Paragraph("Evidence Report -- Confidential", subtitle_style))
    elements.append(HRFlowable(
        width="100%", thickness=2,
        color=colors.HexColor("#0f3460"), spaceAfter=12
    ))

    # Report metadata
    report_id = hashlib.sha256(
        f"{asset_id}_{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16].upper()

    meta_data = [
        ["Report ID:", report_id],
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")],
        ["Asset ID:", asset_id],
        ["Classification:", "CONFIDENTIAL -- LEGAL EVIDENCE"],
    ]
    meta_table = Table(meta_data, colWidths=[120, 350])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#333333")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 16))

    # ---- Section 1: Asset Identity ----
    elements.append(Paragraph("1. Asset Identity and Fingerprint", heading_style))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#cccccc"), spaceAfter=8
    ))

    identity_data = [
        ["Field", "Value"],
        ["Asset ID", asset["asset_id"]],
        ["Name", asset["name"]],
        ["Owner Organization", asset["owner_org"]],
        ["Registered At", asset["registered_at"]],
    ]
    identity_table = Table(identity_data, colWidths=[140, 330])
    identity_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    elements.append(identity_table)
    elements.append(Spacer(1, 12))

    # ---- Section 2: Digital Fingerprint ----
    elements.append(Paragraph("2. Digital Fingerprint (Media DNA)", heading_style))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#cccccc"), spaceAfter=8
    ))

    dna_data = [
        ["Component", "Value"],
        ["Perceptual Hash (pHash)", asset.get("phash", "N/A")],
        ["Histogram Signature", asset.get("histogram_sig", "N/A")],
        ["Metadata SHA-256", asset.get("metadata_sha", "N/A")],
        ["Combined DNA", asset.get("dna_combined", "N/A")],
    ]
    dna_table = Table(dna_data, colWidths=[160, 310])
    dna_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    elements.append(dna_table)
    elements.append(Spacer(1, 12))

    # ---- Section 3: Chain of Custody ----
    elements.append(Paragraph("3. Chain of Custody", heading_style))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#cccccc"), spaceAfter=8
    ))

    if trail:
        custody_data = [["#", "Timestamp", "Event", "Recipient", "HMAC Status"]]
        for i, entry in enumerate(trail, 1):
            hmac_ok = _verify_hmac(entry)
            status_text = "VERIFIED" if hmac_ok else "TAMPERED"
            custody_data.append([
                str(i),
                entry["timestamp"],
                entry["event_type"].upper(),
                entry.get("recipient", "N/A"),
                status_text,
            ])

        custody_table = Table(custody_data, colWidths=[30, 120, 80, 140, 100])
        custody_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]

        # Color-code event types and HMAC status
        for i, entry in enumerate(trail, 1):
            if entry["event_type"] == "violated":
                custody_styles.append(
                    ("TEXTCOLOR", (2, i), (2, i), colors.HexColor("#dc3545"))
                )
            elif entry["event_type"] == "licensed":
                custody_styles.append(
                    ("TEXTCOLOR", (2, i), (2, i), colors.HexColor("#28a745"))
                )
            elif entry["event_type"] == "distributed":
                custody_styles.append(
                    ("TEXTCOLOR", (2, i), (2, i), colors.HexColor("#007bff"))
                )

            hmac_ok = _verify_hmac(entry)
            if hmac_ok:
                custody_styles.append(
                    ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#28a745"))
                )
            else:
                custody_styles.append(
                    ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#dc3545"))
                )

        custody_table.setStyle(TableStyle(custody_styles))
        elements.append(custody_table)
    else:
        elements.append(Paragraph("No custody events recorded for this asset.", body_style))

    elements.append(Spacer(1, 12))

    # ---- Section 4: Violation Summary ----
    violations = [e for e in trail if e["event_type"] == "violated"]
    elements.append(Paragraph("4. Violation Summary", heading_style))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#cccccc"), spaceAfter=8
    ))

    if violations:
        for v in violations:
            elements.append(Paragraph(
                f"<b>Violation Detected:</b> {v['timestamp']}", body_style
            ))
            elements.append(Paragraph(
                f"<b>Recipient / Source:</b> {v.get('recipient', 'Unknown')}", body_style
            ))
            elements.append(Paragraph(
                f"<b>Notes:</b> {v.get('notes', 'None')}", body_style
            ))
            hmac_ok = _verify_hmac(v)
            elements.append(Paragraph(
                f"<b>Record Integrity:</b> {'HMAC Verified -- record has not been tampered with' if hmac_ok else 'WARNING: HMAC verification failed -- possible tampering'}",
                body_style
            ))
            elements.append(Spacer(1, 8))
    else:
        elements.append(Paragraph(
            "No violations recorded for this asset at the time of report generation.",
            body_style
        ))

    elements.append(Spacer(1, 20))

    # ---- Footer ----
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#0f3460"), spaceAfter=8
    ))

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        f"Report generated by Digital Asset Protection System | "
        f"Report ID: {report_id} | "
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        footer_style
    ))
    elements.append(Paragraph(
        "This document is confidential and intended for authorized recipients only. "
        "Unauthorized distribution is prohibited.",
        footer_style
    ))

    # Build PDF
    doc.build(elements)
    return output_path


if __name__ == "__main__":
    path = generate_report("ASSET_001")
    print(f"[OK] Report generated: {path}")
