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
            self.conn.autocommit = False
            self._ensure_tables()
            logger.info("postgres_connection_success")
        except Exception as e:
            logger.error("postgres_connection_failed", error=str(e))
            raise

    def _ensure_tables(self):
        with self.conn.cursor() as cur:
            # Table Produits (inchangée)
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
        self.conn.commit()
            # ON CHANGE LE NOM : fact_libraries_enriched
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fact_libraries_enriched (
                    id SERIAL PRIMARY KEY,
                    nom_librairie TEXT,
                    adresse TEXT,
                    code_postal TEXT,
                    ville TEXT,
                    ca_annuel FLOAT,
                    date_partenariat DATE,
                    specialite TEXT
                );

                CREATE TABLE IF NOT EXISTS dim_geoloc (
                    id SERIAL PRIMARY KEY,
                    library_id INTEGER UNIQUE NOT NULL, -- Plus de REFERENCES ici pour éviter le bug
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION
                );
            """)
        self.conn.commit()


    def save_geoloc(self, lib_id, lat, lon):
        query = """
            INSERT INTO dim_geoloc (library_id, latitude, longitude)
            VALUES (%s, %s, %s)
            ON CONFLICT (library_id) DO UPDATE 
            SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (lib_id, lat, lon))
        self.conn.commit()
    
    def get_libraries_to_enrich(self):
        """Retourne les libs qui n'ont pas encore de géoloc dans dim_geoloc"""
        query = """
            SELECT l.id, l.adresse, l.ville, l.code_postal 
            FROM fact_libraries_enriched l
            LEFT JOIN dim_geoloc g ON l.id = g.library_id
            WHERE g.id IS NULL;
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

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
            self.conn.commit() 
        except Exception as e:
            logger.error("postgres_upsert_failed", error=str(e))
            self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("postgres_connection_closed")