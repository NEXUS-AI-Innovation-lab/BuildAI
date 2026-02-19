import sys
from pathlib import Path
import json
import time
from datetime import datetime

# Ensure server package is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))

from app.services.raw_data_service import RawDataService


RAW_DIR = ROOT / 'storage' / 'raw_data'


def process_file(p: Path):
    metadata = {
        'filename': p.name,
        'file_type': p.suffix.lower().lstrip('.'),
        'file_size': p.stat().st_size,
        'modified_at': datetime.utcfromtimestamp(p.stat().st_mtime).isoformat() + 'Z'
    }

    content = ''
    try:
        if p.suffix.lower() == '.txt':
            content = p.read_text(encoding='utf-8', errors='ignore')
        elif p.suffix.lower() in ('.html', '.htm'):
            content = p.read_text(encoding='utf-8', errors='ignore')
        else:
            # For binaries (pdf, jpg...) we keep empty content and store metadata
            content = ''
    except Exception:
        content = ''

    doc_id = p.stem
    title = p.stem

    ok = RawDataService.save_document(doc_id=doc_id, content=content, title=title, source=None, metadata=metadata)
    return ok


def main():
    if not RAW_DIR.exists():
        print(f"No raw data directory found at {RAW_DIR}")
        return

    files = sorted(RAW_DIR.iterdir())
    total = len(files)
    print(f"Found {total} files in {RAW_DIR}")

    success = 0
    for i, f in enumerate(files, 1):
        try:
            ok = process_file(f)
            if ok:
                success += 1
                print(f"[{i}/{total}] ingested: {f.name}")
            else:
                print(f"[{i}/{total}] failed: {f.name}")
        except Exception as e:
            print(f"[{i}/{total}] error: {f.name} -> {e}")
        time.sleep(0.02)

    print(f"Ingestion finished: {success}/{total} documents saved to MongoDB")


if __name__ == '__main__':
    main()
