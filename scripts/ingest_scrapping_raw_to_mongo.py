#!/usr/bin/env python3
"""Ingest files from scrapping/raw_data into MongoDB (LibreChat.raw_data).

Usage:
  python scripts/ingest_scrapping_raw_to_mongo.py [--raw-dir PATH] [--mongo-uri URI] [--apply]

By default the script runs in dry-run mode and will only report which files would be inserted.
Pass `--apply` to perform writes to MongoDB.
"""

import argparse
import hashlib
import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient

MAX_CONTENT_BYTES = 5_000_000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def compute_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_file_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def connect_mongo(uri: str):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client.get_default_database()
        if db is None:
            db = client['LibreChat']
        coll = db['raw_data']
        coll.create_index('metadata.content_hash', unique=True, sparse=True)
        logger.info('✓ Connected to MongoDB')
        return client, coll
    except Exception as e:
        logger.warning(f'⚠ Could not connect to MongoDB: {e}')
        return None, None


def build_doc(path: Path, content_hash: str) -> dict:
    filename = path.name
    file_size = path.stat().st_size
    file_type = get_file_type(filename)

    if file_type.startswith('text/') or filename.lower().endswith('.txt'):
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')[:MAX_CONTENT_BYTES]
        except Exception:
            content = ''
    else:
        content = f'[Binary file: {filename} ({file_type})]'

    now = datetime.utcnow()
    doc = {
        'doc_id': filename,
        'filename': filename,
        'file_type': file_type,
        'file_size': file_size,
        'content': (content or '')[:MAX_CONTENT_BYTES],
        'metadata': {
            'source': 'scrapping/raw_data',
            'migrated_from': str(path),
            'content_hash': content_hash,
            'migrated_at': now.isoformat(),
        },
        'created_at': now,
        'updated_at': now,
    }
    return doc


def main():
    parser = argparse.ArgumentParser()
    default_raw = str(Path(__file__).resolve().parent / 'raw_data')
    parser.add_argument('--raw-dir', default=os.environ.get('RAW_DATA_PATH', default_raw))
    parser.add_argument('--mongo-uri', default=os.environ.get('MONGO_URI', 'mongodb://127.0.0.1:27017/LibreChat'))
    parser.add_argument('--apply', action='store_true', help='Perform writes to MongoDB (default: dry-run)')
    parser.add_argument('--limit', type=int, default=0, help='Limit files processed (0 = no limit)')
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists() or not raw_dir.is_dir():
        logger.error(f'Raw data directory not found: {raw_dir}')
        raise SystemExit(1)

    client = None
    coll = None
    if args.apply:
        client, coll = connect_mongo(args.mongo_uri)
        if coll is None:
            logger.error('MongoDB required for --apply but connection failed. Aborting.')
            raise SystemExit(2)

    files = [p for p in sorted(raw_dir.iterdir()) if p.is_file()]
    if args.limit:
        files = files[: args.limit]

    total = len(files)
    if total == 0:
        logger.warning('No files to process')
        return

    logger.info(f'Starting ingestion (dry-run={not args.apply}) - {total} files found in {raw_dir}')
    inserted = 0
    skipped = 0
    failed = 0

    for idx, path in enumerate(files, 1):
        try:
            content_hash = compute_hash(path)
            filename = path.name
            if coll is not None and coll.find_one({'metadata.content_hash': content_hash}):
                logger.info(f'[{idx}/{total}] ↺ Skip duplicate: {path.name}')
                skipped += 1
                continue

            doc = build_doc(path, content_hash)

            if args.apply:
                # If a document with same content_hash exists, skip.
                existing_by_hash = coll.find_one({'metadata.content_hash': content_hash}) if coll is not None else None
                if existing_by_hash:
                    logger.info(f'[{idx}/{total}] ↺ Skip duplicate by hash: {path.name}')
                    skipped += 1
                else:
                    # Upsert by doc_id to avoid duplicate-key errors from older records missing content_hash.
                    coll.replace_one({'doc_id': filename}, doc, upsert=True)
                    inserted += 1
                    logger.info(f'[{idx}/{total}] ✓ Inserted: {path.name}')
            else:
                logger.info(f'[{idx}/{total}] Would insert: {path.name} (hash={content_hash[:10]})')
        except Exception as e:
            failed += 1
            logger.error(f'[{idx}/{total}] ✗ Error processing {path.name}: {e}')

    logger.info('Ingestion summary:')
    logger.info(f'  Total files: {total}')
    logger.info(f'  Inserted: {inserted}')
    logger.info(f'  Skipped (duplicates): {skipped}')
    logger.info(f'  Failed: {failed}')

    if client:
        client.close()


if __name__ == '__main__':
    main()
