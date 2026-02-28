from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


class PDFBuilder:
    def build_consumption_report(
        self,
        data: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        title = Paragraph("<b>FactoryOPS - Energy Consumption Report</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        date_range = Paragraph(f"Period: {start_date} to {end_date}", styles['Normal'])
        story.append(date_range)
        story.append(Spacer(1, 0.3 * inch))
        
        summary_data = []
        for device in data.get("devices", []):
            summary_data.append([
                device.get("device_id", ""),
                f"{device.get('total_kwh', 0):.2f} kWh",
                f"{device.get('avg_power_w', 0):.2f} W",
                f"{device.get('peak_power_w', 0):.2f} W",
                f"{device.get('running_hours', 0):.2f} hrs"
            ])
        
        if summary_data:
            table_data = [["Device ID", "Total kWh", "Avg Power (W)", "Peak Power (W)", "Running Hours"]]
            table_data.extend(summary_data)
            
            t = Table(table_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)
        
        footer = Paragraph(f"<br/><br/>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        story.append(footer)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    def build_wastage_report(
        self,
        data: Dict[str, Any]
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        title = Paragraph("<b>FactoryOPS - Energy Wastage Report</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        summary = data.get("summary", {})
        
        summary_text = Paragraph(
            f"""
            <b>Summary:</b><br/>
            Total Wasted: {summary.get('total_wasted_kwh', 0):.2f} kWh<br/>
            Wasted Cost: ₹{summary.get('total_wasted_rupees', 0):.2f}<br/>
            Efficiency Score: {summary.get('efficiency_score', 0)}%<br/>
            Efficiency Grade: {summary.get('efficiency_grade', 'N/A')}<br/>
            """,
            styles['Normal']
        )
        story.append(summary_text)
        story.append(Spacer(1, 0.3 * inch))
        
        breakdown = data.get("breakdown", [])
        if breakdown:
            breakdown_data = [["Source", "Wasted (kWh)", "Percentage"]]
            for item in breakdown:
                breakdown_data.append([
                    item.get("source", ""),
                    f"{item.get('kwh', 0):.2f}",
                    f"{item.get('percent', 0):.1f}%"
                ])
            
            t = Table(breakdown_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)
        
        recommendations = data.get("recommendations", [])
        if recommendations:
            story.append(Spacer(1, 0.3 * inch))
            rec_title = Paragraph("<b>Recommendations:</b>", styles['Heading2'])
            story.append(rec_title)
            
            for rec in recommendations:
                rec_text = Paragraph(
                    f"{rec.get('rank')}. {rec.get('action')} (Potential savings: {rec.get('potential_savings_kwh', 0):.2f} kWh / ₹{rec.get('potential_savings_rupees', 0):.2f})",
                    styles['Normal']
                )
                story.append(rec_text)
        
        footer = Paragraph(f"<br/><br/>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        story.append(footer)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.read()


pdf_builder = PDFBuilder()
