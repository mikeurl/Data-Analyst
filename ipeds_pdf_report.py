"""
IPEDS Fall Enrollment PDF Report Generator

This module generates downloadable PDF reports containing IPEDS Fall Enrollment
data formatted for easy entry into the NCES IPEDS system.

Uses ReportLab for PDF generation. Falls back to HTML if ReportLab is not available.
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

# Try to import ReportLab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, PageBreak, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class IPEDSPDFReportGenerator:
    """
    Generates PDF reports for IPEDS Fall Enrollment data.

    Creates formatted PDF documents containing Parts A, B, C, E, and F
    data ready for manual entry into the NCES IPEDS system.
    """

    def __init__(self):
        """Initialize the PDF generator."""
        self.styles = None
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            # Add custom styles
            self.styles.add(ParagraphStyle(
                name='IPEDSTitle',
                parent=self.styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=20
            ))
            self.styles.add(ParagraphStyle(
                name='IPEDSSubtitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=12
            ))
            self.styles.add(ParagraphStyle(
                name='IPEDSPartTitle',
                parent=self.styles['Heading2'],
                fontSize=12,
                spaceAfter=10,
                spaceBefore=20
            ))

    def _create_table_style(self) -> TableStyle:
        """Create a standard table style for IPEDS tables."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D6DCE4')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E7E6E6')]),
            # Bold the last row (totals)
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#B4C6E7')),
        ])

    def _df_to_table_data(self, df: pd.DataFrame, include_index: bool = True) -> list:
        """Convert DataFrame to list of lists for ReportLab table."""
        if include_index:
            # Include index as first column
            headers = [''] + list(df.columns)
            data = [headers]
            for idx, row in df.iterrows():
                data.append([str(idx)] + [str(v) for v in row.values])
        else:
            headers = list(df.columns)
            data = [headers]
            for _, row in df.iterrows():
                data.append([str(v) for v in row.values])
        return data

    def generate_pdf(self, report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate a PDF report from IPEDS data.

        Args:
            report_data: Dictionary containing IPEDS report data
            output_path: Optional path for the output file

        Returns:
            Path to the generated PDF file
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_html_fallback(report_data, output_path)

        if output_path is None:
            output_path = os.path.join(
                tempfile.gettempdir(),
                f"IPEDS_Fall_Enrollment_{report_data['term'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        elements = []

        # Title
        elements.append(Paragraph(
            "IPEDS Fall Enrollment Report",
            self.styles['IPEDSTitle']
        ))
        elements.append(Paragraph(
            f"{report_data['term']}",
            self.styles['IPEDSSubtitle']
        ))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 20))

        # Part A: Enrollment by Race/Ethnicity and Gender
        elements.append(Paragraph("Part A: Enrollment by Race/Ethnicity and Gender", self.styles['IPEDSPartTitle']))

        for status, label in [('full_time', 'Full-time Undergraduate'), ('part_time', 'Part-time Undergraduate')]:
            df = report_data['part_a'][status]
            elements.append(Paragraph(f"{label} Students", self.styles['Heading3']))
            elements.append(Spacer(1, 5))

            table_data = self._df_to_table_data(df)
            table = Table(table_data, repeatRows=1)
            table.setStyle(self._create_table_style())
            elements.append(table)
            elements.append(Spacer(1, 15))

        elements.append(PageBreak())

        # Part B: Enrollment by Age
        elements.append(Paragraph("Part B: Enrollment by Age", self.styles['IPEDSPartTitle']))
        df = report_data['part_b']
        table_data = self._df_to_table_data(df)
        table = Table(table_data, repeatRows=1)
        table.setStyle(self._create_table_style())
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Part C: Residence of First-time Students
        elements.append(Paragraph("Part C: Residence of First-time Students", self.styles['IPEDSPartTitle']))
        df = report_data['part_c']
        table_data = self._df_to_table_data(df, include_index=False)
        table = Table(table_data, repeatRows=1)
        table.setStyle(self._create_table_style())
        elements.append(table)
        elements.append(Spacer(1, 20))

        elements.append(PageBreak())

        # Part E: Retention Rates
        part_e = report_data['part_e']
        elements.append(Paragraph(f"Part E: Retention Rates (Cohort Year: {part_e['cohort_year']})", self.styles['IPEDSPartTitle']))

        retention_data = [
            ['', 'Full-time', 'Part-time'],
            ['Initial Cohort', str(part_e['full_time']['cohort']), str(part_e['part_time']['cohort'])],
            ['Exclusions', str(part_e['full_time']['exclusions']), str(part_e['part_time']['exclusions'])],
            ['Adjusted Cohort', str(part_e['full_time']['adjusted_cohort']), str(part_e['part_time']['adjusted_cohort'])],
            ['Retained or Completed', str(part_e['full_time']['retained_or_completed']), str(part_e['part_time']['retained_or_completed'])],
            ['Retention Rate', f"{part_e['full_time']['retention_rate']}%", f"{part_e['part_time']['retention_rate']}%"]
        ]
        table = Table(retention_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        table.setStyle(self._create_table_style())
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Part F: Student-to-Faculty Ratio
        part_f = report_data['part_f']
        elements.append(Paragraph(f"Part F: Student-to-Faculty Ratio", self.styles['IPEDSPartTitle']))

        ratio_data = [
            ['Metric', 'Value'],
            ['Full-time Students', str(part_f['full_time_students'])],
            ['Part-time Students', str(part_f['part_time_students'])],
            ['Student FTE', str(part_f['student_fte'])],
            ['Faculty FTE', str(part_f['faculty_fte'])],
            ['Student-to-Faculty Ratio', part_f['ratio_display']]
        ]
        table = Table(ratio_data, colWidths=[2.5*inch, 1.5*inch])
        table.setStyle(self._create_table_style())
        elements.append(table)

        # Footer note
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "This report was generated from synthetic data for demonstration purposes. "
            "Please verify all data before entering into the official IPEDS system.",
            self.styles['Normal']
        ))

        # Build PDF
        doc.build(elements)
        return output_path

    def _generate_html_fallback(self, report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate an HTML report when ReportLab is not available.

        Args:
            report_data: Dictionary containing IPEDS report data
            output_path: Optional path for the output file

        Returns:
            Path to the generated HTML file
        """
        if output_path is None:
            output_path = os.path.join(
                tempfile.gettempdir(),
                f"IPEDS_Fall_Enrollment_{report_data['term'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )

        html = """
<!DOCTYPE html>
<html>
<head>
    <title>IPEDS Fall Enrollment Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #1f4e79; text-align: center; }
        h2 { color: #2e75b6; border-bottom: 2px solid #2e75b6; padding-bottom: 5px; }
        h3 { color: #4472c4; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th { background-color: #4472c4; color: white; padding: 10px; text-align: center; }
        td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr:last-child { font-weight: bold; background-color: #b4c6e7; }
        .note { font-style: italic; color: #666; margin-top: 30px; }
        @media print { body { margin: 20px; } }
    </style>
</head>
<body>
"""
        html += f"<h1>IPEDS Fall Enrollment Report</h1>"
        html += f"<h2 style='text-align: center; border: none;'>{report_data['term']}</h2>"
        html += f"<p style='text-align: center;'>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>"

        # Part A
        html += "<h2>Part A: Enrollment by Race/Ethnicity and Gender</h2>"
        for status, label in [('full_time', 'Full-time Undergraduate'), ('part_time', 'Part-time Undergraduate')]:
            df = report_data['part_a'][status]
            html += f"<h3>{label} Students</h3>"
            html += df.to_html(classes='ipeds-table')

        # Part B
        html += "<h2>Part B: Enrollment by Age</h2>"
        html += report_data['part_b'].to_html(classes='ipeds-table')

        # Part C
        html += "<h2>Part C: Residence of First-time Students</h2>"
        html += report_data['part_c'].to_html(classes='ipeds-table', index=False)

        # Part E
        part_e = report_data['part_e']
        html += f"<h2>Part E: Retention Rates (Cohort Year: {part_e['cohort_year']})</h2>"
        html += """<table>
            <tr><th></th><th>Full-time</th><th>Part-time</th></tr>
        """
        html += f"<tr><td>Initial Cohort</td><td>{part_e['full_time']['cohort']}</td><td>{part_e['part_time']['cohort']}</td></tr>"
        html += f"<tr><td>Exclusions</td><td>{part_e['full_time']['exclusions']}</td><td>{part_e['part_time']['exclusions']}</td></tr>"
        html += f"<tr><td>Adjusted Cohort</td><td>{part_e['full_time']['adjusted_cohort']}</td><td>{part_e['part_time']['adjusted_cohort']}</td></tr>"
        html += f"<tr><td>Retained or Completed</td><td>{part_e['full_time']['retained_or_completed']}</td><td>{part_e['part_time']['retained_or_completed']}</td></tr>"
        html += f"<tr><td>Retention Rate</td><td>{part_e['full_time']['retention_rate']}%</td><td>{part_e['part_time']['retention_rate']}%</td></tr>"
        html += "</table>"

        # Part F
        part_f = report_data['part_f']
        html += "<h2>Part F: Student-to-Faculty Ratio</h2>"
        html += f"""<table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Full-time Students</td><td>{part_f['full_time_students']}</td></tr>
            <tr><td>Part-time Students</td><td>{part_f['part_time_students']}</td></tr>
            <tr><td>Student FTE</td><td>{part_f['student_fte']}</td></tr>
            <tr><td>Faculty FTE</td><td>{part_f['faculty_fte']}</td></tr>
            <tr><td>Student-to-Faculty Ratio</td><td>{part_f['ratio_display']}</td></tr>
        </table>"""

        html += """
<p class="note">This report was generated from synthetic data for demonstration purposes.
Please verify all data before entering into the official IPEDS system.</p>
</body>
</html>
"""
        with open(output_path, 'w') as f:
            f.write(html)

        return output_path


def generate_ipeds_pdf(report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Convenience function to generate an IPEDS PDF report.

    Args:
        report_data: Dictionary containing IPEDS report data
        output_path: Optional path for the output file

    Returns:
        Path to the generated PDF/HTML file
    """
    generator = IPEDSPDFReportGenerator()
    return generator.generate_pdf(report_data, output_path)


if __name__ == "__main__":
    # Demo - requires ipeds_query_engine and database
    try:
        from ipeds_query_engine import get_ipeds_engine

        engine = get_ipeds_engine()
        terms = engine.get_available_terms()

        if terms:
            term = terms[0]
            print(f"Generating PDF report for {term}...")
            report = engine.generate_full_report(term)
            pdf_path = generate_ipeds_pdf(report)
            print(f"Report generated: {pdf_path}")
        else:
            print("No terms available. Run synthetic data generator first.")
    except Exception as e:
        print(f"Demo failed: {e}")
        print("Make sure to run create_ipeds_db_schema.py and SyntheticDataforSchema2.py first.")
