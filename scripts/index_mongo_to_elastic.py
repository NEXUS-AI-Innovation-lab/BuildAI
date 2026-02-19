import sys
from pathlib import Path
import time

# Ensure server package is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))

from config_loader import settings
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers


def ensure_index(es: Elasticsearch, index_name: str):
    if not es.indices.exists(index=index_name):
        mapping = {
            'mappings': {
                'properties': {
                    import sys
                    from pathlib import Path
                    import time
                    import logging

                    # Ensure server package is importable
                    ROOT = Path(__file__).resolve().parents[1]
                    sys.path.insert(0, str(ROOT / 'server'))

                    from config_loader import settings
                    from pymongo import MongoClient
                    from pymongo.errors import ServerSelectionTimeoutError
                    from elasticsearch import Elasticsearch, helpers
                    from elasticsearch.exceptions import ElasticsearchException


                    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
                    logger = logging.getLogger(__name__)


                    def ensure_index(es: Elasticsearch, index_name: str):
                        try:
                            if not es.indices.exists(index=index_name):
                                mapping = {
                                    'mappings': {
                                        'properties': {
                                            'doc_id': {'type': 'keyword'},
                                            'text': {'type': 'text'},
                                            'metadata': {'type': 'object', 'enabled': False}
                                        }
                                    }
                                }
                                es.indices.create(index=index_name, body=mapping)
                                logger.info("Created Elasticsearch index '%s'", index_name)
                            else:
                                logger.info("Elasticsearch index '%s' already exists, skipping creation", index_name)
                        except ElasticsearchException as e:
                            logger.error("Error creating index '%s': %s", index_name, e)
                            raise


                    def main():
                        mongo_uri = getattr(settings, 'MONGO_URI', f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}/LibreChat")
                        es_url = getattr(settings, 'ELASTICSEARCH_URL', 'http://localhost:9200')
                        index_name = getattr(settings, 'ELASTICSEARCH_INDEX', 'btp_bm25_v2_index')

                        try:
                            mongo = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                            # Test connection
                            mongo.server_info()
                            logger.info("Connected to MongoDB")
                        except ServerSelectionTimeoutError as e:
                            logger.error("Cannot connect to MongoDB: %s", e)
                            return

                        try:
                            es = Elasticsearch(es_url, timeout=30)
                            if not es.ping():
                                logger.error("Elasticsearch cluster is not reachable")
                                return
                            logger.info("Connected to Elasticsearch cluster")
                        except ElasticsearchException as e:
                            logger.error("Cannot connect to Elasticsearch: %s", e)
                            return

                        try:
                            db_name = mongo_uri.split('/')[-1].split('?')[0]
                            db = mongo[db_name]
                            coll = db['raw_data']

                            ensure_index(es, index_name)

                            total_new = 0
                            batch_size = 500
                            actions = []

                            cursor = coll.find({})
                            logger.info("Found documents cursor from MongoDB, iterating...")

                            for doc in cursor:
                                doc_id = doc.get('doc_id') or str(doc.get('_id'))

                                # Skip if already present in ES
                                try:
                                    if es.exists(index=index_name, id=doc_id):
                                        continue
                                except Exception:
                                    # On error checking existence, continue and let bulk index handle duplicates
                                    pass

                                text = doc.get('content', '')
                                # Truncate very large texts to avoid huge payloads
                                max_text = 200_000
                                if isinstance(text, str) and len(text) > max_text:
                                    text = text[:max_text]

                                body = {
                                    'doc_id': doc_id,
                                    'text': text,
                                    'metadata': doc.get('metadata', {})
                                }

                                actions.append({
                                    '_op_type': 'index',
                                    '_index': index_name,
                                    '_id': doc_id,
                                    '_source': body
                                })

                                if len(actions) >= batch_size:
                                    try:
                                        success, errors = helpers.bulk(es, actions, stats_only=False)
                                        total_new += success
                                        if errors:
                                            logger.warning('Bulk indexing returned errors: %s', errors)
                                        logger.info('Indexed %d new documents so far', total_new)
                                    except ElasticsearchException as e:
                                        logger.error('Error indexing batch: %s', e)
                                    actions = []
                                    time.sleep(0.05)

                            # Final batch
                            if actions:
                                try:
                                    success, errors = helpers.bulk(es, actions, stats_only=False)
                                    total_new += success
                                    if errors:
                                        logger.warning('Bulk indexing returned errors: %s', errors)
                                except ElasticsearchException as e:
                                    logger.error('Error indexing final batch: %s', e)

                            logger.info("Indexing finished: %d new documents indexed into '%s'", total_new, index_name)

                        finally:
                            try:
                                mongo.close()
                                logger.info('MongoDB connection closed')
                            except Exception:
                                pass


                    if __name__ == '__main__':
                        start = time.time()
                        logger.info('Starting MongoDB → Elasticsearch indexing script')
                        main()
                        logger.info('Script finished in %.2f seconds', time.time() - start)
