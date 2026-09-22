import re
import sys
from bs4 import BeautifulSoup

html_content = open("dashboard/index.html", "r", encoding="utf-8").read()
soup = BeautifulSoup(html_content, "html.parser")

# Extract JS code
script_match = re.search(r"<script>([\s\S]*?)</script>", html_content)
if not script_match:
    print("[FAIL] No <script> tag found!")
    sys.exit(1)

js = script_match.group(1)

print("=== CHECK 1: Verifying All Operational Function Handlers in JavaScript ===")
required_functions = [
    "toggleMode",
    "toggleAgent",
    "triggerAction",
    "switchTab",
    "closeModal",
    "loadForensicSample",
    "openForensicModal",
    "addTelemetryRow",
    "checkStatus",
    "initSSE",
    "drawOscilloscope",
    "drawSpectrum",
    "drawRadar"
]

all_funcs_ok = True
for func in required_functions:
    pattern = rf"function\s+{func}\s*\("
    if re.search(pattern, js):
        print(f"[PASS] Function '{func}' is defined in JavaScript")
    else:
        print(f"[FAIL] Function '{func}' is MISSING in JavaScript!")
        all_funcs_ok = False

print("\n=== CHECK 2: Verifying Target Sections for All Navigation Links ===")
links = soup.find_all("a", href=True)
all_links_ok = True
for a in links:
    href = a["href"]
    if href.startswith("#") and len(href) > 1:
        target_id = href[1:]
        target_element = soup.find(id=target_id)
        if target_element:
            print(f"[PASS] Link '{href}' points to valid element <{target_element.name} id='{target_id}'>")
        else:
            print(f"[FAIL] Link '{href}' points to MISSING id='{target_id}'!")
            all_links_ok = False

print("\n=== CHECK 3: Verifying Tab IDs for Tab Switching Buttons ===")
tab_buttons = [
    ("benchmark", "tab-benchmark"),
    ("executive", "tab-executive"),
    ("technical", "tab-technical"),
    ("explainer", "tab-explainer")
]
all_tabs_ok = True
for tab_arg, tab_panel_id in tab_buttons:
    panel = soup.find(id=tab_panel_id)
    btn = soup.find(id=f"tabBtn-{tab_arg}")
    if panel and btn:
        print(f"[PASS] Tab '{tab_arg}' -> Button '#tabBtn-{tab_arg}' & Panel '#{tab_panel_id}' both exist")
    else:
        print(f"[FAIL] Tab '{tab_arg}' panel or button missing! (Panel: {bool(panel)}, Btn: {bool(btn)})")
        all_tabs_ok = False

print("\n=== CHECK 4: Verifying Modal Elements and Controls ===")
modal = soup.find(id="forensicModal")
modal_elements = ["modalInode", "modalEntropy", "modalComm", "modalHexDump", "btnSampleCipher", "btnSamplePlain"]
all_modal_ok = True
if modal:
    print("[PASS] Modal '#forensicModal' exists in DOM")
    for el_id in modal_elements:
        if soup.find(id=el_id):
            print(f"[PASS] Modal child '#{el_id}' exists")
        else:
            print(f"[FAIL] Modal child '#{el_id}' MISSING!")
            all_modal_ok = False
else:
    print("[FAIL] Modal '#forensicModal' MISSING!")
    all_modal_ok = False

print("\n=== CHECK 5: Verifying Tactical Threat Simulation Buttons & Header Controls ===")
sim_actions = [
    "simulate_encryptor",
    "simulate_canary",
    "simulate_entropy",
    "simulate_benign",
    "clear_logs"
]
all_sims_ok = True
for act in sim_actions:
    btn = soup.find("button", onclick=re.compile(rf"triggerAction\(['\"]{act}['\"]\s*\)"))
    if btn:
        print(f"[PASS] Simulation button for action '{act}' exists in DOM")
    else:
        print(f"[FAIL] Simulation button for action '{act}' MISSING!")
        all_sims_ok = False

header_controls = ["modeBtn", "agentToggleBtn", "statusBadge"]
for ctrl in header_controls:
    el = soup.find(id=ctrl)
    if el:
        print(f"[PASS] Header control '#{ctrl}' exists in DOM")
    else:
        print(f"[FAIL] Header control '#{ctrl}' MISSING!")
        all_sims_ok = False

print("\n=== SUMMARY ===")
if all_funcs_ok and all_links_ok and all_tabs_ok and all_modal_ok and all_sims_ok:
    print("[SUCCESS] ALL BUTTONS, HANDLERS, LINKS, AND DOM TARGETS ARE 100% VALIDATED!")
    sys.exit(0)
else:
    print("[ERROR] SOME BUTTONS OR TARGETS FAILED VALIDATION!")
    sys.exit(1)
