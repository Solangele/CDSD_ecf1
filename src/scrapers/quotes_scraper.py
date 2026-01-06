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
        self.headers = {
            'User-Agent': 'DataPulse-Scraper-Project/1.0 (Student Project; educational use)'
        }

    def run(self):
        current_url = self.site_cfg.base_url
        saved_count = 0
        
        logger.info("starting_quotes_scraper", url=current_url)

        while current_url:
            try:
                time.sleep(1) 
                
                response = requests.get(current_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                quote_elements = soup.find_all("div", class_="quote")
                
                for elem in quote_elements:
                    data = {
                        "text": elem.find("span", class_="text").text.strip(),
                        "author": elem.find("small", class_="author").text.strip(),
                        "tags": [tag.text for tag in elem.find_all("a", class_="tag")],
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    if self.mongo.save_item("quotes", data):
                        saved_count += 1

                next_button = soup.find("li", class_="next")
                if next_button:
                    relative_url = next_button.find("a")["href"]
                    current_url = "https://quotes.toscrape.com" + relative_url
                    logger.info("moving_to_next_page", next_url=current_url)
                else:
                    current_url = None 

            except Exception as e:
                logger.error("quotes_scraper_page_failed", url=current_url, error=str(e))
                break

        self.mongo.log_run("quotes_scraper", saved_count)
        logger.info("quotes_scraper_finished", total=saved_count)

if __name__ == "__main__":
    scraper = QuotesScraper()
    scraper.run()