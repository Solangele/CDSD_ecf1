import re
import time
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import structlog

from src.storage.mongo_client import MongoDBStorage
from src.storage.minio_client import MinIOStorage
from src.storage.postgres_client import PostgresStorage
from config.settings import scraper_config, minio_config

logger = structlog.get_logger()

class EcommerceScraper:
    def __init__(self):
        site_cfg = scraper_config.sites["webscraper"]
        self.base_url = site_cfg.base_url
        self.delay = max(1.0, site_cfg.delay) 
        self.headers = {
            'User-Agent': 'DataPulse-Ecom-Bot/1.0 (ECF Student Project)'
        }
        
        self.mongo = MongoDBStorage()
        self.minio = MinIOStorage()
        self.pg = PostgresStorage()

    def run(self):
        logger.info("starting_ecommerce_scraping")
        
        target_urls = [
            ("Computers", "Laptops", f"{self.base_url}/test-sites/e-commerce/allinone/computers/laptops"),
            ("Phones", "Touch", f"{self.base_url}/test-sites/e-commerce/allinone/phones/touch")
        ]
        
        total_saved = 0
        for cat, subcat, url in target_urls:
            total_saved += self.scrape_category(url, cat, subcat)

        self.mongo.log_run("ecommerce_scraper", total_saved)
        logger.info("ecommerce_scraping_finished", total=total_saved)

    def scrape_category(self, url, category, subcategory):
        current_url = url
        saved_count = 0
        
        while current_url:
            try:
                time.sleep(self.delay)                
                response = requests.get(current_url, headers=self.headers, timeout=10)
                response.raise_for_status() 
            
                soup = BeautifulSoup(response.text, "lxml")
                products_elements = soup.find_all("div", class_="thumbnail")
                
                for elem in products_elements:
                    product_data = self._parse_product(elem, category, subcategory)
                    
                    if product_data:
                        # self._handle_image(product_data)
                        self.mongo.save_item("products", product_data)
                        
                        sql_data = {
                            "source": "WebScraper IO",
                            "title": product_data["title"],
                            "price_euro": product_data["price"],
                            "rating": product_data["rating"],
                            "category": product_data["category"],
                            "minio_image_uri": product_data.get("minio_uri"),
                            "scraped_at": datetime.now()
                        }
                        self.pg.upsert_product(sql_data)
                        saved_count += 1

                next_page = soup.find("a", {"rel": "next"}) or soup.select_one(".pagination .active + li a")
                if next_page and next_page.get("href"):
                    current_url = urljoin(self.base_url, next_page["href"])
                    logger.info("next_page_found", url=current_url)
                else:
                    current_url = None

            except Exception as e:
                logger.error("category_page_failed", url=current_url, error=str(e))
                break
                
        return saved_count

    def _parse_product(self, elem, category, subcategory):
        try:
            title_elem = elem.find("a", class_="title")
            data = {
                "title": title_elem.get("title") or title_elem.text.strip(),
                "price": float(re.search(r"[\d.]+", elem.find("h4", class_="price").text).group()),
                "description": elem.find("p", class_="description").text.strip(),
                "rating": len(elem.find("div", class_="ratings").find_all("span", class_="ws-icon-star")),
                "category": category,
                "subcategory": subcategory,
                "image_url": urljoin(self.base_url, elem.find("img")["src"]),
                "scraped_at": datetime.now().isoformat()
            }
            return data
        except Exception:
            return None

    def _handle_image(self, product_data):
        try:
            img_res = requests.get(product_data["image_url"])
            if img_res.status_code == 200:
                filename = product_data["title"].replace(" ", "_").lower()[:20] + ".jpg"
                
                minio_uri = self.minio.upload_file(
                    bucket_name=minio_config.bucket_images,
                    object_name=filename,
                    data=img_res.content,
                    content_type="image/jpeg"
                )
                product_data["minio_uri"] = minio_uri
        except Exception as e:
            logger.error("image_storage_failed", error=str(e))

if __name__ == "__main__":
    scraper = EcommerceScraper()
    scraper.run()