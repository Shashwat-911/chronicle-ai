"""
styles.py — All CSS for ChronicleAI's visual novel interface.

Provides the ``STYLES`` constant: a single CSS string injected into
the Streamlit app via ``st.markdown``. Includes Google Fonts, animated
backgrounds, styled story panels, stat bars, and character panels.
"""

STYLES = """
<style>
/* ══════════════════════════════════════════════════════════════════
   GOOGLE FONTS
   ══════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700;900&family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');

/* ══════════════════════════════════════════════════════════════════
   GLOBAL RESETS & BACKGROUND
   ══════════════════════════════════════════════════════════════════ */
.stApp {
    background: #0a0a0f;
    background-image:
        radial-gradient(ellipse at 50% 40%, rgba(30,20,10,0.5) 0%, transparent 70%),
        radial-gradient(ellipse at 80% 20%, rgba(60,40,15,0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 20% 80%, rgba(40,20,40,0.2) 0%, transparent 50%);
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

/* Animated gold particle overlay */
.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    background-image:
        radial-gradient(1px 1px at 15% 25%, rgba(201,168,76,0.4) 0%, transparent 100%),
        radial-gradient(1px 1px at 35% 65%, rgba(201,168,76,0.3) 0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 55% 15%, rgba(201,168,76,0.5) 0%, transparent 100%),
        radial-gradient(1px 1px at 75% 45%, rgba(201,168,76,0.35) 0%, transparent 100%),
        radial-gradient(1px 1px at 85% 85%, rgba(201,168,76,0.25) 0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 25% 90%, rgba(201,168,76,0.4) 0%, transparent 100%),
        radial-gradient(1px 1px at 65% 75%, rgba(201,168,76,0.3) 0%, transparent 100%),
        radial-gradient(1px 1px at 45% 50%, rgba(201,168,76,0.2) 0%, transparent 100%);
    background-size: 200% 200%;
    animation: particleDrift 20s ease-in-out infinite;
}

@keyframes particleDrift {
    0%   { background-position: 0% 100%; opacity: 0.6; }
    25%  { background-position: 50% 50%; opacity: 1; }
    50%  { background-position: 100% 0%; opacity: 0.7; }
    75%  { background-position: 50% 50%; opacity: 1; }
    100% { background-position: 0% 100%; opacity: 0.6; }
}

/* Ensure content is above the particle layer */
.stApp > * {
    position: relative;
    z-index: 1;
}

/* ══════════════════════════════════════════════════════════════════
   TYPOGRAPHY DEFAULTS
   ══════════════════════════════════════════════════════════════════ */
.stApp, .stApp p, .stApp span, .stApp li {
    font-family: 'EB Garamond', Georgia, serif !important;
    color: #e8e0d0;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Cinzel', serif !important;
    color: #c9a84c !important;
}

/* ══════════════════════════════════════════════════════════════════
   HEADER / TITLE
   ══════════════════════════════════════════════════════════════════ */
.chronicle-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}

.chronicle-title {
    font-family: 'Cinzel Decorative', serif !important;
    font-size: 3rem;
    font-weight: 900;
    background: linear-gradient(135deg, #c9a84c 0%, #f5e6a3 40%, #c9a84c 60%, #8b6914 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: none;
    letter-spacing: 3px;
    margin-bottom: 0.25rem;
    animation: titleShimmer 4s ease-in-out infinite;
    background-size: 200% 100%;
}

.chronicle-title-compact {
    font-family: 'Cinzel Decorative', serif !important;
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c9a84c 0%, #f5e6a3 40%, #c9a84c 60%, #8b6914 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 2px;
    margin-bottom: 0;
    animation: titleShimmer 4s ease-in-out infinite;
    background-size: 200% 100%;
}

@keyframes titleShimmer {
    0%   { background-position: -100% 0; }
    50%  { background-position: 100% 0; }
    100% { background-position: -100% 0; }
}

.chronicle-subtitle {
    font-family: 'EB Garamond', serif !important;
    font-size: 1.1rem;
    color: #8a7e6b;
    font-style: italic;
    letter-spacing: 2px;
    margin-top: 0;
}

/* ══════════════════════════════════════════════════════════════════
   STORY PANEL (Main DM text display)
   ══════════════════════════════════════════════════════════════════ */
.story-panel {
    background: rgba(15, 12, 8, 0.95);
    border: 1px solid rgba(201, 168, 76, 0.3);
    border-radius: 4px;
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 18px;
    line-height: 1.9;
    color: #e8e0d0;
    padding: 2rem;
    max-height: 500px;
    overflow-y: auto;
    margin: 1rem 0;
    position: relative;
    box-shadow:
        0 0 30px rgba(0,0,0,0.5),
        inset 0 0 60px rgba(0,0,0,0.3);
}

.story-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba(201,168,76,0.5), transparent);
}

/* Custom scrollbar for story panel */
.story-panel::-webkit-scrollbar {
    width: 6px;
}
.story-panel::-webkit-scrollbar-track {
    background: rgba(10, 10, 15, 0.5);
}
.story-panel::-webkit-scrollbar-thumb {
    background: rgba(201, 168, 76, 0.4);
    border-radius: 3px;
}
.story-panel::-webkit-scrollbar-thumb:hover {
    background: rgba(201, 168, 76, 0.7);
}

.story-panel p {
    margin-bottom: 1rem;
    text-indent: 1.5em;
}
.story-panel p:first-child {
    text-indent: 0;
}
.story-panel p:first-child::first-letter {
    font-family: 'Cinzel Decorative', serif;
    font-size: 2.5em;
    float: left;
    line-height: 0.8;
    margin-right: 0.1em;
    color: #c9a84c;
}

/* Fade-in animation for new story text */
.story-panel-new {
    animation: storyFadeIn 1.2s ease-out;
}

@keyframes storyFadeIn {
    0%   { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* ══════════════════════════════════════════════════════════════════
   PLAYER INPUT AREA
   ══════════════════════════════════════════════════════════════════ */
.player-input {
    border-left: 4px solid #c9a84c;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    background: rgba(15, 12, 8, 0.8);
}

.player-input-label {
    font-family: 'Cinzel', serif !important;
    font-size: 0.75rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #c9a84c;
    margin-bottom: 0.5rem;
    font-variant: small-caps;
}

.player-input-text {
    font-family: 'Courier New', monospace !important;
    color: #c9a84c;
    font-style: italic;
    font-size: 1rem;
}

/* ══════════════════════════════════════════════════════════════════
   STAT BARS (Health & Sanity)
   ══════════════════════════════════════════════════════════════════ */
.stat-bar-container {
    margin: 0.5rem 0;
}

.stat-bar-label {
    font-family: 'Cinzel', serif !important;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #8a7e6b;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stat-bar-track {
    width: 100%;
    height: 12px;
    background: rgba(20, 18, 15, 0.9);
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
    position: relative;
}

.stat-bar-fill-health {
    height: 100%;
    border-radius: 6px;
    background: linear-gradient(90deg, #8b0000, #cc2200);
    transition: width 0.8s ease-out;
    position: relative;
    box-shadow: 0 0 8px rgba(204, 34, 0, 0.4);
}

.stat-bar-fill-sanity {
    height: 100%;
    border-radius: 6px;
    background: linear-gradient(90deg, #1a0033, #6600cc);
    transition: width 0.8s ease-out;
    position: relative;
    box-shadow: 0 0 8px rgba(102, 0, 204, 0.4);
}

/* Critical shimmer when low */
.stat-bar-critical {
    animation: criticalPulse 1s ease-in-out infinite;
}

@keyframes criticalPulse {
    0%   { opacity: 1; box-shadow: 0 0 8px rgba(255,0,0,0.4); }
    50%  { opacity: 0.7; box-shadow: 0 0 20px rgba(255,0,0,0.8); }
    100% { opacity: 1; box-shadow: 0 0 8px rgba(255,0,0,0.4); }
}

/* ══════════════════════════════════════════════════════════════════
   CHARACTER PANEL (Sidebar)
   ══════════════════════════════════════════════════════════════════ */
.char-panel {
    background:
        linear-gradient(180deg, rgba(25,20,15,0.95) 0%, rgba(15,12,8,0.98) 100%);
    border: 1px solid rgba(201,168,76,0.2);
    border-radius: 4px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.char-name {
    font-family: 'Cinzel Decorative', serif !important;
    font-size: 1.1rem;
    color: #c9a84c;
    text-align: center;
    margin-bottom: 0.25rem;
}

.char-class-badge {
    display: inline-block;
    padding: 0.15rem 0.75rem;
    border-radius: 12px;
    font-family: 'Cinzel', serif !important;
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-align: center;
    width: 100%;
    margin-bottom: 0.75rem;
}

.class-warrior  { background: rgba(139,0,0,0.3); color: #e74c3c; border: 1px solid rgba(231,76,60,0.3); }
.class-mage     { background: rgba(26,0,51,0.3); color: #9b59b6; border: 1px solid rgba(155,89,182,0.3); }
.class-rogue    { background: rgba(0,51,26,0.3); color: #2ecc71; border: 1px solid rgba(46,204,113,0.3); }
.class-scholar  { background: rgba(0,26,51,0.3); color: #3498db; border: 1px solid rgba(52,152,219,0.3); }

/* ══════════════════════════════════════════════════════════════════
   INVENTORY
   ══════════════════════════════════════════════════════════════════ */
.inventory-container {
    margin: 0.75rem 0;
}

.inventory-title {
    font-family: 'Cinzel', serif !important;
    font-size: 0.75rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #8a7e6b;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid rgba(201,168,76,0.15);
    padding-bottom: 0.25rem;
}

.inventory-item {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    margin: 0.15rem;
    border-radius: 3px;
    background: rgba(201,168,76,0.1);
    border: 1px solid rgba(201,168,76,0.25);
    color: #c9a84c;
    font-family: 'EB Garamond', serif !important;
    font-size: 0.85rem;
    transition: all 0.2s;
}

.inventory-item:hover {
    background: rgba(201,168,76,0.2);
    border-color: rgba(201,168,76,0.5);
}

.inventory-empty {
    color: #4a4535;
    font-style: italic;
    font-size: 0.85rem;
}

/* ══════════════════════════════════════════════════════════════════
   QUEST LOG
   ══════════════════════════════════════════════════════════════════ */
.quest-active {
    color: #c9a84c;
    font-family: 'EB Garamond', serif !important;
    font-size: 0.9rem;
    padding: 0.25rem 0;
    border-bottom: 1px solid rgba(201,168,76,0.08);
}

.quest-completed {
    color: #4a7c59;
    font-family: 'EB Garamond', serif !important;
    font-size: 0.9rem;
    text-decoration: line-through;
    padding: 0.25rem 0;
    opacity: 0.7;
}

/* ══════════════════════════════════════════════════════════════════
   MESSAGE HISTORY
   ══════════════════════════════════════════════════════════════════ */
.history-entry {
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(201,168,76,0.08);
    margin-bottom: 0.25rem;
}

.history-player {
    text-align: right;
    color: #c9a84c;
    font-style: italic;
    font-family: 'EB Garamond', serif !important;
    font-size: 0.85rem;
}

.history-dm {
    text-align: left;
    color: #a09880;
    font-family: 'EB Garamond', serif !important;
    font-size: 0.82rem;
    line-height: 1.4;
}

.history-beat-label {
    font-family: 'Cinzel', serif !important;
    font-size: 0.6rem;
    color: #4a4535;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ══════════════════════════════════════════════════════════════════
   CHAPTER TRANSITION
   ══════════════════════════════════════════════════════════════════ */
.chapter-transition {
    text-align: center;
    padding: 3rem 2rem;
    margin: 2rem 0;
    animation: chapterReveal 2s ease-out;
}

.chapter-divider {
    width: 60%;
    margin: 1rem auto;
    height: 2px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}

.chapter-number {
    font-family: 'Cinzel Decorative', serif !important;
    font-size: 2.5rem;
    color: #c9a84c;
    letter-spacing: 8px;
    text-transform: uppercase;
}

.chapter-title {
    font-family: 'EB Garamond', serif !important;
    font-size: 1.3rem;
    color: #8a7e6b;
    font-style: italic;
    margin-top: 0.5rem;
}

@keyframes chapterReveal {
    0%   { opacity: 0; transform: scale(0.9); }
    50%  { opacity: 1; }
    100% { opacity: 1; transform: scale(1); }
}

/* ══════════════════════════════════════════════════════════════════
   GAME OVER SCREEN
   ══════════════════════════════════════════════════════════════════ */
.game-over-container {
    text-align: center;
    padding: 3rem 2rem;
    background: rgba(10, 8, 5, 0.95);
    border: 1px solid rgba(201,168,76,0.3);
    border-radius: 8px;
    margin: 2rem auto;
    max-width: 700px;
    animation: gameOverFade 2s ease-out;
}

@keyframes gameOverFade {
    0%   { opacity: 0; transform: translateY(20px); }
    100% { opacity: 1; transform: translateY(0); }
}

.game-over-title {
    font-family: 'Cinzel Decorative', serif !important;
    font-size: 2.5rem;
    color: #c9a84c;
    letter-spacing: 5px;
    margin-bottom: 1rem;
}

.ending-badge {
    display: inline-block;
    padding: 0.3rem 1.5rem;
    border-radius: 20px;
    font-family: 'Cinzel', serif !important;
    font-size: 0.8rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.ending-heroic_death { background: rgba(139,0,0,0.3); color: #e74c3c; border: 1px solid rgba(231,76,60,0.4); }
.ending-madness      { background: rgba(26,0,51,0.3); color: #9b59b6; border: 1px solid rgba(155,89,182,0.4); }
.ending-victory      { background: rgba(0,51,26,0.3); color: #2ecc71; border: 1px solid rgba(46,204,113,0.4); }
.ending-legend       { background: rgba(51,40,0,0.3); color: #f1c40f; border: 1px solid rgba(241,196,15,0.4); }

.epilogue-text {
    font-family: 'EB Garamond', serif !important;
    font-size: 1.15rem;
    line-height: 1.9;
    color: #c0b8a8;
    text-align: left;
    max-width: 600px;
    margin: 1.5rem auto;
    padding: 1.5rem;
    border-left: 2px solid rgba(201,168,76,0.3);
}

.score-display {
    margin-top: 2rem;
}

.score-label {
    font-family: 'Cinzel', serif !important;
    font-size: 0.7rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #8a7e6b;
}

.score-value {
    font-family: 'Cinzel Decorative', serif !important;
    font-size: 3rem;
    color: #c9a84c;
    text-shadow: 0 0 20px rgba(201,168,76,0.3);
}

/* ══════════════════════════════════════════════════════════════════
   SETUP SCREEN
   ══════════════════════════════════════════════════════════════════ */
.setup-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 2rem 0;
}

.world-option {
    padding: 1rem;
    background: rgba(15,12,8,0.8);
    border: 1px solid rgba(201,168,76,0.15);
    border-radius: 4px;
    margin-bottom: 0.5rem;
    transition: all 0.3s;
}

.world-option:hover {
    border-color: rgba(201,168,76,0.5);
    background: rgba(20,16,10,0.9);
}

/* ══════════════════════════════════════════════════════════════════
   BUTTONS
   ══════════════════════════════════════════════════════════════════ */
.stButton > button {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    background: linear-gradient(135deg, rgba(201,168,76,0.2), rgba(201,168,76,0.1)) !important;
    border: 1px solid rgba(201,168,76,0.4) !important;
    color: #c9a84c !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(201,168,76,0.35), rgba(201,168,76,0.2)) !important;
    border-color: rgba(201,168,76,0.7) !important;
    box-shadow: 0 0 15px rgba(201,168,76,0.2) !important;
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Primary button (Begin Chronicle, Commit Action) */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(201,168,76,0.3), rgba(139,105,20,0.3)) !important;
    font-size: 1rem !important;
    padding: 0.6rem 2rem !important;
}

/* ══════════════════════════════════════════════════════════════════
   FORM STYLING
   ══════════════════════════════════════════════════════════════════ */
[data-testid="stForm"] {
    background: rgba(15, 12, 8, 0.6);
    border: 1px solid rgba(201,168,76,0.15);
    border-radius: 4px;
    padding: 1rem;
}

/* ══════════════════════════════════════════════════════════════════
   TABS STYLING
   ══════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid rgba(201,168,76,0.2);
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 1px;
    color: #8a7e6b !important;
    font-size: 0.85rem;
}

.stTabs [aria-selected="true"] {
    color: #c9a84c !important;
    border-bottom-color: #c9a84c !important;
}

/* ══════════════════════════════════════════════════════════════════
   METRIC CARDS
   ══════════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
    background: rgba(15,12,8,0.6);
    border: 1px solid rgba(201,168,76,0.1);
    border-radius: 4px;
    padding: 0.75rem;
}

[data-testid="stMetricLabel"] {
    font-family: 'Cinzel', serif !important;
    font-size: 0.7rem !important;
    letter-spacing: 1px;
    text-transform: uppercase;
}

[data-testid="stMetricValue"] {
    font-family: 'Cinzel Decorative', serif !important;
    color: #c9a84c !important;
}

/* ══════════════════════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d14 0%, #0a0a0f 100%);
    border-right: 1px solid rgba(201,168,76,0.15);
}

section[data-testid="stSidebar"] .stMarkdown {
    font-family: 'EB Garamond', serif !important;
}

/* ══════════════════════════════════════════════════════════════════
   EXPANDER
   ══════════════════════════════════════════════════════════════════ */
.streamlit-expanderHeader {
    font-family: 'Cinzel', serif !important;
    color: #c9a84c !important;
    font-size: 0.85rem;
    letter-spacing: 1px;
}

[data-testid="stExpander"] {
    border-color: rgba(201,168,76,0.15) !important;
}

/* ══════════════════════════════════════════════════════════════════
   INPUTS
   ══════════════════════════════════════════════════════════════════ */
.stTextInput input, .stTextArea textarea {
    font-family: 'EB Garamond', serif !important;
    background: rgba(15,12,8,0.8) !important;
    border-color: rgba(201,168,76,0.25) !important;
    color: #e8e0d0 !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(201,168,76,0.6) !important;
    box-shadow: 0 0 10px rgba(201,168,76,0.1) !important;
}

.stSelectbox [data-baseweb="select"] {
    font-family: 'EB Garamond', serif !important;
}

.stRadio label {
    font-family: 'EB Garamond', serif !important;
}

/* ══════════════════════════════════════════════════════════════════
   SPINNER
   ══════════════════════════════════════════════════════════════════ */
.stSpinner > div {
    border-top-color: #c9a84c !important;
}

/* ══════════════════════════════════════════════════════════════════
   API STATUS INDICATOR
   ══════════════════════════════════════════════════════════════════ */
.api-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Cinzel', serif !important;
    font-size: 0.7rem;
    letter-spacing: 1px;
    color: #8a7e6b;
}

.api-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.api-dot-connected {
    background: #2ecc71;
    box-shadow: 0 0 6px rgba(46,204,113,0.5);
}

.api-dot-disconnected {
    background: #e74c3c;
    box-shadow: 0 0 6px rgba(231,76,60,0.5);
}

/* ══════════════════════════════════════════════════════════════════
   TURN COUNTER
   ══════════════════════════════════════════════════════════════════ */
.turn-counter {
    font-family: 'Cinzel', serif !important;
    font-size: 0.75rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a4535;
    text-align: center;
    margin: 0.5rem 0;
}

/* ══════════════════════════════════════════════════════════════════
   AUDIO INPUT STYLING
   ══════════════════════════════════════════════════════════════════ */
[data-testid="stAudioInput"] {
    border: 1px solid rgba(201,168,76,0.2) !important;
    border-radius: 4px;
}

/* ══════════════════════════════════════════════════════════════════
   DOWNLOAD BUTTON
   ══════════════════════════════════════════════════════════════════ */
.stDownloadButton > button {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 1px;
    font-size: 0.8rem;
}

/* ══════════════════════════════════════════════════════════════════
   HIDE STREAMLIT BRANDING
   ══════════════════════════════════════════════════════════════════ */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ══════════════════════════════════════════════════════════════════
   RESPONSIVE
   ══════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
    .chronicle-title { font-size: 2rem; }
    .story-panel { font-size: 16px; padding: 1.25rem; max-height: 400px; }
    .chapter-number { font-size: 1.8rem; }
}
</style>
"""
