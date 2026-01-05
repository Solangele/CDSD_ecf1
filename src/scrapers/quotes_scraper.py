import requests
from bs4 import BeautifulSoup
import time
import structlog


from src.storage.mongo_client import MongoDBStorage
from config.settings import scraper_config

logger = structlog.get_logger()

class QuotesScraper:
    def __init__(self):

        self.site_cfg = scraper_config.sites["autre_site"]
        self.mongo = MongoDBStorage()

    def run(self):
        logger.info("starting_quotes_scraper", url=self.site_cfg.base_url)
        
        try:
            # 1. Requête HTTP
            response = requests.get(self.site_cfg.base_url, timeout=10)
            response.raise_for_status()
            
            # 2. Analyse du HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Sur ce site, chaque citation est dans une div avec la classe 'quote'
            quote_elements = soup.find_all("div", class_="quote")
            
            saved_count = 0
            for elem in quote_elements:
                # Extraction des données précises
                data = {
                    "text": elem.find("span", class_="text").text.strip(),
                    "author": elem.find("small", class_="author").text.strip(),
                    "tags": [tag.text for tag in elem.find_all("a", class_="tag")]
                }

                if self.mongo.save_item("quotes", data):
                    saved_count += 1
                
                time.sleep(self.site_cfg.delay)

            self.mongo.log_run("quotes_scraper", saved_count)
            logger.info("quotes_scraper_finished", total=saved_count)
            
        except Exception as e:
            logger.error("quotes_scraper_failed", error=str(e))

if __name__ == "__main__":
    scraper = QuotesScraper()
    scraper.run()