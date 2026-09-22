def check_html():
    html_path = "dashboard/index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("Threat Simulation Deck", 'id="section-hero"'),
        ("Telemetry Metrics Grid", 'class="metrics-grid"'),
        ("Defense Pipeline Strip", 'class="pipeline-card"'),
        ("Oscilloscope Canvas", 'id="oscilloCanvas"'),
        ("256-Bin Spectrum Canvas", 'id="spectrumCanvas"'),
        ("Canary Radar Canvas", 'id="radarCanvas"'),
        ("Process State Machine", 'id="currentTierBadge"'),
        ("Live Telemetry Stream", 'id="telemetryTable"'),
        ("Forensic Hex Modal", 'id="forensicModal"'),
        ("Benchmark & Architecture Tabs", 'id="tab-benchmark"')
    ]

    print("=== Checking index.html UI Requirements ===")
    all_pass = True
    for label, target in checks:
        if target in content:
            print(f"[PASS] {label} (Found '{target}')")
        else:
            print(f"[FAIL] {label} (Target '{target}' not found)")
            all_pass = False

    return all_pass

if __name__ == "__main__":
    if check_html():
        print("\n[+] All index.html UI components verified successfully!")
        exit(0)
    else:
        print("\n[-] UI verification failed!")
        exit(1)
