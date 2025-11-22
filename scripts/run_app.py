# run_app.py
import os
import subprocess
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# ===============================
# Project root equivalent to `set "PROJECT_ROOT=%CD%"`
# ===============================
PROJECT_ROOT = project_root
print("=================================")
print("   DSDE Project - Starting App   ")
print("=================================")
print()

STREAMLIT_DIR = os.path.join(PROJECT_ROOT, "streamlit")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if not os.path.exists(STREAMLIT_DIR):
    print("ERROR: 'streamlit' directory not found.")
    sys.exit(1)

# Add src to sys.path for imports
sys.path.insert(0, SRC_DIR)

# List all Python files in streamlit/
files = [f for f in os.listdir(STREAMLIT_DIR) if f.endswith(".py")]
if not files:
    print("No Python files found in 'streamlit'.")
    sys.exit(1)

while True:
    print("\nAvailable Streamlit apps in 'streamlit':")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")

    userinput = input("\nEnter number or filename to run (or 'exit' to quit): ").strip()
    if not userinput:
        continue

    if userinput.lower() == "exit":
        print("Goodbye!")
        sys.exit(0)

    chosenfile = None

    # ===== Numeric input =====
    if userinput.isdigit():
        idx = int(userinput)
        if 1 <= idx <= len(files):
            chosenfile = files[idx - 1]
        else:
            print(f"Invalid number. Enter 1-{len(files)}.")
            continue

    # ===== Keyword shortcuts =====
    if chosenfile is None:
        keywords = {
            "line": "LineChartVisualize.py",
            "mapscatter": "MapScatter.py",
            "map": "MapVisualize.py",
            "visual": "MapVisualize.py",
            "scatter": "Scatter.py",
        }
        chosenfile = keywords.get(userinput.lower(), None)

    # ===== Partial match =====
    if chosenfile is None:
        for f in files:
            if userinput.lower() in f.lower():
                chosenfile = f
                break

    if chosenfile is None:
        print("No matching file found.")
        continue

    print(f"\nRunning Streamlit app: {chosenfile}")
    print("(Press Ctrl+C to stop and return to menu.)\n")

    # ===== Run Streamlit =====
    venv_streamlit = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "streamlit.exe")
    venv_python = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")

    try:
        if os.path.exists(venv_streamlit):
            result = subprocess.run(
                [
                    venv_streamlit,
                    "run",
                    os.path.join(STREAMLIT_DIR, chosenfile),
                    "--server.port=8501",
                ]
            )
        elif os.path.exists(venv_python):
            result = subprocess.run(
                [
                    venv_python,
                    "-m",
                    "streamlit",
                    "run",
                    os.path.join(STREAMLIT_DIR, chosenfile),
                    "--server.port=8501",
                ]
            )
        else:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    os.path.join(STREAMLIT_DIR, chosenfile),
                    "--server.port=8501",
                ]
            )

        print("\nStreamlit app stopped.")

    except KeyboardInterrupt:
        print("\nStreamlit app interrupted by user.")
    except Exception as e:
        print(f"\nError running Streamlit app: {e}")

    input("\nPress Enter to return to menu...")
