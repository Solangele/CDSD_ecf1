import psycopg2
from psycopg2.extras import RealDictCursor
import structlog
from config.settings import postgres_config

logger = structlog.get_logger()

class PostgresStorage:
    def __init__(self):
        # Connexion à la base de données
        try:
            self.conn = psycopg2.connect(
                host=postgres_config.host,
                port=postgres_config.port,
                user=postgres_config.user,
                password=postgres_config.password,
                database=postgres_config.database
            )
            self.conn.autocommit = True
            self._ensure_tables()
            logger.info("postgres_connection_success")
        except Exception as e:
            logger.error("postgres_connection_failed", error=str(e))
            raise

    def _ensure_tables(self):
        with self.conn.cursor() as cur:
            # Table pour les produits (Webscraper + Books)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dim_products (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50),
                    title TEXT UNIQUE,
                    price_euro DECIMAL(10,2),
                    rating INTEGER,
                    category VARCHAR(100),
                    minio_image_uri TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table pour les librairies (Excel + API Adresse)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fact_libraries (
                    id SERIAL PRIMARY KEY,
                    nom_librairie VARCHAR(255),
                    adresse TEXT,
                    code_postal VARCHAR(10),
                    ville VARCHAR(100),
                    specialite VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    ca_annuel DECIMAL(15,2)
                );
            """)
            logger.info("postgres_tables_ready")

    def upsert_product(self, data):
        query = """
            INSERT INTO dim_products (source, title, price_euro, rating, category, minio_image_uri, scraped_at)
            VALUES (%(source)s, %(title)s, %(price_euro)s, %(rating)s, %(category)s, %(minio_image_uri)s, %(scraped_at)s)
            ON CONFLICT (title) DO UPDATE SET 
                price_euro = EXCLUDED.price_euro,
                rating = EXCLUDED.rating,
                scraped_at = EXCLUDED.scraped_at;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, data)
        except Exception as e:
            logger.error("postgres_upsert_failed", error=str(e))

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("postgres_connection_closed")