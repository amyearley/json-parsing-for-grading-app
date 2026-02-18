import streamlit as st
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT
from transcript_formatter import format_transcript

st.set_page_config(page_title="Call Grading Tools", layout="wide")

st.title("📞 Call Grading Tools")

# Sidebar navigation
page = st.sidebar.radio("Select Tool", ["Transcript Formatter", "Rubric Editor"])

if page == "Transcript Formatter":
    st.header("Transcript Formatter")
    st.write("Upload your call transcript JSON and get a formatted PDF ready for Claude Console.")
    
    uploaded_file = st.file_uploader("Upload transcript JSON", type="json", key="transcript_uploader")
    
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
                    if len(line) > 100:
                        for i in range(0, len(line), 100):
                            chunk = line[i:i+100]
                            story.append(Paragraph(chunk, mono_style))
                    else:
                        story.append(Paragraph(line, mono_style))
                else:
                    story.append(Spacer(1, 0.05*inch))
            
            doc.build(story)
            pdf_buffer.seek(0)
            
            # Display success and download button
            st.success("✓ Transcript formatted successfully!")
            
            call_id = transcript_data.get("call", {}).get("call_id", transcript_data.get("JobName", "transcript"))
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

elif page == "Rubric Editor":
    st.header("Rubric Editor")
    st.write("Load the default rubric, customize it, and download as PDF for Claude Console.")
    
    # Load default rubric
    try:
        with open('grading_rubric.json', 'r') as f:
            default_rubric = json.load(f)
    except FileNotFoundError:
        st.error("❌ Default rubric file not found. Please ensure grading_rubric.json is in the repo.")
        st.stop()
    
    # Initialize session state for rubric
    if 'rubric' not in st.session_state:
        st.session_state.rubric = default_rubric
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Metadata", "Categories", "Red Flags & Bonuses"])
    
    with tab1:
        st.subheader("Rubric Metadata")
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.rubric["_meta"]["firm"] = st.text_input(
                "Firm Name",
                value=st.session_state.rubric["_meta"]["firm"]
            )
            st.session_state.rubric["_meta"]["rubric_name"] = st.text_input(
                "Rubric Name",
                value=st.session_state.rubric["_meta"]["rubric_name"]
            )
        
        with col2:
            st.session_state.rubric["_meta"]["version"] = st.text_input(
                "Version",
                value=st.session_state.rubric["_meta"]["version"]
            )
        
        st.text_area(
            "Scoring Note",
            value=st.session_state.rubric["_meta"]["scoring_note"],
            height=150,
            key="scoring_note",
            on_change=lambda: st.session_state.rubric["_meta"].update({"scoring_note": st.session_state.scoring_note})
        )
    
    with tab2:
        st.subheader("Categories")
        
        # Calculate subscore totals
        logistics_total = sum(cat["max_points"] for cat in st.session_state.rubric["categories"] if cat["active"] and cat["subscore"] == "logistics")
        human_element_total = sum(cat["max_points"] for cat in st.session_state.rubric["categories"] if cat["active"] and cat["subscore"] == "human_element")
        
        # Display subscore summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Logistics Total", f"{logistics_total} pts")
        with col2:
            st.metric("Human Element Total", f"{human_element_total} pts")
        
        st.divider()
        
        for idx, category in enumerate(st.session_state.rubric["categories"]):
            # Badge for subscore type
            badge_color = "🔵" if category["subscore"] == "logistics" else "🟢"
            badge_label = "Logistics" if category["subscore"] == "logistics" else "Human Element"
            
            # Status indicator
            status = "✓ Active" if category["active"] else "○ Inactive"
            
            with st.expander(f"{badge_color} {category['label']} — {status}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    category["active"] = st.checkbox(
                        "Active",
                        value=category["active"],
                        key=f"cat_active_{idx}"
                    )
                    category["max_points"] = st.number_input(
                        "Max Points",
                        value=category["max_points"],
                        min_value=1,
                        key=f"cat_max_{idx}"
                    )
                
                with col2:
                    category["weight_pct"] = st.number_input(
                        "Weight %",
                        value=category["weight_pct"],
                        min_value=0,
                        key=f"cat_weight_{idx}"
                    )
                
                with col3:
                    category["subscore"] = st.selectbox(
                        "Subscore",
                        ["logistics", "human_element"],
                        index=0 if category["subscore"] == "logistics" else 1,
                        key=f"cat_subscore_{idx}"
                    )
                
                category["purpose"] = st.text_input(
                    "Purpose",
                    value=category["purpose"],
                    key=f"cat_purpose_{idx}"
                )
                
                category["importance"] = st.text_area(
                    "Importance",
                    value=category["importance"],
                    height=80,
                    key=f"cat_importance_{idx}"
                )
    
    with tab3:
        st.subheader("Red Flags")
        
        for idx, flag in enumerate(st.session_state.rubric["red_flags"]["flags"]):
            with st.expander(f"{flag['label']} ({flag['id']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    flag["active"] = st.checkbox(
                        "Active",
                        value=flag["active"],
                        key=f"flag_active_{idx}"
                    )
                    flag["penalty"] = st.number_input(
                        "Penalty",
                        value=flag["penalty"],
                        key=f"flag_penalty_{idx}"
                    )
                
                with col2:
                    flag["subscore"] = st.selectbox(
                        "Subscore",
                        ["logistics", "human_element"],
                        index=0 if flag["subscore"] == "logistics" else 1,
                        key=f"flag_subscore_{idx}"
                    )
                
                flag["description"] = st.text_area(
                    "Description",
                    value=flag["description"],
                    height=80,
                    key=f"flag_desc_{idx}"
                )
        
        st.subheader("Bonuses")
        
        for idx, bonus in enumerate(st.session_state.rubric["bonuses"]["items"]):
            with st.expander(f"{bonus['label']} ({bonus['id']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    bonus["active"] = st.checkbox(
                        "Active",
                        value=bonus["active"],
                        key=f"bonus_active_{idx}"
                    )
                    bonus["points"] = st.number_input(
                        "Points",
                        value=bonus["points"],
                        key=f"bonus_points_{idx}"
                    )
                
                with col2:
                    bonus["subscore"] = st.selectbox(
                        "Subscore",
                        ["logistics", "human_element"],
                        index=0 if bonus["subscore"] == "logistics" else 1,
                        key=f"bonus_subscore_{idx}"
                    )
                
                bonus["description"] = st.text_area(
                    "Description",
                    value=bonus["description"],
                    height=80,
                    key=f"bonus_desc_{idx}"
                )
    
    # Download buttons
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        # Download as JSON
        json_str = json.dumps(st.session_state.rubric, indent=2)
        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name="custom_rubric.json",
            mime="application/json"
        )
    
    with col2:
        # Download as PDF
        try:
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
            
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            subheading_style = styles['Heading3']
            normal_style = styles['Normal']
            
            story = []
            
            # Title
            story.append(Paragraph(st.session_state.rubric["_meta"]["rubric_name"], title_style))
            story.append(Paragraph(f"Version {st.session_state.rubric['_meta']['version']}", normal_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Metadata
            story.append(Paragraph("Metadata", heading_style))
            story.append(Paragraph(f"<b>Firm:</b> {st.session_state.rubric['_meta']['firm']}", normal_style))
            story.append(Paragraph(f"<b>Scoring Note:</b> {st.session_state.rubric['_meta']['scoring_note'][:200]}...", normal_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Categories
            story.append(PageBreak())
            story.append(Paragraph("Categories", heading_style))
            
            for category in st.session_state.rubric["categories"]:
                if category["active"]:
                    story.append(Paragraph(f"<b>{category['label']}</b> ({category['max_points']} pts)", subheading_style))
                    story.append(Paragraph(f"<i>Purpose:</i> {category['purpose']}", normal_style))
                    story.append(Paragraph(f"<i>Importance:</i> {category['importance']}", normal_style))
                    
                    # Score bands
                    for band in category.get("score_bands", []):
                        range_str = f"{band['range'][0]}-{band['range'][1]}"
                        story.append(Paragraph(f"<b>{band['rating']}</b> ({range_str}): {band['description']}", normal_style))
                    
                    story.append(Spacer(1, 0.15*inch))
            
            # Red Flags
            story.append(PageBreak())
            story.append(Paragraph("Red Flags", heading_style))
            
            for flag in st.session_state.rubric["red_flags"]["flags"]:
                if flag["active"]:
                    story.append(Paragraph(f"<b>{flag['label']}</b> (Penalty: {flag['penalty']})", subheading_style))
                    story.append(Paragraph(flag['description'], normal_style))
                    story.append(Spacer(1, 0.1*inch))
            
            # Bonuses
            story.append(PageBreak())
            story.append(Paragraph("Bonuses", heading_style))
            
            for bonus in st.session_state.rubric["bonuses"]["items"]:
                if bonus["active"]:
                    story.append(Paragraph(f"<b>{bonus['label']}</b> (+{bonus['points']} pts)", subheading_style))
                    story.append(Paragraph(bonus['description'], normal_style))
                    story.append(Spacer(1, 0.1*inch))
            
            doc.build(story)
            pdf_buffer.seek(0)
            
            st.download_button(
                label="📥 Download as PDF",
                data=pdf_buffer,
                file_name="custom_rubric.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
