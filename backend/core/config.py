from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent.parent

DATA_DIR = ROOT_DIR / "data"
PUBLIC_DIR = ROOT_DIR / "public"
BACKEND_DIR = ROOT_DIR / "backend"

APP_TITLE = "Field Data Collector API"
APP_VERSION = "1.0.1" 

DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "spots").mkdir(exist_ok=True)
(DATA_DIR / "routes").mkdir(exist_ok=True)
(DATA_DIR / "sites").mkdir(exist_ok=True)
(DATA_DIR / "uploads").mkdir(exist_ok=True)
(DATA_DIR / "media").mkdir(exist_ok=True)
(DATA_DIR / "processing").mkdir(exist_ok=True)