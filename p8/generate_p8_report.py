from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

OUT = "p8/P8_User_Testing_Report.pdf"
BLUE = colors.HexColor("#143D59")
TEAL = colors.HexColor("#0F766E")
INK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#5B6470")
PALE = colors.HexColor("#EAF2F8")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=28, leading=34, textColor=BLUE, alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontName="Helvetica", fontSize=13, leading=20, textColor=MUTED, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=24, textColor=BLUE, spaceBefore=4, spaceAfter=10))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=TEAL, spaceBefore=9, spaceAfter=5))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=14, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10.5, textColor=INK))
styles.add(ParagraphStyle(name="TableHeader", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white))
styles.add(ParagraphStyle(name="Quote", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=9.4, leading=14, textColor=INK, leftIndent=14, borderColor=colors.HexColor("#8DB5C9"), borderWidth=2, borderPadding=7, spaceAfter=8))

def P(text, style="Bodyx"):
    return Paragraph(text, styles[style])

def table(data, widths, small=False):
    body_style = styles["Smallx"] if small else styles["Bodyx"]
    cooked = [[Paragraph(str(v), styles["TableHeader"] if i == 0 else body_style) for v in row] for i, row in enumerate(data)]
    t = Table(cooked, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#B8C6D1")),
        ("BACKGROUND", (0,1), (-1,-1), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, PALE]),
        ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B8C6D1"))
    canvas.line(0.7*inch, 0.55*inch, 7.8*inch, 0.55*inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.7*inch, 0.37*inch, "Score Companion | P#8 User Testing")
    canvas.drawRightString(7.8*inch, 0.37*inch, f"Page {doc.page}")
    canvas.restoreState()

story = []
story += [Spacer(1, 1.35*inch), P("SCORE COMPANION", "CoverTitle"), P("P#8 User Testing Report", "CoverTitle"), Spacer(1, 0.2*inch), P("Team 08 | October 18, 2026", "CoverSub"), Spacer(1, 0.45*inch), P("A formative usability study of a rehearsal score companion for musicians who need reliable score access and fast, contextual practice reminders.", "CoverSub"), Spacer(1, 0.7*inch), P("Testing concluded after three participants by team decision. All evidence is anonymized.", "CoverSub"), PageBreak()]

story += [P("Executive summary", "H1x"), P("Three musicians completed a Wizard-of-Oz test of Score Companion's core flow: open an offline score, mark a difficult measure, add context, review it, and mark it resolved. Everyone completed the task, but participants repeatedly struggled to understand what a marker saved, how to reach the practice review, and what the sparse, non-musical score representation meant. The team will prioritize realistic score context and an explicit mark-to-note-to-review flow before adding requested secondary tools. Offline availability and the resolved confirmation remain because participants valued them. These conclusions are directional, based on a small formative sample of three participants."),
P("Methodology", "H1x"), P("The team used a think-aloud Wizard-of-Oz protocol with the static P#7/P#8 prototype. Participants were asked to describe what they saw and what they would tap while moving through the offline library, score view, marker, note, review, and resolved states. The available records include two supplied anonymous observation forms and one complete GitLab session note. The first two records list 2:00 and 1:30 completion times; the GitLab record does not contain a duration. No personal names or contact information are retained."),
table([["Participant", "Segment / context", "Completion", "Time", "Evidence source"], ["P1", "Format-Constrained Score Navigator", "Yes", "2:00", "Supplied observation PDF"], ["P2", "Reactive Score Annotator", "Yes", "1:30", "Supplied observation PDF"], ["P3", "Musician using a tablet before practice", "Yes, with confusion", "Not recorded", "GitLab issue #19 note"]], [0.7*inch, 1.75*inch, 1.0*inch, 0.65*inch, 2.7*inch], small=True),
Spacer(1, 9), P("Study limitation", "H2x"), P("The records support behavior, comments, and design decisions, but some session logistics (such as exact attendance roles and full timestamps) were not recorded. The results should guide the next prototype iteration, not be treated as generalizable measurement.") , PageBreak()]

story += [P("Session summaries", "H1x"), P("Participant 1 - Format-Constrained Score Navigator", "H2x"), P("P1 completed the task in two minutes, but did not know where to tap in the score view and did not know to use Practice review after saving a measure. They asked how to add songs and whether display quality would improve. The participant said the slide did not look like normal sheet music and lacked enough song context for the unresolved-passages view. Their suggestion was to make measures resemble sheet music and provide a text prompt for practice notes. They would not use the prototype in its current form because it felt convoluted and insufficiently interactive."),
P("Participant 2 - Reactive Score Annotator", "H2x"), P("P2 completed the task in 1.5 minutes. They attempted to open Practice review before saving a measure and asked whether the action was a correction or merely a saved measure. They described the experience as empty and were unsure whether a displayed note came from them or from AI. They repeated P1's suggestions for music-like measures and a clearer note prompt, and added tuner/metronome ideas. They saw value in offline music access and noting difficult parts, but said the current prototype was not different enough to use."),
P("Participant 3 - GitLab session", "H2x"), P("P3 valued the offline-ready badge because rehearsal Wi-Fi is unreliable. They could navigate the flow but did not recognize the marker icon, initially went back to the library after saving, and found the phrase 'add context after rehearsal' too specific for a before-practice use case. They expected to mark multiple measures. They liked the large resolved checkmark because it felt like an accomplishment. The full downloaded local record is retained in the P8 folder."),
P("Representative evidence", "H2x"), P('"This slide does not look like normal sheet music." - P1', "Quote"), P('"What is the correction I am adding? Or am I just saving the specific measures?" - P2', "Quote"), P('"I do like [offline ready] because our stadium and rehearsal hall Wi-Fi is horrible." - P3', "Quote"), PageBreak()]

