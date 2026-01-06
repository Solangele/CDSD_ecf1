import requests
import structlog
import time
from src.storage.postgres_client import PostgresStorage

logger = structlog.get_logger()

class APIEnricher:
    def __init__(self):
        self.pg = PostgresStorage()
        self.api_url = "https://api-adresse.data.gouv.fr/search/"
        self.headers = {'User-Agent': 'DataPulse-Enricher-Student-Project/1.0'}

    def run(self):
        logger.info("starting_api_enrichment")
        
        with self.pg.conn.cursor() as cur:
            cur.execute("SELECT id, adresse, ville, code_postal FROM fact_libraries WHERE latitude IS NULL;")
            libraries = cur.fetchall()

        if not libraries:
            logger.info("no_libraries_to_enrich")
            return

        for lib_id, adresse, ville, cp in libraries:
            full_address = f"{adresse}, {cp} {ville}"
            logger.info("enriching_library", id=lib_id, address=full_address)
            
            try:
                time.sleep(0.2) 
                
                params = {'q': full_address, 'limit': 1}
                response = requests.get(
                    self.api_url, 
                    params=params, 
                    headers=self.headers, # AJOUT
                    timeout=5
                )
                
                response.raise_for_status() 
                
                data = response.json()
                if data['features']:
                    lon, lat = data['features'][0]['geometry']['coordinates']
                    self._update_library_coords(lib_id, lat, lon)
                    logger.info("enrichment_success", id=lib_id, lat=lat, lon=lon)
                else:
                    logger.warn("address_not_found", address=full_address, id=lib_id)
                
            except requests.exceptions.HTTPError as http_err:
                logger.error("api_http_error", status=response.status_code, error=str(http_err))
            except Exception as e:
                logger.error("api_call_failed", error=str(e))

    def _update_library_coords(self, lib_id, lat, lon):
        query = "UPDATE fact_libraries SET latitude = %s, longitude = %s WHERE id = %s"
        with self.pg.conn.cursor() as cur:
            cur.execute(query, (lat, lon, lib_id))

if __name__ == "__main__":
    enricher = APIEnricher()
    enricher.run()