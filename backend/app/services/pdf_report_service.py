import io
import datetime
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from ..schemas.prescription import PrescriptionResponse

class PDFReportService:
    @staticmethod
    def generate_prescription_report(prescription: PrescriptionResponse) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom professional typography
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f2744'),
            alignment=TA_LEFT
        )
        tagline_style = ParagraphStyle(
            'ReportTagline',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0f766e'),
            alignment=TA_LEFT
        )
        meta_style = ParagraphStyle(
            'ReportMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#475569'),
            alignment=TA_RIGHT
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#0f2744'),
            spaceBefore=10,
            spaceAfter=6
        )
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1e293b')
        )
        cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=cell_style,
            fontName='Helvetica-Bold'
        )
        cell_green = ParagraphStyle(
            'TableCellGreen',
            parent=cell_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0f766e')
        )
        cell_amber = ParagraphStyle(
            'TableCellAmber',
            parent=cell_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#b45309')
        )
        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#334155')
        )

        elements = []

        # Header Table: Title & Tagline on Left, Report ID & Timestamp on Right
        gen_time = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%b-%Y %H:%M UTC")
        rep_id = f"REP-{prescription.prescription_id.replace('RX-', '')}"

        header_data = [
            [
                Paragraph("<b>MedLedger</b>", title_style),
                Paragraph(f"<b>Report ID:</b> {rep_id}<br/><b>Generated:</b> {gen_time}<br/><b>Prescription ID:</b> {prescription.prescription_id}", meta_style)
            ],
            [
                Paragraph("Every medicine match. Every price. Every claim backed by evidence.", tagline_style),
                Paragraph("Pharmacist & Clinical Audit Report", meta_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[320, 220])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d9488'), spaceBefore=2, spaceAfter=10))

        # Executive 3-Totals Summary Cards Table
        summary = prescription.summary
        s_data = [
            [
                Paragraph("<b>CONFIRMED POTENTIAL SAVINGS</b>", ParagraphStyle('SH', parent=cell_bold, fontSize=7, textColor=colors.HexColor('#0f766e'))),
                Paragraph("<b>UNRESOLVED ITEMS</b>", ParagraphStyle('SH', parent=cell_bold, fontSize=7, textColor=colors.HexColor('#b45309'))),
                Paragraph("<b>EXCLUDED ESTIMATE</b>", ParagraphStyle('SH', parent=cell_bold, fontSize=7, textColor=colors.HexColor('#64748b')))
            ],
            [
                Paragraph(f"<font size=14 color='#065f46'><b>₹{summary.confirmed_total_savings_inr:.2f}</b></font><br/><font size=7 color='#0d9488'><b>{summary.confirmed_savings_percentage}% overall reduction</b></font>", cell_style),
                Paragraph(f"<font size=14 color='#92400e'><b>{summary.unresolved_items_count} of {summary.total_items_count}</b></font><br/><font size=7 color='#78350f'>Quarantined from totals</font>", cell_style),
                Paragraph(
                    f"<font size=14 color='#475569'><b>₹{summary.excluded_potential_savings_inr:.2f}</b></font><br/><font size=7 color='#64748b'>Unverified estimate (excluded)</font>"
                    if summary.excluded_potential_savings_inr is not None
                    else "<font size=11 color='#94a3b8'><b>Cannot estimate</b></font><br/><font size=7 color='#94a3b8'>Insufficient evidence</font>",
                    cell_style
                )
            ]
        ]
        sum_table = Table(s_data, colWidths=[180, 180, 180])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 1), colors.HexColor('#f0fdfa')),
            ('BACKGROUND', (1, 0), (1, 1), colors.HexColor('#fffbeb')),
            ('BACKGROUND', (2, 0), (2, 1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (0, 1), 1, colors.HexColor('#99f6e4')),
            ('BOX', (1, 0), (1, 1), 1, colors.HexColor('#fde68a')),
            ('BOX', (2, 0), (2, 1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(sum_table)
        elements.append(Spacer(1, 12))

        # Section: Itemized Prescription Evidence Table
        elements.append(Paragraph("<b>Prescription Line Items & Candidate Alternatives</b>", section_heading))
        
        table_rows = [
            [
                Paragraph("<b>Prescribed Item</b>", cell_bold),
                Paragraph("<b>PMBJP Generic Match</b>", cell_bold),
                Paragraph("<b>Status</b>", cell_bold),
                Paragraph("<b>Ref Price</b>", cell_bold),
                Paragraph("<b>PMBJP Price</b>", cell_bold),
                Paragraph("<b>Saving (₹)</b>", cell_bold),
                Paragraph("<b>Evidence ID</b>", cell_bold)
            ]
        ]

        for item in prescription.items:
            is_verified = (item.verification_status == "VERIFIED_FOR_PRICE_COMPARISON" and item.is_eligible_for_savings)
            status_p = Paragraph("Verified Match", cell_green) if is_verified else Paragraph("Needs Clarification", cell_amber)
            ref_str = f"₹{item.reference_price_inr:.2f}" if item.reference_price_inr is not None else (f"₹{item.user_reference_price_inr:.2f}" if item.user_reference_price_inr else "Unquoted")
            gen_str = f"₹{item.comparison_price_inr:.2f}" if item.comparison_price_inr is not None else (f"₹{item.candidate_mrp_inr:.2f}" if item.candidate_mrp_inr else "N/A")
            sav_str = f"+₹{item.calculated_saving_inr:.2f}" if is_verified and item.calculated_saving_inr is not None else "Quarantined"
            ev_id = item.evidence_decision_id or "DEC-UNVERIFIED"

            table_rows.append([
                Paragraph(f"<b>{item.prescribed_name}</b><br/><font size=6.5 color='#64748b'>{item.original_text}</font>", cell_style),
                Paragraph(f"{item.candidate_name or 'No generic selected'}<br/><font size=6.5 color='#64748b'>{item.candidate_id or ''} • {item.candidate_unit_size or ''}</font>", cell_style),
                status_p,
                Paragraph(ref_str, cell_style),
                Paragraph(gen_str, cell_style),
                Paragraph(sav_str, cell_green if is_verified else cell_amber),
                Paragraph(f"<font size=6.5 color='#0f766e'>{ev_id}</font>", cell_style)
            ])

        item_table = Table(table_rows, colWidths=[105, 135, 75, 55, 55, 60, 55])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 12))

        # Section: Audit Notes on Unresolved Items (if any)
        unresolved_items = [i for i in prescription.items if not (i.verification_status == "VERIFIED_FOR_PRICE_COMPARISON" and i.is_eligible_for_savings)]
        if unresolved_items:
            elements.append(Paragraph("<b>Audit Log: Quarantined & Unresolved Items</b>", section_heading))
            audit_rows = [
                [
                    Paragraph("<b>Item Name</b>", cell_bold),
                    Paragraph("<b>Reason for Exclusion from Confirmed Savings</b>", cell_bold)
                ]
            ]
            for u in unresolved_items:
                reason = u.ineligible_reason or "Missing clinical attribute, omitted strength, or unrecorded reference brand price."
                audit_rows.append([
                    Paragraph(f"<b>{u.prescribed_name}</b>", cell_style),
                    Paragraph(reason, cell_style)
                ])
            audit_table = Table(audit_rows, colWidths=[130, 410])
            audit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fff7ed')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fed7aa')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(audit_table)
            elements.append(Spacer(1, 12))

        # Section: Pharmacist & Physician Clinical Legal Notice
        elements.append(KeepTogether([
            Paragraph("<b>MANDATORY CLINICAL & REGULATORY NOTICE</b>", ParagraphStyle('NoteH', parent=cell_bold, fontSize=8, textColor=colors.HexColor('#991b1b'))),
            Spacer(1, 3),
            Paragraph(
                "This report is generated by MedLedger for informational price transparency using official datasets "
                "(PMBJP catalogue and NPPA DPCO statutory ceiling prices). It does NOT constitute medical advice, diagnosis, "
                "or generic substitution authorization. "
                "Generic substitution must always be evaluated, confirmed, and dispensed under the clinical discretion of a qualified "
                "registered medical practitioner or licensed pharmacist. MedLedger strictly quarantines unresolved items to ensure "
                "no unsubstantiated financial or clinical claims are made.",
                disclaimer_style
            )
        ]))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
