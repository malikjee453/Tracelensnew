import json, html
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

def build_json_report(result):
    return json.dumps(result, indent=2, ensure_ascii=False, default=str).encode("utf-8")

def build_html_report(result):
    safe = lambda x: html.escape(str(x))
    findings = "".join(f"<li>{safe(x)}</li>" for x in result.get("findings", []))
    limitations = "".join(f"<li>{safe(x)}</li>" for x in result.get("limitations", []))
    metadata = safe(json.dumps(result.get("metadata", {}), indent=2, ensure_ascii=False, default=str))
    facts = result.get("file_facts", {})
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>TraceLens Forensics Report</title>
<style>body{{font:15px Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#202938}}h1{{color:#174a7e}}pre{{white-space:pre-wrap;background:#f3f5f7;padding:14px;border-radius:8px}}.warn{{background:#fff5df;padding:12px;border-left:4px solid #d99b22}}</style></head><body>
<h1>TraceLens Forensics</h1><h2>Digital Media Triage Report</h2>
<p><b>File:</b> {safe(facts.get('filename',''))}<br><b>Media type:</b> {safe(result.get('media_type'))}<br><b>SHA-256:</b> {safe(facts.get('sha256'))}<br><b>Examined:</b> {safe(result.get('analysis_timestamp',facts.get('examined_at_local','')))}</p>
<h3>Summary</h3><p>{safe(result.get('summary',''))}</p><h3>Findings</h3><ul>{findings}</ul>
<h3>Metadata</h3><pre>{metadata}</pre><h3>Limitations</h3><div class="warn"><ul>{limitations}</ul></div>
<p>Automated triage only; not a definitive authenticity or deepfake determination.</p></body></html>""".encode("utf-8")

def build_pdf_report(result):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallMono", parent=styles["Code"], fontSize=7, leading=9, wordWrap="CJK"))
    story = [Paragraph("TraceLens Forensics", styles["Title"]), Paragraph("Digital Media Triage Report", styles["Heading2"]), Spacer(1, 8)]
    facts = result.get("file_facts", {})
    rows = [["Field","Value"],["Filename",str(facts.get("filename",""))],["Media type",str(result.get("media_type",""))],
            ["Size (bytes)",str(facts.get("size_bytes",""))],["SHA-256",str(facts.get("sha256",""))],
            ["Examined",str(result.get("analysis_timestamp",facts.get("examined_at_local","")))]]
    table = Table(rows, colWidths=[38*mm, 130*mm])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#174a7e")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                               ("GRID",(0,0),(-1,-1),.4,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),8)]))
    story += [table, Spacer(1,12), Paragraph("Summary",styles["Heading2"]), Paragraph(str(result.get("summary","")),styles["BodyText"])]
    story.append(Paragraph("Findings",styles["Heading2"]))
    for finding in result.get("findings",[]): story.append(Paragraph("• "+str(finding),styles["BodyText"]))
    story.append(Paragraph("Metadata",styles["Heading2"]))
    story.append(Preformatted(json.dumps(result.get("metadata",{}),indent=2,ensure_ascii=False,default=str),styles["SmallMono"]))
    story.append(Paragraph("Limitations",styles["Heading2"]))
    for item in result.get("limitations",[]): story.append(Paragraph("• "+str(item),styles["BodyText"]))
    story.append(Spacer(1,10))
    story.append(Paragraph("Automated triage only. This report is not a definitive authenticity or deepfake determination.",styles["Italic"]))
    doc.build(story)
    return buf.getvalue()
