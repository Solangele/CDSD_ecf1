import structlog
from src.scrapers.quotes_scraper import QuotesScraper
from src.scrapers.ecom_scraper import EcommerceScraper
from src.processors.excel_loader import ExcelLoader
from src.processors.api_enricher import APIEnricher

logger = structlog.get_logger()

class DataPipeline:
    def __init__(self):
        self.excel_loader = ExcelLoader()
        self.api_enricher = APIEnricher()
        self.quotes_scraper = QuotesScraper()
        self.ecom_scraper = EcommerceScraper()

    def run(self):
        logger.info("global_pipeline_started")

        # Étape 1 : Excel
        logger.info("step_1_excel_import")
        self.excel_loader.load_and_clean()

        # Étape 2 : API Enrichment (juste après l'Excel)
        logger.info("step_2_api_enrichment")
        self.api_enricher.run()

        # Étape 3 : Scraping Quotes (MongoDB)
        logger.info("step_3_quotes_scraping")
        self.quotes_scraper.run()

        # Étape 4 : Scraping E-commerce (Multi-sources)
        logger.info("step_4_ecommerce_scraping")
        self.ecom_scraper.run()

        logger.info("global_pipeline_finished")

data_pipeline = DataPipeline()