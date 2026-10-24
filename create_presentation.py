import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    C_BG = RGBColor(11, 15, 25)           # Obsidian Dark
    C_CARD_BG = RGBColor(20, 28, 45)      # Card Slate
    C_CARD_BORDER = RGBColor(56, 189, 248) # Cyan Border
    C_WHITE = RGBColor(248, 250, 252)
    C_MUTED = RGBColor(148, 163, 184)
    C_CYAN = RGBColor(0, 242, 254)
    C_PURPLE = RGBColor(168, 85, 247)
    C_EMERALD = RGBColor(16, 185, 129)
    C_AMBER = RGBColor(245, 158, 11)
    C_RED = RGBColor(239, 68, 68)

    def set_slide_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, tag, title, subtitle):
        # Tag
        tb_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.4))
        p_tag = tb_tag.text_frame.paragraphs[0]
        p_tag.text = tag.upper()
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(11)
        p_tag.font.bold = True
        p_tag.font.color.rgb = C_CYAN

        # Title
        tb_t = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.8))
        p_t = tb_t.text_frame.paragraphs[0]
        p_t.text = title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(28)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE

        # Subtitle
        if subtitle:
            tb_s = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.5), Inches(0.5))
            p_s = tb_s.text_frame.paragraphs[0]
            p_s.text = subtitle
            p_s.font.name = "Arial"
            p_s.font.size = Pt(14)
            p_s.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 1: Cinematic Cover
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1)

    # Glowing title card
    tb1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.5), Inches(2.2))
    tf1 = tb1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "AUTONOMOUS AGENTIC HARDWARE ARCHITECT"
    p1.font.name = "Arial"
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = C_CYAN

    p2 = tf1.add_paragraph()
    p2.text = "VISION (Vison Forge)"
    p2.font.name = "Arial"
    p2.font.size = Pt(46)
    p2.font.bold = True
    p2.font.color.rgb = C_WHITE

    p3 = tf1.add_paragraph()
    p3.text = "Turning low-voltage maker concepts into safe, deterministic build-packs with live-catalog component pricing (₹ INR)."
    p3.font.name = "Arial"
    p3.font.size = Pt(16)
    p3.font.color.rgb = C_MUTED

    # 4 Team Cards on Cover
    members = [
        ("Sunil Kumar", "TEAM LEAD · AGENT CORE", "uAgents, ACP Mailbox, ASI:One & Submission", C_PURPLE),
        ("Ayush Sharma", "TOOLS & LOGIC ENGINEER", "Quartz Live API, Safety Rules, Edge Tests", C_CYAN),
        ("Rajnish Raj Shekhar", "PRESENTATION & PITCH LEAD", "3D PPT Deck, 3-Min Pitch, Storyline & Q&A", C_AMBER),
        ("Kamal Kumar Sharma", "DEMO & DOCUMENTATION LEAD", "README, Terminal Demos, Video Script & Media", C_EMERALD)
    ]

    card_w = Inches(2.7)
    card_h = Inches(2.4)
    start_x = Inches(0.8)
    gap = Inches(0.3)

    for i, (name, role, desc, color) in enumerate(members):
        x = start_x + i * (card_w + gap)
        y = Inches(3.8)
        card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_BG
        card.line.color.rgb = color
        card.line.width = Pt(1.5)

        tb = s1.shapes.add_textbox(x + Inches(0.15), y + Inches(0.2), card_w - Inches(0.3), card_h - Inches(0.4))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = role
        p.font.name = "Arial"
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = color

        p_name = tf.add_paragraph()
        p_name.text = name
        p_name.font.name = "Arial"
        p_name.font.size = Pt(16)
        p_name.font.bold = True
        p_name.font.color.rgb = C_WHITE

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = "Arial"
        p_desc.font.size = Pt(11)
        p_desc.font.color.rgb = C_MUTED

    # Status Pill at bottom
    tb_pill = s1.shapes.add_textbox(Inches(0.8), Inches(6.6), Inches(11.5), Inches(0.4))
    p_pill = tb_pill.text_frame.paragraphs[0]
    p_pill.text = "⚡ Built on Fetch.ai uAgents Protocol  |  ASI:One Ready  |  Zero Hallucination Hardware Architecture"
    p_pill.font.name = "Arial"
    p_pill.font.size = Pt(11)
    p_pill.font.color.rgb = C_CYAN

    # ==========================================
    # SLIDE 2: Problem Statement
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2)
    add_header(s2, "01 · The Problem", "The Hardware Prototyping Trap", "Why 65%+ of student and hackathon robotics builds fail before their first test:")

    problems = [
        ("High-Voltage Catastrophes", "Beginners inadvertently connect 220V AC mains or high-discharge LiPos to 3.3V/5V logic, frying microcontrollers, triggering smoke, or risking electrical fire.", C_RED),
        ("Phantom & Hallucinated Pricing", "Standard LLMs (ChatGPT, Claude) fabricate prices from obsolete foreign blogs. Teams budget ₹1,000 only to find parts cost ₹3,500 locally or are completely out of stock.", C_AMBER),
        ("Pin & Logic Mismatches", "Conflicting I2C addresses, unlevel-shifted 5V sensors connected to 3.3V ESP32 GPIOs, and missing pull-ups cause days of frustrating debugging.", C_RED)
    ]

    p_w = Inches(3.6)
    p_h = Inches(4.3)
    p_start_x = Inches(0.8)
    p_gap = Inches(0.4)

    for i, (p_title, p_desc, p_col) in enumerate(problems):
        px = p_start_x + i * (p_w + p_gap)
        py = Inches(2.3)
        c = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px, py, p_w, p_h)
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD_BG
        c.line.color.rgb = p_col
        c.line.width = Pt(1.5)

        tb = s2.shapes.add_textbox(px + Inches(0.25), py + Inches(0.3), p_w - Inches(0.5), p_h - Inches(0.6))
        tf = tb.text_frame
        
        p = tf.paragraphs[0]
        p.text = f"CRITICAL BOTTLENECK 0{i+1}"
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = p_col

        p_t = tf.add_paragraph()
        p_t.text = p_title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(18)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE

        p_d = tf.add_paragraph()
        p_d.text = "\n" + p_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(13)
        p_d.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 3: The Solution
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3)
    add_header(s3, "02 · The Solution", "Vison Forge: Deterministic Agentic Hardware Planning", "An autonomous AI agent that generates build-ready hardware packs backed by verified real-world data:")

    solutions = [
        ("Deterministic Safety Gate", "Hard-coded electrical safety rules automatically catch mains AC, unisolated relays, and dangerous battery chemistries—redirecting builders to low-voltage alternatives.", C_EMERALD),
        ("Live Retailer Tool (₹ INR)", "Direct live catalog integration with Quartz Components (Indian electronics distributor). Retrieves verified item prices, stock flags, timestamps, and calculates transparent project totals.", C_CYAN),
        ("Complete Build-Pack Synthesis", "Autonomously outputs PROJECT_PLAN.md, BOM.csv with direct purchase links, WIRING.md with GPIO pin assignments, and TEST_PLAN.md mapped to team member count.", C_PURPLE)
    ]

    for i, (s_title, s_desc, s_col) in enumerate(solutions):
        sx = p_start_x + i * (p_w + p_gap)
        sy = Inches(2.3)
        c = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, sy, p_w, p_h)
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD_BG
        c.line.color.rgb = s_col
        c.line.width = Pt(1.5)

        tb = s3.shapes.add_textbox(sx + Inches(0.25), sy + Inches(0.3), p_w - Inches(0.5), p_h - Inches(0.6))
        tf = tb.text_frame
        
        p = tf.paragraphs[0]
        p.text = f"AGENT PILLAR 0{i+1}"
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = s_col

        p_t = tf.add_paragraph()
        p_t.text = s_title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(18)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE

        p_d = tf.add_paragraph()
        p_d.text = "\n" + s_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(13)
        p_d.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 4: Architecture
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4)
    add_header(s4, "03 · Architecture", "Fetch.ai uAgents Protocol & Tool Execution Flow", "End-to-end data pipeline connecting conversational intent to live hardware procurement:")

    steps = [
        ("1. User Intent", "ASI:One Chat / CLI\nNatural language specs:\nBoard, sensors, budget, days", C_WHITE),
        ("2. ACP Ingress", "agent.py uAgent\nChat Protocol Spec\nAsyncio ThreadPoolExecutor", C_CYAN),
        ("3. Safety Gate", "vison/forge.py\nAC voltage checks\nBattery discharge limits", C_EMERALD),
        ("4. Live Tool", "vison/retailer.py\nQuartz Components API\nReal INR prices & stock", C_AMBER),
        ("5. Build Pack", "Artifact Generator\nBOM.csv, WIRING.md,\nPLAN.md & TEST_PLAN.md", C_PURPLE)
    ]

    step_w = Inches(2.1)
    step_h = Inches(3.2)
    step_start_x = Inches(0.8)
    step_gap = Inches(0.3)

    for i, (st_name, st_body, st_col) in enumerate(steps):
        x = step_start_x + i * (step_w + step_gap)
        y = Inches(2.4)
        c = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, step_w, step_h)
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD_BG
        c.line.color.rgb = st_col
        c.line.width = Pt(1.5)

        tb = s4.shapes.add_textbox(x + Inches(0.15), y + Inches(0.25), step_w - Inches(0.3), step_h - Inches(0.5))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = st_name
        p.font.name = "Arial"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = st_col

        p_b = tf.add_paragraph()
        p_b.text = "\n" + st_body
        p_b.font.name = "Arial"
        p_b.font.size = Pt(11)
        p_b.font.color.rgb = C_MUTED

    # Bottom notes card
    note_box = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.9))
    note_box.fill.solid()
    note_box.fill.fore_color.rgb = C_CARD_BG
    note_box.line.color.rgb = C_CARD_BORDER
    tb_nb = s4.shapes.add_textbox(Inches(1.0), Inches(6.05), Inches(11.3), Inches(0.8))
    p_nb = tb_nb.text_frame.paragraphs[0]
    p_nb.text = "🔒 Ethical Agent Policy: Strictly informational. Never touches payment cards or places orders. Strictly adheres to robots.txt and published agents.md guidelines."
    p_nb.font.name = "Arial"
    p_nb.font.size = Pt(11)
    p_nb.font.color.rgb = C_CYAN

    # ==========================================
    # SLIDE 5: Demo Run & Case Study
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5)
    add_header(s5, "04 · Execution Case Study", "Live Run: Automated ESP32 Plant Irrigation System", "Validated execution on prompt: 'ESP32 plant watering system for 2 plants under ₹2500 in 7 days'")

    # Left: Terminal Output
    t_box = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.2), Inches(6.2), Inches(4.6))
    t_box.fill.solid()
    t_box.fill.fore_color.rgb = RGBColor(5, 7, 12)
    t_box.line.color.rgb = C_CARD_BORDER

    tb_t = s5.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.8), Inches(4.3))
    tf_t = tb_t.text_frame
    p = tf_t.paragraphs[0]
    p.text = "// VERIFIED EXECUTION OUTPUT\n"
    p.font.name = "Consolas"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    logs = (
        "> Request parsed: Microcontroller=ESP32, Plants=2, Budget=₹2,500, Team=2\n"
        "> Safety Gate: PASS (Safe low voltage 5V/3.3V DC)\n"
        "> Retailer Adapter: Querying Quartz Components catalog...\n"
        "> Match found: ESP32 NodeMCU, 5V Relay, Capacitive Probes, 5V Mini Pump\n"
        "> Verified Pricing Tiers Calculated:\n"
        "   • Basic Tier:       ₹845  (Direct GPIO / 1 Pump)\n"
        "   • Recommended Tier: ₹1,420 (Dual Relays + ESP32 CP2102)\n"
        "   • Premium Tier:     ₹2,190 (Solar shield + Industrial probe)\n"
        "> Generated: BOM.csv, WIRING.md, PROJECT_PLAN.md, TEST_PLAN.md"
    )
    p_l = tf_t.add_paragraph()
    p_l.text = logs
    p_l.font.name = "Consolas"
    p_l.font.size = Pt(10)
    p_l.font.color.rgb = C_WHITE

    # Right: Artifacts Breakdown
    r_box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.3), Inches(2.2), Inches(5.2), Inches(4.6))
    r_box.fill.solid()
    r_box.fill.fore_color.rgb = C_CARD_BG
    r_box.line.color.rgb = C_PURPLE

    tb_r = s5.shapes.add_textbox(Inches(7.5), Inches(2.3), Inches(4.8), Inches(4.3))
    tf_r = tb_r.text_frame
    p_rh = tf_r.paragraphs[0]
    p_rh.text = "GENERATED ARTIFACTS PACK"
    p_rh.font.name = "Arial"
    p_rh.font.size = Pt(14)
    p_rh.font.bold = True
    p_rh.font.color.rgb = C_PURPLE

    arts = (
        "\n• BOM.csv:\n"
        "  Item name, Quartz URL, stock status, and ₹ observed cost.\n\n"
        "• WIRING.md:\n"
        "  Exact pin table: D32 (Sensor 1), D33 (Sensor 2), D22 (Relay 1), D21 (Relay 2).\n\n"
        "• PROJECT_PLAN.md:\n"
        "  7-day sprint plan distributed evenly between Team Member 1 & 2.\n\n"
        "• TEST_PLAN.md:\n"
        "  Dry bench tests, sensor calibration, pump current checks, WiFi failover."
    )
    p_rb = tf_r.add_paragraph()
    p_rb.text = arts
    p_rb.font.name = "Arial"
    p_rb.font.size = Pt(11)
    p_rb.font.color.rgb = C_WHITE

    # ==========================================
    # SLIDE 6: Team Roles & Ownership
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6)
    add_header(s6, "05 · Team Roles", "Engineering Division of Labor", "Four specialized roles covering protocol, logic, presentation, and quality assurance:")

    for i, (name, role, desc, color) in enumerate(members):
        x = start_x + i * (card_w + gap)
        y = Inches(2.3)
        card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, Inches(4.5))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_BG
        card.line.color.rgb = color
        card.line.width = Pt(1.5)

        tb = s6.shapes.add_textbox(x + Inches(0.15), y + Inches(0.3), card_w - Inches(0.3), Inches(4.0))
        tf = tb.text_frame
        
        p = tf.paragraphs[0]
        p.text = role
        p.font.name = "Arial"
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = color

        p_n = tf.add_paragraph()
        p_n.text = name
        p_n.font.name = "Arial"
        p_n.font.size = Pt(17)
        p_n.font.bold = True
        p_n.font.color.rgb = C_WHITE

        # Detailed breakdown per member
        details = {
            "Sunil Kumar": "\n• GitHub repo & CI setup\n• agent.py ACP implementation\n• Agentverse mailbox connector\n• ASI:One live chat test\n• Final platform submission",
            "Ayush Sharma": "\n• Quartz live API scraping\n• Safety gate rules (forge.py)\n• Price tier math & INR logic\n• test_retailer.py unit suite\n• Multi-agent ACP handoffs",
            "Rajnish Raj Shekhar": "\n• PPT Deck & 3D visual styling\n• 3-Minute pitch speech script\n• Problem & solution alignment\n• Market differentiator analysis\n• Live judge pitch & delivery",
            "Kamal Kumar Sharma": "\n• Comprehensive README.md\n• Architecture flowcharts & visual assets\n• Demo video recording & audio script\n• Terminal screenshots\n• Judge Q&A playbook prep"
        }

        p_d = tf.add_paragraph()
        p_d.text = details[name]
        p_d.font.name = "Arial"
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 7: Future Scope & Roadmap
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7)
    add_header(s7, "06 · The Future", "Why VISION Wins & Strategic Roadmap", "Evolving from a planning agent into an end-to-end autonomous hardware co-pilot:")

    roadmap = [
        ("Phase 1: Validated MVP (Live Today)", "• Fetch.ai uAgent with ACP protocol\n• Real INR pricing via Quartz live API\n• Zero hallucination safety gate\n• Complete downloadable build-packs", C_CYAN),
        ("Phase 2: Vision Breadboard Inspector", "• Take a smartphone photo of the circuit\n• Multimodal AI compares physical jumper wires against WIRING.md before powering on\n• Prevents burnt components in real time", C_PURPLE),
        ("Phase 3: Multi-Agent Procurement", "• Sourcing Agent + Schematic Verification Agent\n• Autonomous cross-store price comparison across Indian distributors\n• Direct KiCad schematic & PCB Gerber generation", C_EMERALD)
    ]

    for i, (r_title, r_desc, r_col) in enumerate(roadmap):
        rx = p_start_x + i * (p_w + p_gap)
        ry = Inches(2.3)
        c = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, rx, ry, p_w, p_h)
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD_BG
        c.line.color.rgb = r_col
        c.line.width = Pt(1.5)

        tb = s7.shapes.add_textbox(rx + Inches(0.25), ry + Inches(0.3), p_w - Inches(0.5), p_h - Inches(0.6))
        tf = tb.text_frame
        
        p = tf.paragraphs[0]
        p.text = f"MILESTONE 0{i+1}"
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = r_col

        p_t = tf.add_paragraph()
        p_t.text = r_title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE

        p_d = tf.add_paragraph()
        p_d.text = "\n" + r_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = C_MUTED

    prs.save("VISION_Forge_Presentation.pptx")
    print("SUCCESS: VISION_Forge_Presentation.pptx generated successfully!")

if __name__ == "__main__":
    create_deck()
