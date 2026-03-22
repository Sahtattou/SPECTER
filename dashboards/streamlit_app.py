import sys
from pathlib import Path


dashboard_dir = Path(__file__).resolve().parent
dashboard_dir_str = str(dashboard_dir)
if dashboard_dir_str not in sys.path:
    sys.path.insert(0, dashboard_dir_str)

from app import run_dashboard


if __name__ == "__main__":
    run_dashboard()
