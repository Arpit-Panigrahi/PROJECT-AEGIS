def check_html():
    html_path = "dashboard/index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("Guided Presentation Mode button", 'Guided Presentation Mode'),
        ("Floating HUD drawer", 'id="presenterDrawer"'),
        ("Oscilloscope Canvas", 'id="oscilloCanvas"'),
        ("256-Bin Spectrum Canvas", 'id="spectrumCanvas"'),
        ("360° Radar Canvas", 'id="radarCanvas"'),
        ("Forensic Hex Modal", 'id="forensicModal"')
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
