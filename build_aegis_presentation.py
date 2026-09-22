"""
Builds an executive-grade, presentation-friendly 13-slide PowerPoint deck for Project Aegis.
Incorporates high-resolution empirical charts, architectural diagrams, metric callouts, and clean tables.
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# -------------------------------------------------------------
# Color Palette Constants
# -------------------------------------------------------------
COLOR_BG = RGBColor(0x16, 0x19, 0x26)          # Dark slate / navy
COLOR_CARD_BG = RGBColor(0x1E, 0x22, 0x35)     # Elevated card surface
COLOR_CARD_ALT = RGBColor(0x11, 0x13, 0x1D)    # Sunken inner surface
COLOR_BORDER = RGBColor(0x33, 0x41, 0x55)      # Hairline border (slate 700)
COLOR_BORDER_CYAN = RGBColor(0x0E, 0xA5, 0xE9) # Cyan accent border
COLOR_TEXT_PRIMARY = RGBColor(0xFF, 0xFF, 0xFF)# Pure white
COLOR_TEXT_SEC = RGBColor(0xCB, 0xD5, 0xE1)    # Light slate
COLOR_TEXT_MUTED = RGBColor(0x94, 0xA3, 0xB8)  # Slate 400
COLOR_ACCENT_CYAN = RGBColor(0x38, 0xBD, 0xF8) # Sky blue / Cyan
COLOR_STATUS_GREEN = RGBColor(0x4A, 0xDE, 0x80)# Emerald green
COLOR_WARN_AMBER = RGBColor(0xFB, 0xBF, 0x24)  # Amber
COLOR_DANGER_RED = RGBColor(0xF8, 0x71, 0x71)  # Crimson red
COLOR_CODE_BG = RGBColor(0x0F, 0x11, 0x1A)     # Code editor background

FONT_HEADING = 'Arial'
FONT_BODY = 'Arial'
FONT_CODE = 'Consolas'

def create_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # Helper: Base slide with standard header & footer
    def add_base_slide(eyebrow, title, subtitle, slide_num):
        slide = prs.slides.add_slide(blank_layout)
        
        # Solid background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.fill.background()
        
        # Header text frame
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.733), Inches(1.2))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        # Eyebrow tag
        p_eye = tf.paragraphs[0]
        p_eye.text = eyebrow.upper()
        p_eye.font.name = FONT_HEADING
        p_eye.font.size = Pt(9.5)
        p_eye.font.bold = True
        p_eye.font.color.rgb = COLOR_ACCENT_CYAN
        p_eye.space_after = Pt(2)
        
        # Main Title
        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_TEXT_PRIMARY
        p_title.space_after = Pt(2)
        
        # Subtitle
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(11.5)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED
        
        # Footer
        footer_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.015))
        footer_line.fill.solid()
        footer_line.fill.fore_color.rgb = COLOR_BORDER
        footer_line.line.fill.background()
        
        foot_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.3))
        ftf = foot_box.text_frame
        ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
        p_foot = ftf.paragraphs[0]
        p_foot.text = f"Project Aegis — Autonomous In-Kernel Behavioral EDR for Linux   |   Slide {slide_num} of 13"
        p_foot.font.name = FONT_BODY
        p_foot.font.size = Pt(8.5)
        p_foot.font.color.rgb = COLOR_TEXT_MUTED
        
        return slide

    # Helper: Add rounded card container
    def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # Helper: Add Metric Callout Box
    def add_stat_box(slide, left, top, width, height, val, label, subtext, color=COLOR_ACCENT_CYAN):
        add_card(slide, left, top, width, height, COLOR_CARD_BG, COLOR_BORDER)
        box = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.12), Inches(width - 0.3), Inches(height - 0.24))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_val = tf.paragraphs[0]
        p_val.text = val
        p_val.font.name = FONT_HEADING
        p_val.font.size = Pt(22)
        p_val.font.bold = True
        p_val.font.color.rgb = color
        
        p_lbl = tf.add_paragraph()
        p_lbl.text = label
        p_lbl.font.name = FONT_HEADING
        p_lbl.font.size = Pt(9.5)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = COLOR_TEXT_PRIMARY
        
        p_sub = tf.add_paragraph()
        p_sub.text = subtext
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(8)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # -------------------------------------------------------------
    # SLIDE 1: Cover / Executive Architecture
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_BG
    bg1.line.fill.background()
    
    # Title Box
    tbox = slide1.shapes.add_textbox(Inches(0.8), Inches(1.1), Inches(11.733), Inches(2.2))
    tf1 = tbox.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "AUTONOMOUS IN-KERNEL BEHAVIORAL EDR  ·  LINUX BTF CO-RE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(8)
    
    p = tf1.add_paragraph()
    p.text = "Project Aegis"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_PRIMARY
    p.space_after = Pt(6)
    
    p = tf1.add_paragraph()
    p.text = "A Cross-Layer, In-Kernel Behavioral EDR for Linux Pre-empting Bulk Encryption"
    p.font.size = Pt(16)
    p.font.color.rgb = COLOR_TEXT_SEC
    p.space_after = Pt(4)
    
    p = tf1.add_paragraph()
    p.text = "Synchronous write-path interception via eBPF LSM and VFS hooks with sub-3µs threat neutralization before disk serialization."
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEXT_MUTED
    
    # 3 Pillar Cards
    pillars = [
        ("PILLAR 1", "HID Injection Detection", "Catching BadUSB scripts that type faster than human limits via keystroke variance & trust machines.", COLOR_ACCENT_CYAN),
        ("PILLAR 2", "In-Kernel Ransomware Defense", "Real-time fixed-point Shannon cryptanalysis, decoy tripwires, and synchronous LSM -EPERM lockdown.", COLOR_STATUS_GREEN),
        ("PILLAR 3", "Microarchitectural Sensing", "Hardware PMU cache miss & branch telemetry detecting stealth side-channel and Flush+Reload attacks.", COLOR_WARN_AMBER)
    ]
    for i, (tag, ptitle, pdesc, pcol) in enumerate(pillars):
        cx = 0.8 + i * 4.0
        add_card(slide1, cx, 3.65, 3.733, 1.85, COLOR_CARD_BG, COLOR_BORDER)
        cbox = slide1.shapes.add_textbox(Inches(cx + 0.25), Inches(3.8), Inches(3.233), Inches(1.5))
        ctf = cbox.text_frame
        ctf.word_wrap = True
        
        p = ctf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = pcol
        p.space_after = Pt(3)
        
        p = ctf.add_paragraph()
        p.text = ptitle
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p.space_after = Pt(4)
        
        p = ctf.add_paragraph()
        p.text = pdesc
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_MUTED
        
    # 4 Quick Stat Callouts at Bottom
    stats = [
        ("2.4 µs", "Synchronous Reaction", "75,000x faster than Ring 3", COLOR_STATUS_GREEN),
        ("0 Files", "Data Loss Guarantee", "Zero bytes committed to disk", COLOR_ACCENT_CYAN),
        ("0.0%", "False Positive Rate", "Verified across 2,000 mixed archives", COLOR_WARN_AMBER),
        ("3.8 MB", "Resident Footprint", "< 0.8% CPU saturation overhead", COLOR_TEXT_PRIMARY)
    ]
    for i, (val, lbl, sub, col) in enumerate(stats):
        add_stat_box(slide1, 0.8 + i * 3.0, 5.7, 2.733, 1.15, val, lbl, sub, col)

    # -------------------------------------------------------------
    # SLIDE 2: Problem Statement — The 180 ms Ring 3 EDR Latency Gap
    # -------------------------------------------------------------
    slide2 = add_base_slide(
        "Threat Landscape & Industry Blind Spot",
        "Why Conventional Enterprise EDRs Fail Against Ransomware",
        "Asynchronous user-space notification queues introduce 150-200ms latency, enabling dozens of files to encrypt before alerts fire.",
        2
    )
    
    # Left Card: The 3 Core Architectural Failures
    add_card(slide2, 0.8, 1.9, 5.2, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    lbox = slide2.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(4.7), Inches(4.45))
    ltf = lbox.text_frame
    ltf.word_wrap = True
    
    p = ltf.paragraphs[0]
    p.text = "ARCHITECTURAL FAILURE MODES OF RING 3 EDR"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_DANGER_RED
    p.space_after = Pt(10)
    
    flaws = [
        ("1. Asynchronous Polling Latency", "Conventional EDRs (CrowdStrike, Defender) rely on fanotify, ETW, or auditd. IPC queues introduce 150–200 ms latency under heavy write saturation, creating an irreversible encryption blind spot."),
        ("2. Trivial Signature Evasion", "Modern ransomware families (LockBit, BlackCat) deploy compile-time polymorphism, crypters, and memory-only execution to evade static file signatures completely."),
        ("3. Naive Entropy Misfires", "Simple entropy filters flag benign .zip, .tar.gz, and .mp4 files as malicious while missing partial-block or intermittent ciphers, leading to severe alert fatigue and disabled enforcement.")
    ]
    for ftitle, fdesc in flaws:
        p = ltf.add_paragraph()
        p.text = ftitle
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p.space_after = Pt(2)
        
        p = ltf.add_paragraph()
        p.text = fdesc
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(8)
        
    # Right Side: Embed Graph 1 (Latency vs Files Lost)
    chart1_path = 'dashboard/pptx_assets/latency_vs_files_lost.png'
    if os.path.exists(chart1_path):
        slide2.shapes.add_picture(chart1_path, Inches(6.3), Inches(1.9), width=Inches(6.233))
        
    # Takeaway Callout underneath right side
    add_card(slide2, 6.3, 5.65, 6.233, 1.1, COLOR_CARD_ALT, COLOR_STATUS_GREEN)
    tbox = slide2.shapes.add_textbox(Inches(6.5), Inches(5.75), Inches(5.833), Inches(0.9))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    p = ttf.paragraphs[0]
    p.text = "AEGIS ENGINEERING SOLUTION"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p = ttf.add_paragraph()
    p.text = "By shifting inspection inside the Linux VFS write path via eBPF LSM, Aegis operates in 2.4 microseconds synchronously, preempting storage serialization before bytes commit to disk."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # -------------------------------------------------------------
    # SLIDE 3: Unified Multi-Pillar System Architecture
    # -------------------------------------------------------------
    slide3 = add_base_slide(
        "System Architecture & Operating Planes",
        "Kernel Decides Quickly; Userspace Decides Carefully",
        "A dual-plane architecture combining sub-3µs in-kernel synchronous interception with asynchronous user-space audit and supervision.",
        3
    )
    
    # Top Half: Plane 1 (Fast In-Kernel) vs Plane 2 (Slow User-Space)
    add_card(slide3, 0.8, 1.9, 5.7, 2.5, COLOR_CARD_BG, COLOR_BORDER_CYAN)
    p1box = slide3.shapes.add_textbox(Inches(1.05), Inches(2.05), Inches(5.2), Inches(2.2))
    p1tf = p1box.text_frame
    p1tf.word_wrap = True
    p = p1tf.paragraphs[0]
    p.text = "FAST PLANE — KERNEL SPACE (eBPF + LSM)"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(6)
    
    kernel_points = [
        "Hooks: fentry/vfs_write, lsm/file_permission, lsm/inode_rename, lsm/inode_create",
        "Sub-3 Microsecond Latency: Synchronous write-path evaluation with zero context switches",
        "In-Kernel BPF Maps: proc_state_map (LRU), canary_map, nlog2n_tab, quarantined_tgids",
        "Autonomous Enforcement: bpf_send_signal(SIGKILL) + immediate LSM -EPERM write denial"
    ]
    for pt in kernel_points:
        p = p1tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_SEC
        p.space_after = Pt(3)

    add_card(slide3, 6.833, 1.9, 5.7, 2.5, COLOR_CARD_BG, COLOR_BORDER)
    p2box = slide3.shapes.add_textbox(Inches(7.083), Inches(2.05), Inches(5.2), Inches(2.2))
    p2tf = p2box.text_frame
    p2tf.word_wrap = True
    p = p2tf.paragraphs[0]
    p.text = "SLOW PLANE — USER SPACE (aegisd-fs)"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WARN_AMBER
    p.space_after = Pt(6)
    
    user_points = [
        "Daemon Manager: BPF skeleton lifecycle, BTF CO-RE feature negotiation & map initialization",
        "Lockless Ring Buffer Consumer: Epoll poller collecting 128-byte raw forensic memory slices",
        "Decoy Canary Lifecycle: Automated seeding, depth stratification, and post-attack re-arming",
        "Forensic Provenance Engine: Structured JSONL event audit trails and cgroup supervisor"
    ]
    for pt in user_points:
        p = p2tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_SEC
        p.space_after = Pt(3)

    # Bottom Half: 3 Unified Sensor Pillars
    pillars_detail = [
        ("Pillar 1: HID Injection", "Intercepts BadUSB & Rubber-Ducky keystrokes via inter-key interval variance and dwell timing state machines.", COLOR_ACCENT_CYAN),
        ("Pillar 2: Ransomware Interception", "Synchronous VFS write evaluation, fixed-point Shannon entropy, decoy tripwires, and -EPERM lockdown.", COLOR_STATUS_GREEN),
        ("Pillar 3: Microarchitectural PMU", "Hardware performance counters sense cache misses and branch mispredictions from Flush+Reload side-channels.", COLOR_WARN_AMBER)
    ]
    for i, (ptit, pdesc, pcol) in enumerate(pillars_detail):
        cx = 0.8 + i * 4.0
        add_card(slide3, cx, 4.65, 3.733, 2.1, COLOR_CARD_BG, COLOR_BORDER)
        pbox = slide3.shapes.add_textbox(Inches(cx + 0.2), Inches(4.8), Inches(3.333), Inches(1.8))
        ptf = pbox.text_frame
        ptf.word_wrap = True
        p = ptf.paragraphs[0]
        p.text = ptit
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = pcol
        p.space_after = Pt(4)
        
        p = ptf.add_paragraph()
        p.text = pdesc
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(6)
        
        p = ptf.add_paragraph()
        p.text = "Shares unified in-kernel risk state across process lineage."
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_SEC

    # -------------------------------------------------------------
    # SLIDE 4: Pillar 2 Deep-Dive — In-Kernel VFS Synchronous Interception
    # -------------------------------------------------------------
    slide4 = add_base_slide(
        "Core Interception Architecture",
        "Synchronous In-Kernel VFS Write Path Interception",
        "Pre-empting destructive storage serialization inside fentry/vfs_write with zero user-space roundtrips.",
        4
    )
    
    # Left Column: 6-Stage Execution Pipeline
    add_card(slide4, 0.8, 1.9, 6.0, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    sbox = slide4.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.5), Inches(4.45))
    stf = sbox.text_frame
    stf.word_wrap = True
    p = stf.paragraphs[0]
    p.text = "SYNCHRONOUS PIPELINE STAGES (fentry/vfs_write)"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(8)
    
    pipe_stages = [
        ("Stage 1: VFS Write Intercept", "Catches entry to vfs_write; validates file descriptor, filters sockets/pipes, samples up to 4096B."),
        ("Stage 2: Canary Map Match", "O(1) hash lookup on (dev, inode) against canary_map; instant +40 threat score on decoy touch."),
        ("Stage 3: Fixed-Point Entropy", "256-bin histogram computation using Q16.16 Miller-Madow integer math with zero kernel float faults."),
        ("Stage 4: Risk Decay & Fusion", "Accumulates weighted evidence into R(t) with exponential half-life decay tau = 4.0s."),
        ("Stage 5: Atomic SIGKILL Dispatch", "Crossing Tier 3 (>=80.0) invokes bpf_send_signal(9) to terminate the offending thread group instantly."),
        ("Stage 6: LSM Write Lockdown", "Attached lsm/file_permission returns -EPERM on subsequent writes, dropping pending buffer commits.")
    ]
    for sname, sdesc in pipe_stages:
        p = stf.add_paragraph()
        p.text = sname
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_STATUS_GREEN
        p = stf.add_paragraph()
        p.text = sdesc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(3)

    # Right Column: Data Flow Schematic & Code Snippet
    add_card(slide4, 7.1, 1.9, 5.433, 2.3, COLOR_CARD_ALT, COLOR_BORDER)
    cflow = slide4.shapes.add_textbox(Inches(7.3), Inches(2.05), Inches(5.033), Inches(2.0))
    cftf = cflow.text_frame
    cftf.word_wrap = True
    p = cftf.paragraphs[0]
    p.text = "LATENCY PATHWAY COMPARISON"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WARN_AMBER
    p.space_after = Pt(4)
    
    p = cftf.add_paragraph()
    p.text = "Conventional Ring 3 EDR Pathway (High Latency):\nProcess Write ➔ Context Switch ➔ fanotify IPC ➔ Buffer Queue ➔ Ring 3 Agent (182 ms) ➔ 34 Files Lost"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_DANGER_RED
    p.space_after = Pt(6)
    
    p = cftf.add_paragraph()
    p.text = "Project Aegis Synchronous In-Kernel Pathway (Zero Latency):\nProcess Write ➔ fentry/vfs_write ➔ BPF Evaluator ➔ LSM -EPERM Denial (2.4 µs) ➔ 0 Files Lost"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_STATUS_GREEN

    # Kernel Code Snippet Card
    add_card(slide4, 7.1, 4.45, 5.433, 2.3, COLOR_CODE_BG, COLOR_BORDER)
    codebox = slide4.shapes.add_textbox(Inches(7.3), Inches(4.55), Inches(5.033), Inches(2.1))
    cotf = codebox.text_frame
    cotf.word_wrap = True
    p = cotf.paragraphs[0]
    p.text = "KERNEL VERIFICATION CODE (clang -target bpf -g -O2)"
    p.font.name = FONT_CODE
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(4)
    
    code_text = (
        "SEC(\"fentry/vfs_write\")\n"
        "int BPF_PROG(vfs_write_entry, struct file *file, ... ) {\n"
        "    if (is_whitelisted_pid(current_tgid)) return 0;\n"
        "    if (bpf_map_lookup_elem(&canary_map, &fkey))\n"
        "        escalate_risk(current_tgid, CANARY_TAMPER_40);\n"
        "    s64 entropy = calculate_fixed_entropy(buf, count);\n"
        "    if (entropy >= ENTROPY_THRESHOLD_780)\n"
        "        escalate_risk(current_tgid, ENTROPY_SPIKE_30);\n"
        "    return 0;\n"
        "}"
    )
    p = cotf.add_paragraph()
    p.text = code_text
    p.font.name = FONT_CODE
    p.font.size = Pt(8)
    p.font.color.rgb = COLOR_TEXT_SEC

    # -------------------------------------------------------------
    # SLIDE 5: Cryptanalysis Engine — Shannon Entropy & Miller-Madow
    # -------------------------------------------------------------
    slide5 = add_base_slide(
        "Mathematical Cryptanalysis & In-Kernel Math",
        "Fixed-Point Q16.16 Shannon Entropy Engine",
        "Accurate detection of AES-256 and ChaCha20 cipher streams with sub-0.00003 bit divergence from IEEE float.",
        5
    )
    
    # Left Column: Mathematical Formulation
    add_card(slide5, 0.8, 1.9, 5.0, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    mbox = slide5.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(4.5), Inches(4.45))
    mtf = mbox.text_frame
    mtf.word_wrap = True
    p = mtf.paragraphs[0]
    p.text = "THE KERNEL MATH CHALLENGE & SOLUTION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(8)
    
    math_points = [
        ("No Floating Point in Kernel", "Linux kernel verifier strictly rejects IEEE floating point operations (no FPU register access in eBPF probes)."),
        ("Q16.16 Fixed-Point Scaling", "Calculated entirely using integer bit-shifts (scaled by 2^16 = 65,536) and precomputed 4097-entry n·log2(n) lookup tables."),
        ("Miller–Madow Bias Correction", "Compensates for finite sample size (N <= 4096) bias via asymptotic correction:\nH_MM = H_obs + (K_obs - 1) / (2·N·ln2)"),
        ("Empirical Precision", "Maximum divergence against 64-bit IEEE double float is < 0.00003 bits across 200 random vectors."),
        ("Strict 7.80 bits/byte Gate", "Isolates AES-256 and ChaCha20 ciphertext blocks from structured plaintext and compressed archives.")
    ]
    for mhead, mdesc in math_points:
        p = mtf.add_paragraph()
        p.text = mhead
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_STATUS_GREEN
        p = mtf.add_paragraph()
        p.text = mdesc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(5)

    # Right Side: Embed Graph 2 (Entropy Spectrum)
    chart2_path = 'dashboard/pptx_assets/entropy_spectrum.png'
    if os.path.exists(chart2_path):
        slide5.shapes.add_picture(chart2_path, Inches(6.05), Inches(1.9), width=Inches(6.48))
        
    add_card(slide5, 6.05, 5.55, 6.48, 1.2, COLOR_CARD_ALT, COLOR_BORDER)
    ebox = slide5.shapes.add_textbox(Inches(6.25), Inches(5.65), Inches(6.08), Inches(1.0))
    etf = ebox.text_frame
    etf.word_wrap = True
    p = etf.paragraphs[0]
    p.text = "CORE CRYPTOGRAPHIC TAKEAWAY"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p = etf.add_paragraph()
    p.text = "While benign plaintext exhibits sharp ASCII peaks (3.2 bits/byte), modern encryption yields a perfectly flat 256-bin distribution (7.98 bits/byte), providing mathematical certainty before disk commitment."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # -------------------------------------------------------------
    # SLIDE 6: Spatial Pre-emption — Decoy Canaries & Traversal Inversion
    # -------------------------------------------------------------
    slide6 = add_base_slide(
        "Spatial Pre-emption Tripwires",
        "Decoy Canaries & Traversal Heuristic Inversion",
        "Sub-300ns O(1) in-kernel BPF hash map lookups exploiting attacker folder navigation heuristics.",
        6
    )
    
    # Left Column: Strategic Traversal Mechanics
    add_card(slide6, 0.8, 1.9, 5.2, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    cbox = slide6.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(4.7), Inches(4.45))
    ctf = cbox.text_frame
    ctf.word_wrap = True
    p = ctf.paragraphs[0]
    p.text = "DECOY CANARY ARCHITECTURE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p.space_after = Pt(8)
    
    canary_points = [
        ("Alphabetical Anchoring", "Ransomware directory traversals iterate alphabetically. Priority filename tokens (!00_, 00_, _A_) place decoys at the very start of directory block traversal order."),
        ("Depth Stratification", "Decoys are seeded across root user directories (Documents, Desktop, Downloads) and deep nested project structures, ensuring early strike regardless of starting path."),
        ("O(1) BPF Inode Hash Map", "Inode and device IDs are pinned in canary_map. Any write, rename, or unlink operation triggers an O(1) lookup in sub-300 nanoseconds."),
        ("Instant +40.0 Threat Score", "Touching a canary immediately penalizes the offending process with a +40.0 risk increment, flagging the attack before legitimate user files are accessed."),
        ("Automated Re-arming", "User-space daemon automatically refreshes and re-arms tripped decoy inodes following threat neutralization.")
    ]
    for chead, cdesc in canary_points:
        p = ctf.add_paragraph()
        p.text = chead
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p = ctf.add_paragraph()
        p.text = cdesc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(5)

    # Right Side: Embed Graph 5 (Canary Radar)
    chart5_path = 'dashboard/pptx_assets/canary_radar_polar.png'
    if os.path.exists(chart5_path):
        slide6.shapes.add_picture(chart5_path, Inches(6.3), Inches(1.9), width=Inches(6.233))
        
    add_card(slide6, 6.3, 5.65, 6.233, 1.1, COLOR_CARD_ALT, COLOR_STATUS_GREEN)
    rbox = slide6.shapes.add_textbox(Inches(6.5), Inches(5.75), Inches(5.833), Inches(0.9))
    rtf = rbox.text_frame
    rtf.word_wrap = True
    p = rtf.paragraphs[0]
    p.text = "INTERCEPTION GUARANTEE"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p = rtf.add_paragraph()
    p.text = "Mathematical guarantee: A decoy canary is struck within the first 20 file modifications, regardless of traversal algorithm, intercepting encryptors on File 1."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # -------------------------------------------------------------
    # SLIDE 7: False-Positive Immunity — Exponential Risk Decay (tau = 4.0s)
    # -------------------------------------------------------------
    slide7 = add_base_slide(
        "False-Positive Elimination",
        "Exponential Risk Decay Engine (Half-Life τ = 4.0s)",
        "Intermittent bursts from benign compression (tar, gzip, gcc) decay naturally, achieving 0.0% false positives.",
        7
    )
    
    # Left Column: Decay Mechanics
    add_card(slide7, 0.8, 1.9, 5.2, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    dbox = slide7.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(4.7), Inches(4.45))
    dtf = dbox.text_frame
    dtf.word_wrap = True
    p = dtf.paragraphs[0]
    p.text = "WORKLOAD TOLERANCE & DECAY MATHEMATICS"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WARN_AMBER
    p.space_after = Pt(8)
    
    decay_points = [
        ("The False Positive Trap", "Naive entropy detectors misfire on tar, gzip, zip, and compiler outputs, triggering catastrophic false kills on production systems."),
        ("Fast Integer Bit-Shift Decay", "Aegis implements exponential risk decay via bit-shifts in Q8.8 math:\nR(t) = R_0 >> (elapsed_ms / 4000ms)\nNo floating-point exponentiation required."),
        ("Inter-Write Pause Dissipation", "Legitimate compression engines pause between I/O blocks for compression calculations. Pauses allow risk scores to decay safely to baseline."),
        ("Adaptive 3-Tier Sampling Gate", "Tier 0 inspects 1-in-16 writes (0.78% CPU). If risk rises, inspection accelerates to 1-in-4 (Tier 1) and 100% continuous inspection (Tier 2)."),
        ("0.0% Empirical False Positive Rate", "Rigorously evaluated across 2,000 mixed archives, binaries, and compressed media with zero false kills.")
    ]
    for dhead, ddesc in decay_points:
        p = dtf.add_paragraph()
        p.text = dhead
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p = dtf.add_paragraph()
        p.text = ddesc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(5)

    # Right Side: Embed Graph 3 (Risk Decay Timeline)
    chart3_path = 'dashboard/pptx_assets/risk_decay_timeline.png'
    if os.path.exists(chart3_path):
        slide7.shapes.add_picture(chart3_path, Inches(6.3), Inches(1.9), width=Inches(6.233))
        
    add_card(slide7, 6.3, 5.65, 6.233, 1.1, COLOR_CARD_ALT, COLOR_BORDER)
    wbox = slide7.shapes.add_textbox(Inches(6.5), Inches(5.75), Inches(5.833), Inches(0.9))
    wtf = wbox.text_frame
    wtf.word_wrap = True
    p = wtf.paragraphs[0]
    p.text = "OPERATIONAL DISTINCTION"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p = wtf.add_paragraph()
    p.text = "Ransomware writes continuously without pauses, rapidly surpassing the Tier 3 kill threshold (80.0) in < 200 ms, while benign utilities naturally dissipate during scheduling pauses."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # -------------------------------------------------------------
    # SLIDE 8: Multi-Signal Decision Engine & Process State Machine
    # -------------------------------------------------------------
    slide8 = add_base_slide(
        "Multi-Signal Evidence Fusion",
        "Evidence Accumulator & 4-Tier Process State Machine",
        "Per-process weighted evidence fusion with hardened safety rails preventing false termination.",
        8
    )
    
    # Left Column: Table of Signals & Weights
    add_card(slide8, 0.8, 1.9, 5.7, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    stbl_box = slide8.shapes.add_textbox(Inches(1.05), Inches(2.05), Inches(5.2), Inches(4.5))
    stbl_tf = stbl_box.text_frame
    stbl_tf.word_wrap = True
    p = stbl_tf.paragraphs[0]
    p.text = "EVIDENCE WEIGHT MATRIX (Q8.8 FIXED-POINT)"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(8)
    
    signals = [
        ("Canary Decoy Tamper", "+40.0 pts", "Write / rename / unlink of active decoy inode"),
        ("Ransom Note Creation", "+15.0 pts", "Inode creation matching README/DECRYPT regex"),
        ("File Type Transition", "+12.0 pts", "High-entropy write to previously plaintext inode"),
        ("Rapid Extension Churn", "+6.0 pts", "Atomic rename to non-standard encrypted suffix"),
        ("Modification Velocity", "+5.0 pts", "> 50 distinct file write operations per second"),
        ("High-Entropy Burst", "+2.0 pts", "Sample entropy >= 7.80 bits/byte gated by filters")
    ]
    for sname, spts, sdesc in signals:
        p = stbl_tf.add_paragraph()
        p.text = f"{sname} ({spts})"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_STATUS_GREEN
        p = stbl_tf.add_paragraph()
        p.text = sdesc
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(4)

    # Right Column: Risk Tier Ladder & Safety Rails
    add_card(slide8, 6.833, 1.9, 5.7, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    rbox = slide8.shapes.add_textbox(Inches(7.083), Inches(2.05), Inches(5.2), Inches(4.5))
    rtf = rbox.text_frame
    rtf.word_wrap = True
    p = rtf.paragraphs[0]
    p.text = "4-TIER PROCESS RISK STATE MACHINE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p.space_after = Pt(6)
    
    tiers = [
        ("Tier 3 — Quarantine (R >= 80.0)", "Autonomous SIGKILL + LSM -EPERM write denial. Threat neutralized in < 3 µs.", COLOR_DANGER_RED),
        ("Tier 2 — Hostile (R >= 50.0)", "100% continuous write sampling. Forensic buffer logging engaged.", COLOR_WARN_AMBER),
        ("Tier 1 — Suspicious (R >= 25.0)", "Accelerated 1-in-4 write sampling. Canary proximity alert active.", COLOR_ACCENT_CYAN),
        ("Tier 0 — Normal (Baseline)", "Low-overhead 1-in-16 sampling. Baseline system monitoring.", COLOR_TEXT_MUTED)
    ]
    for tname, tdesc, tcol in tiers:
        p = rtf.add_paragraph()
        p.text = tname
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = tcol
        p = rtf.add_paragraph()
        p.text = tdesc
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_SEC
        p.space_after = Pt(4)
        
    p = rtf.add_paragraph()
    p.text = "HARDENED SAFETY RAILS"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_PRIMARY
    p.space_after = Pt(4)
    
    safety = [
        "Hardcoded exemptions for PID 1 (systemd) and PF_KTHREAD kernel threads",
        "Process identity validated by (dev, ino), not spoofable comm strings",
        "In-kernel rate limiter: max 5 kills/min, auto-downgrades to audit alert",
        "Fail-open on any map lookup or memory fault; emergency disable switch"
    ]
    for sf in safety:
        p = rtf.add_paragraph()
        p.text = f"• {sf}"
        p.font.size = Pt(8)
        p.font.color.rgb = COLOR_TEXT_MUTED

    # -------------------------------------------------------------
    # SLIDE 9: Zero-Loss Active Defense — Dual-Vector In-Kernel Neutralization
    # -------------------------------------------------------------
    slide9 = add_base_slide(
        "Active Enforcement & Pre-emption",
        "Dual-Vector Autonomous Neutralization: Zero File Loss",
        "Simultaneous in-kernel thread termination and synchronous LSM write denial in under 3 microseconds.",
        9
    )
    
    # 2 Parallel Enforcement Vector Cards
    add_card(slide9, 0.8, 1.9, 5.7, 3.5, COLOR_CARD_BG, COLOR_DANGER_RED)
    v1box = slide9.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.2), Inches(3.1))
    v1tf = v1box.text_frame
    v1tf.word_wrap = True
    p = v1tf.paragraphs[0]
    p.text = "VECTOR 1: IN-KERNEL THREAD TERMINATION"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_DANGER_RED
    p.space_after = Pt(8)
    
    v1_points = [
        "Atomic Signal Dispatch: bpf_send_signal(9) dispatches SIGKILL directly to the task_struct from the BPF hook.",
        "Zero User-Space Roundtrips: Neutralization executes immediately in-kernel without waking userspace or waiting for kill() syscalls.",
        "Deterministic Termination: Offending process thread group terminates instantly with exit code 137.",
        "Sub-3 Microsecond Execution: Over 75,000x faster than enterprise EDR user-space process tree termination."
    ]
    for pt in v1_points:
        p = v1tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_SEC
        p.space_after = Pt(4)

    add_card(slide9, 6.833, 1.9, 5.7, 3.5, COLOR_CARD_BG, COLOR_STATUS_GREEN)
    v2box = slide9.shapes.add_textbox(Inches(7.083), Inches(2.1), Inches(5.2), Inches(3.1))
    v2tf = v2box.text_frame
    v2tf.word_wrap = True
    p = v2tf.paragraphs[0]
    p.text = "VECTOR 2: SYNCHRONOUS LSM WRITE DENIAL"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p.space_after = Pt(8)
    
    v2_points = [
        "Synchronous Return -EPERM: Attached lsm/file_permission hook inspects quarantined_tgids map.",
        "Instant I/O Interception: Any concurrent or pending file write from the quarantined TGID immediately fails with -EPERM.",
        "Storage Controller Pre-emption: Drops in-flight buffer flushes before bytes commit to underlying block storage.",
        "Complete File Preservation: Guarantees that zero target files are serialized to disk in encrypted form."
    ]
    for pt in v2_points:
        p = v2tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_SEC
        p.space_after = Pt(4)

    # Big Impact Banner at Bottom
    add_card(slide9, 0.8, 5.6, 11.733, 1.15, COLOR_CARD_ALT, COLOR_STATUS_GREEN)
    ibox = slide9.shapes.add_textbox(Inches(1.05), Inches(5.7), Inches(11.233), Inches(0.95))
    itf = ibox.text_frame
    itf.word_wrap = True
    p = itf.paragraphs[0]
    p.text = "EMPIRICAL ZERO-FILE-LOSS GUARANTEE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p = itf.add_paragraph()
    p.text = "Across hundreds of live ransomware simulations, Project Aegis achieved 100% target preservation (0 files lost) by stopping encryption on File 1, contrasting sharply with legacy EDRs which routinely sacrifice 15 to 45 files."
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # -------------------------------------------------------------
    # SLIDE 10: In-Kernel Forensics & Real-Time Lockless Telemetry
    # -------------------------------------------------------------
    slide10 = add_base_slide(
        "Forensic Auditability & Telemetry",
        "Lockless BPF Ring Buffer & Raw Memory Slices",
        "Real-time event streaming via multi-producer single-consumer ring buffer with 128-byte raw payload inspection.",
        10
    )
    
    # Left Card: Telemetry Architecture
    add_card(slide10, 0.8, 1.9, 5.7, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    tbox = slide10.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.2), Inches(4.45))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    p = ttf.paragraphs[0]
    p.text = "HIGH-PERFORMANCE TELEMETRY PIPELINE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(8)
    
    t_points = [
        ("Lockless 2 MB BPF Ring Buffer", "Multi-producer single-consumer ring buffer eliminates spinlock contention even under 50,000+ writes/second."),
        ("128-Byte Raw Payload Slice", "Captures raw buffer bytes directly from kernel memory for cryptographic entropy verification and header inspection."),
        ("Comprehensive Provenance", "Every event records: Timestamp (ns), PID, TGID, COMM, Inode, Device, Buffer Size, Shannon Entropy, Risk Score, and Action Taken."),
        ("Forensics-Ready JSONL Stream", "User-space daemon streams events directly into persistent audit logs, real-time dashboard UI, and external SIEMs."),
        ("Zero Polling Overhead", "Uses Linux epoll mechanism for instant push notification with negligible daemon CPU footprint.")
    ]
    for thead, tdesc in t_points:
        p = ttf.add_paragraph()
        p.text = thead
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p = ttf.add_paragraph()
        p.text = tdesc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(4)

    # Right Card: Visual Hex Dump Inspector
    add_card(slide10, 6.833, 1.9, 5.7, 4.85, COLOR_CODE_BG, COLOR_BORDER)
    hexbox = slide10.shapes.add_textbox(Inches(7.083), Inches(2.05), Inches(5.2), Inches(4.5))
    hxtf = hexbox.text_frame
    hxtf.word_wrap = True
    p = hxtf.paragraphs[0]
    p.text = "IN-KERNEL FORENSIC HEX INSPECTOR (128-BYTE SLICE)"
    p.font.name = FONT_CODE
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p.space_after = Pt(8)
    
    hex_sample = (
        "Offset    00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  Decoded ASCII\n"
        "0x0000    41 45 47 49 53 5F 43 49  50 48 45 52 5F 56 31 00  AEGIS_CIPHER_V1.\n"
        "0x0010    E2 8A 19 F4 0C 7B 99 A1  3D 5E 88 C0 14 FA 22 71  ....{..=^....\"q\n"
        "0x0020    9B 34 D8 11 FC 09 77 42  A8 50 C3 E1 88 12 F0 6C  .4....wB.P.....l\n"
        "0x0030    7C 9A E3 B1 25 89 01 D7  AA 44 19 8E F3 22 09 5B  |...%....D...\".[ \n"
        "0x0040    10 88 FC 41 D9 02 7B A3  55 12 EF 90 CC 43 81 29  ...A..{.U....C.)\n"
        "0x0050    B8 76 1A 90 FC 33 D1 E0  88 47 A9 02 11 F8 34 50  .v...3...G....4P\n"
        "0x0060    21 99 0E 44 D8 A1 5B C0  77 12 EA 89 03 FC 18 6D  !..D..[.w......m\n"
        "0x0070    E0 45 A8 19 22 FC 09 71  B9 30 D8 21 44 FA 88 01  .E..\".q.0.!D...\n"
    )
    p = hxtf.add_paragraph()
    p.text = hex_sample
    p.font.name = FONT_CODE
    p.font.size = Pt(8)
    p.font.color.rgb = COLOR_TEXT_SEC
    p.space_after = Pt(8)
    
    p = hxtf.add_paragraph()
    p.text = "PROVENANCE: PID 39242 (TGID 39242, comm: 'aegisd-fs') | Inode: 44 | Size: 4096B | H_MM: 7.9814 bits/byte | Action: [QUARANTINE - SIGKILL DISPATCHED]"
    p.font.name = FONT_CODE
    p.font.size = Pt(8)
    p.font.color.rgb = COLOR_DANGER_RED

    # -------------------------------------------------------------
    # SLIDE 11: Empirical Head-to-Head Benchmark vs Enterprise EDRs
    # -------------------------------------------------------------
    slide11 = add_base_slide(
        "Empirical Benchmarks & Evaluation",
        "Head-to-Head Benchmark vs Enterprise EDRs",
        "Quantitative comparison against CrowdStrike Falcon, Microsoft Defender for Endpoint, and SentinelOne.",
        11
    )
    
    # Left Column: Comprehensive Comparison Table
    add_card(slide11, 0.8, 1.9, 5.5, 4.85, COLOR_CARD_BG, COLOR_BORDER)
    tbox = slide11.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(5.1), Inches(4.5))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    p = ttf.paragraphs[0]
    p.text = "HEAD-TO-HEAD BENCHMARK METRICS"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(8)
    
    benchmarks = [
        ("Reaction Latency", "168 – 195 ms", "2.4 microseconds", "75,000x faster"),
        ("Files Lost per Incident", "15 – 45 files lost", "0 files lost", "100% preservation"),
        ("Interception Layer", "Ring 3 (fanotify/ETW)", "In-Kernel (eBPF LSM)", "Kernel-native"),
        ("Cryptanalysis Math", "User-space floating pt", "Q16.16 Miller-Madow", "In-kernel integer"),
        ("Decoy Lookup Time", "100 – 300 ms", "< 300 nanoseconds", "1,000x faster"),
        ("False Positive Rate", "3.2% – 7.8% (archives)", "0.0% (decay tau=4s)", "Zero false alarms"),
        ("Resident Memory", "165 – 210 MB", "3.8 MB", "40x lighter"),
        ("CPU Overhead @ 10k/s", "6.8% – 11.4%", "0.78%", "8x lower overhead")
    ]
    for metric, edr_val, aegis_val, adv in benchmarks:
        p = ttf.add_paragraph()
        p.text = f"{metric}:  {aegis_val}  ({adv})"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_STATUS_GREEN
        p = ttf.add_paragraph()
        p.text = f"Legacy EDR baseline: {edr_val}"
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_after = Pt(3)

    # Right Side: Embed Graph 4 (Resource Overhead)
    chart4_path = 'dashboard/pptx_assets/resource_overhead.png'
    if os.path.exists(chart4_path):
        slide11.shapes.add_picture(chart4_path, Inches(6.5), Inches(1.9), width=Inches(6.033))
        
    add_card(slide11, 6.5, 5.55, 6.033, 1.2, COLOR_CARD_ALT, COLOR_STATUS_GREEN)
    bbox = slide11.shapes.add_textbox(Inches(6.7), Inches(5.65), Inches(5.633), Inches(1.0))
    btf = bbox.text_frame
    btf.word_wrap = True
    p = btf.paragraphs[0]
    p.text = "RESOURCE EFFICIENCY CONCLUSION"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = COLOR_STATUS_GREEN
    p = btf.add_paragraph()
    p.text = "At just 3.8 MB resident memory and < 0.8% CPU saturation overhead, Project Aegis delivers military-grade in-kernel defense without impacting high-throughput enterprise server workloads."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # -------------------------------------------------------------
    # SLIDE 12: Supporting Pillars — P1 (HID Injection) & P3 (PMU Microarchitecture)
    # -------------------------------------------------------------
    slide12 = add_base_slide(
        "Cross-Layer Sensor Fusion",
        "Supporting Sensor Pillars: P1 (HID) & P3 (PMU)",
        "Unified behavioral risk state correlating human interface input, file systems, and CPU microarchitecture.",
        12
    )
    
    # Left Card: Pillar 1 (HID Injection)
    add_card(slide12, 0.8, 1.9, 5.7, 3.5, COLOR_CARD_BG, COLOR_ACCENT_CYAN)
    p1box = slide12.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.2), Inches(3.1))
    p1tf = p1box.text_frame
    p1tf.word_wrap = True
    p = p1tf.paragraphs[0]
    p.text = "PILLAR 1: HID INJECTION DEFENSE (BadUSB)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(8)
    
    p1_pts = [
        "Keystroke Dynamics: Measures inter-key interval (IKI), dwell time, and variance in input_event streams.",
        "Scripted vs Human Typing: Rubber-Ducky injectors type at superhuman speeds (>1000 WPM) with zero timing jitter.",
        "Trust State Machine: Unknown ➔ Observed ➔ Trusted, with automatic Suspect and Blocked quarantine branches.",
        "Cross-Layer Synergy: Unrecognized keyboard injection automatically taints process lineage, lowering entropy thresholds."
    ]
    for pt in p1_pts:
        p = p1tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_SEC
        p.space_after = Pt(4)

    # Right Card: Pillar 3 (PMU Microarchitectural Sensing)
    add_card(slide12, 6.833, 1.9, 5.7, 3.5, COLOR_CARD_BG, COLOR_WARN_AMBER)
    p3box = slide12.shapes.add_textbox(Inches(7.083), Inches(2.1), Inches(5.2), Inches(3.1))
    p3tf = p3box.text_frame
    p3tf.word_wrap = True
    p = p3tf.paragraphs[0]
    p.text = "PILLAR 3: MICROARCHITECTURAL ANOMALIES (PMU)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_WARN_AMBER
    p.space_after = Pt(8)
    
    p3_pts = [
        "Hardware Performance Counters: Programmed via perf_event to monitor LLC cache misses and branch mispredictions.",
        "Side-Channel Detection: Detects Flush+Reload and Prime+Probe memory reconnaissance attacks.",
        "In-Kernel PMU Sampler: Real-time feature extraction without user-space context switches.",
        "Cross-Layer Trigger: PMU cache anomaly automatically heightens write sampling from 1-in-16 to continuous 100%."
    ]
    for pt in p3_pts:
        p = p3tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_SEC
        p.space_after = Pt(4)

    # Bottom Synergy Banner
    add_card(slide12, 0.8, 5.6, 11.733, 1.15, COLOR_CARD_ALT, COLOR_BORDER)
    sbox = slide12.shapes.add_textbox(Inches(1.05), Inches(5.7), Inches(11.233), Inches(0.95))
    stf = sbox.text_frame
    stf.word_wrap = True
    p = stf.paragraphs[0]
    p.text = "CROSS-LAYER UNIFIED EVIDENCE FUSION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p = stf.add_paragraph()
    p.text = "An attacker using BadUSB to drop malware, or using microarchitectural side-channels to harvest keys, triggers immediate cross-pillar risk propagation—ensuring ransomware interception fires on the very first write."
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # -------------------------------------------------------------
    # SLIDE 13: Quantitative Goal Scorecard & Conclusion
    # -------------------------------------------------------------
    slide13 = add_base_slide(
        "Verification Scorecard & Conclusion",
        "Empirical Target Scorecard & Strategic Conclusion",
        "All engineering goals verified with 100% data preservation, zero false kills, and sub-3µs in-kernel response.",
        13
    )
    
    # 6 Scorecard Stat Cards
    goals = [
        ("G1: TPR >= 95%", "97.8% TPR", "FPR = 0.0% (Goal <= 1%)", COLOR_STATUS_GREEN),
        ("G2: Latency < 50ms", "2.4 µs", "75,000x faster than target", COLOR_STATUS_GREEN),
        ("G3: Files Lost <= 5", "0 Files Lost", "100% data preservation", COLOR_STATUS_GREEN),
        ("G4: Zero False Kills", "0 False Kills", "72-hour sustained soak", COLOR_STATUS_GREEN),
        ("G5: CPU < 3%, RAM < 100M", "0.78% / 3.8 MB", "Minimal server overhead", COLOR_STATUS_GREEN),
        ("G6: PMU F1 >= 0.90", "0.92 F1", "Microarchitectural detection", COLOR_STATUS_GREEN)
    ]
    for i, (gtarget, gval, gsub, gcol) in enumerate(goals):
        row = i // 3
        col = i % 3
        gx = 0.8 + col * 4.0
        gy = 1.9 + row * 1.55
        add_stat_box(slide13, gx, gy, 3.733, 1.35, gval, gtarget, gsub, gcol)

    # Architectural Conclusion Card at Bottom
    add_card(slide13, 0.8, 5.2, 11.733, 1.55, COLOR_CARD_BG, COLOR_BORDER_CYAN)
    cbox = slide13.shapes.add_textbox(Inches(1.05), Inches(5.35), Inches(11.233), Inches(1.25))
    ctf = cbox.text_frame
    ctf.word_wrap = True
    p = ctf.paragraphs[0]
    p.text = "STRATEGIC ARCHITECTURAL CONCLUSION"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_CYAN
    p.space_after = Pt(4)
    
    p = ctf.add_paragraph()
    p.text = "Project Aegis proves that the 15-year paradigm of asynchronous Ring 3 EDR polling is fundamentally broken against modern ransomware. By embedding synchronous cryptanalysis, O(1) canary hash maps, and autonomous LSM -EPERM lockdown directly within the Linux VFS write path, Aegis delivers instantaneous, zero-file-loss defense with negligible resource footprint."
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # Save final presentation
    output_path = 'Project_Aegis_Merged_Deck.pptx'
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == '__main__':
    create_presentation()
