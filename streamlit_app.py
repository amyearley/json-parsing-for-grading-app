import streamlit as st
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from transcript_formatter import format_transcript

st.set_page_config(page_title="Transcript Formatter", layout="centered")

st.title("📞 Call Transcript Formatter")
st.write("Upload your call transcript JSON and get a formatted PDF ready for Claude Console.")

uploaded_file = st.file_uploader("Upload transcript JSON", type="json")

if uploaded_file:
    try:
        # Load JSON
        transcript_data = json.load(uploaded_file)
        
        # Format transcript
        formatted_text = format_transcript(transcript_data)
        
        # Create PDF in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = getSampleStyleSheet()
        mono_style = ParagraphStyle(
            'Mono',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=9,
            leading=10,
            alignment=TA_LEFT
        )
        
        story = []
        for line in formatted_text.split('\n'):
            if line.strip():
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(line, mono_style))
            else:
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        pdf_buffer.seek(0)
        
        # Display success and download button
        st.success("✓ Transcript formatted successfully!")
        
        call_id = transcript_data.get("call", {}).get("call_id", "transcript")
        filename = f"call_{call_id}_formatted.pdf"
        
        st.download_button(
            label="📥 Download PDF",
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf"
        )
        
        st.info(f"**Character count:** {len(formatted_text):,} characters\n\nCopy this PDF into Claude Console along with your rubric to grade the call.")
        
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file. Please upload a valid transcript JSON.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
