"""
Export service for generating reports
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
import pandas as pd
from typing import List, Dict


class ExportService:
    """Service for exporting reports"""
    
    def generate_bill_pdf(self, user_data: dict, prediction_data: dict, usage_data: List[dict]) -> BytesIO:
        """Generate PDF bill report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        elements.append(Paragraph("⚡ Electricity Bill Report", title_style))
        elements.append(Spacer(1, 20))
        
        # User info
        user_info = [
            ["Customer Name:", user_data.get('full_name', 'N/A')],
            ["Email:", user_data.get('email', 'N/A')],
            ["Report Date:", datetime.now().strftime("%B %d, %Y")],
        ]
        
        user_table = Table(user_info, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(user_table)
        elements.append(Spacer(1, 30))
        
        # Prediction Summary
        elements.append(Paragraph("Bill Prediction Summary", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        prediction_data_table = [
            ["Metric", "Value"],
            ["Predicted Bill Amount", f"₹{prediction_data.get('predicted_bill_amount', 0):.2f}"],
            ["Current Consumption", f"{prediction_data.get('current_consumption_kwh', 0):.2f} kWh"],
            ["Days Remaining", str(prediction_data.get('days_remaining', 0))],
            ["Confidence Score", f"{prediction_data.get('confidence_score', 0)*100:.0f}%"],
            ["Prediction Method", prediction_data.get('prediction_method', 'N/A')],
            ["vs Previous Month", f"{prediction_data.get('percentage_change', 0):+.1f}%"],
        ]
        
        pred_table = Table(prediction_data_table, colWidths=[3*inch, 2*inch])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(pred_table)
        elements.append(Spacer(1, 30))
        
        # Usage History
        if usage_data:
            elements.append(Paragraph("Recent Usage History", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            usage_table_data = [["Date", "Consumption (kWh)"]]
            for usage in usage_data[:10]:  # Last 10 days
                usage_table_data.append([
                    usage.get('date', 'N/A'),
                    f"{usage.get('consumption_kwh', 0):.2f}"
                ])
            
            usage_table = Table(usage_table_data, colWidths=[3*inch, 2*inch])
            usage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(usage_table)
        
        # Footer
        elements.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph(
            "Generated by AI-Powered Electricity Billing System | Powered by Machine Learning",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_usage_csv(self, usage_data: List[dict]) -> BytesIO:
        """Generate CSV of usage data"""
        df = pd.DataFrame(usage_data)
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer
    
    def generate_usage_excel(self, usage_data: List[dict], prediction_data: dict) -> BytesIO:
        """Generate Excel report with multiple sheets"""
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Usage data sheet
            df_usage = pd.DataFrame(usage_data)
            df_usage.to_excel(writer, sheet_name='Usage History', index=False)
            
            # Prediction summary sheet
            df_prediction = pd.DataFrame([prediction_data])
            df_prediction.to_excel(writer, sheet_name='Prediction', index=False)
        
        buffer.seek(0)
        return buffer


export_service = ExportService()