story += [P("Pattern analysis", "H1x"), table([["Priority", "Pattern", "Evidence", "Why it matters"], ["P0", "Score representation lacks context and credibility", "P1 and P2 asked for sheet-music-like measures; P1 lacked song context.", "A musician cannot confidently interpret a passage or review list without recognizable score and piece context."], ["P0", "Marker, cue, and review flow has a weak mental model", "P1 missed review; P2 tried it too early; P3 did not understand the marker icon.", "The core promise fails if users cannot tell what is saved or what to do next."], ["P1", "Cue wording is too time-specific", "P2 requested a clearer note prompt; P3 rejected 'after rehearsal' as too narrow.", "The tool must fit before, during, and after rehearsal."], ["P2", "Offline status and completion feedback work", "P3 explicitly valued offline ready and the resolved check; all participants completed the task.", "These reinforce the product promise and should be preserved."], ["Deferred", "Requested secondary tools do not repair the core flow", "P2 suggested tuner/metronome; P1 and P2 questioned differentiation.", "Scope must first establish understandable score marking and review."]], [0.55*inch, 1.7*inch, 2.35*inch, 2.65*inch], small=True),
Spacer(1, 12), P("Design changes and implementation plan", "H1x"), table([["Priority", "Change", "Implementation / acceptance check"], ["P0", "Use a legible score excerpt with persistent piece, movement, and measure context.", "Update score and review screens. In a first-use check, a musician can identify the piece, section, and marked measure without asking."], ["P0", "Replace the star with a labeled 'Mark for practice' action and show explicit Add note / Review saved passages next steps.", "A musician can state what was saved and reach it from the confirmation state."], ["P1", "Use neutral cue copy: 'Add a practice note now or later,' with an example.", "A musician understands that notes can be added before, during, or after rehearsal."], ["P1", "Support repeated marking and show a marked-count indicator.", "A musician can mark two measures and find both in review."], ["P2", "Retain offline-ready and resolved confirmation, with a concise next action.", "Status and completion remain visible without blocking the score task."], ["Deferred", "Do not add tuner, metronome, social features, or AI correction detection yet.", "Re-evaluate only after core comprehension validates."]], [0.55*inch, 2.25*inch, 4.45*inch], small=True), PageBreak()]

story += [P("Appendix A - Raw observation notes", "H1x"), P("Participant 1", "H2x"), P("Segment: Format-Constrained Score Navigator. Date: 10/15. Completed: yes. Time: 2 minutes. Hesitation: did not know where to tap while viewing music. Wrong turn: did not know to select Practice review after saving. Questions: how to add more songs; whether display would improve. Reactions: the slide did not look like normal sheet music; the unresolved-passages section had no song context. Suggestions: music-like measures and a text prompt for practice notes. Would use: no; too convoluted, not interactive, and not new enough."), P("Participant 2", "H2x"), P("Segment: Reactive Score Annotator. Date: 10/16. Completed: yes. Time: 1.5 minutes. Hesitation: none recorded. Wrong turn: tried Practice review before saving. Question: whether the action added a correction or only saved measures. Reactions: it looked empty; uncertainty about an existing note and whether AI made it. Suggestions: music-like measures, a text note prompt, and practice tools such as a metronome or tuner. Would use: not in its present state, though offline access and difficult-part notes could be useful."), P("Participant 3", "H2x"), P("Source: GitLab issue #19, note posted by @lpb100. P3 liked the offline-ready indication due to poor rehearsal Wi-Fi. In the score screen they selected a measure but did not know what the corner star meant. They navigated to Score library after the saved message, then completed the cue and review flow. The phrase 'add context after rehearsal' seemed too specific for a before-practice scenario. They expected to tap multiple measures when multiple corrections arise. The resolved state felt motivating. Duration was not recorded."), P("Appendix B - Traceability and project tracking", "H1x"), P("GitLab is the tracker of record. P#8 milestone: https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/milestones/3. Issues #17-#23 record preparation, recruitment, testing, observations, synthesis, decisions, and reporting. The report, supplied two-participant evidence, downloaded GitLab session record, synthesis, and implementation plan are retained together in the repository's p8 directory."), P("Source files retained in p8", "H2x"), P("P8_TwoParticipants_Issues2-4.pdf (Jonathan-supplied observation evidence); LOGAN_GITLAB_SESSION.md (downloaded GitLab session evidence); P8_SYNTHESIS_AND_IMPLEMENTATION.md (decision record); Score Companion - P8 User Testing Prototype - Figma.pdf (prototype under test).", "Smallx")]

doc = SimpleDocTemplate(OUT, pagesize=letter, rightMargin=0.7*inch, leftMargin=0.7*inch, topMargin=0.7*inch, bottomMargin=0.75*inch, title="Score Companion P8 User Testing Report", author="Team 08")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
