import sys
import subprocess
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pptx
except ImportError:
    install("python-pptx")
    import pptx

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# Initialize presentation
prs = Presentation()

def apply_dark_theme(slide):
    # Set background to dark gray/blue
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(25, 30, 40)
    
def style_text(shape, font_size=20, is_title=False):
    if not shape.has_text_frame:
        return
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(255, 255, 255) # White text
            if is_title:
                run.font.size = Pt(40)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 191, 255) # Cyan title
            else:
                run.font.size = Pt(font_size)

# Slide 1: Title
slide = prs.slides.add_slide(prs.slide_layouts[0])
apply_dark_theme(slide)
title = slide.shapes.title
subtitle = slide.placeholders[1]
title.text = "AI-Powered Ticket Triage System"
subtitle.text = "Automating Helpdesk with LLM Technology\nProject Presentation"
style_text(title, is_title=True)
style_text(subtitle, 24)

# Slide 2: Team Members & Roles
slide = prs.slides.add_slide(prs.slide_layouts[1])
apply_dark_theme(slide)
slide.shapes.title.text = "Team Members & Core Responsibilities"
content = slide.placeholders[1].text_frame
content.text = "Our team divided the research and implementation as follows:"
p = content.add_paragraph()
p.text = "- Govind: Backend, FastAPI, LLM & Database"
p = content.add_paragraph()
p.text = "- Vishali: Data preprocessing, NLP & Prompt Engineering"
p = content.add_paragraph()
p.text = "- Geetha: Dataset, SQL/Data handling, Dashboard & Testing"
p = content.add_paragraph()
p.text = "- Srinivas: ML model, Feature Engineering & Evaluation"
p = content.add_paragraph()
p.text = "- Saikumar: AI/LLM testing, Prompting & AI research"
style_text(slide.shapes.title, is_title=True)
style_text(slide.placeholders[1], 20)

# Slide 3: Architecture Diagram (Image Slide)
slide = prs.slides.add_slide(prs.slide_layouts[5]) # Title only layout
apply_dark_theme(slide)
slide.shapes.title.text = "System Architecture: AI Workflow"
style_text(slide.shapes.title, is_title=True)

# Add AI Workflow image
img_path_workflow = r"C:\Users\Arjun\.gemini\antigravity-ide\brain\e3b12259-b2d2-437d-a20e-e811050d217d\ai_workflow_1789719177642.jpg"
if os.path.exists(img_path_workflow):
    slide.shapes.add_picture(img_path_workflow, Inches(1), Inches(2), width=Inches(8))
else:
    # Fallback text if image not found
    txBox = slide.shapes.add_textbox(Inches(1), Inches(3), Inches(8), Inches(2))
    txBox.text_frame.text = "[Architecture Diagram Image Placeholder]"
    style_text(txBox, 24)

# Slide 4: Technology Stack & Workflow
slide = prs.slides.add_slide(prs.slide_layouts[1])
apply_dark_theme(slide)
slide.shapes.title.text = "System Workflow Details"
content = slide.placeholders[1].text_frame
p = content.add_paragraph()
p.text = "1. Frontend (React/Vite): User submits ticket via our modern portal."
p = content.add_paragraph()
p.text = "2. Backend (FastAPI): Receives request and coordinates AI."
p = content.add_paragraph()
p.text = "3. LLM (Groq API): Extracts Category, Priority, and Summary in one pass."
p = content.add_paragraph()
p.text = "4. Database (Supabase): Stores validated SQL data."
style_text(slide.shapes.title, is_title=True)
style_text(slide.placeholders[1], 22)

# Slide 5: Dashboard UI (Image Slide)
slide = prs.slides.add_slide(prs.slide_layouts[5])
apply_dark_theme(slide)
slide.shapes.title.text = "React Helpdesk Dashboard"
style_text(slide.shapes.title, is_title=True)

# Add Dashboard image
img_path_dash = r"C:\Users\Arjun\.gemini\antigravity-ide\brain\e3b12259-b2d2-437d-a20e-e811050d217d\react_dashboard_1789719162109.jpg"
if os.path.exists(img_path_dash):
    slide.shapes.add_picture(img_path_dash, Inches(1.5), Inches(1.8), width=Inches(7))
else:
    txBox = slide.shapes.add_textbox(Inches(1), Inches(3), Inches(8), Inches(2))
    txBox.text_frame.text = "[Dashboard UI Image Placeholder]"
    style_text(txBox, 24)

# Slide 6: Strategic Decisions & Optimization
slide = prs.slides.add_slide(prs.slide_layouts[1])
apply_dark_theme(slide)
slide.shapes.title.text = "Optimization & Design Decisions"
content = slide.placeholders[1].text_frame
p = content.add_paragraph()
p.text = "Defending our architectural choices during evaluation:"
p = content.add_paragraph()
p.text = "Q: Why are we not using traditional NLP? (Vishali's focus)"
p.level = 1
p = content.add_paragraph()
p.text = "A: The Groq LLM natively understands natural language context without needing manual text tokenization. Also, since we use a React application for the UI, complex text parsing isn't needed on the backend."
p.level = 2
p = content.add_paragraph()
p.text = "Q: What about traditional ML Models & Feature Engineering? (Srinivas's focus)"
p.level = 1
p = content.add_paragraph()
p.text = "A: We evaluated ML, but LLMs proved superior for dynamic classification. They don't require constant retraining, making Govind's backend lightweight."
p.level = 2
p = content.add_paragraph()
p.text = "Q: How is Data/SQL managed? (Geetha's focus)"
p.level = 1
p = content.add_paragraph()
p.text = "A: The React dashboard connects to FastAPI, which securely handles SQL insertion via Supabase."
p.level = 2
style_text(slide.shapes.title, is_title=True)
style_text(slide.placeholders[1], 16) # Smaller font to fit everything

ppt_path = r"C:\Users\Arjun\Downloads\TASK\Project_Presentation.pptx"
prs.save(ppt_path)
print(f"Presentation saved successfully to {ppt_path}")
