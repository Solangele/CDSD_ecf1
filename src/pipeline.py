import structlog
from src.scrapers.quotes_scraper import QuotesScraper
from src.scrapers.ecom_scraper import EcommerceScraper 
from src.processors.excel_loader import ExcelLoader
from src.processors.api_enricher import APIEnricher

logger = structlog.get_logger()

class DataPipeline:
    def __init__(self):
        # On ne les instancie que si nécessaire pour économiser les ressources
        pass

    def run_excel(self):
        logger.info("step_1_excel_import")
        ExcelLoader().load_and_clean()

    def run_api(self):
        logger.info("step_2_api_enrichment")
        APIEnricher().run()

    def run_scraping(self):
        logger.info("step_scraping_all")
        QuotesScraper().run()
        EcommerceScraper().run()

    def run_all(self):
        logger.info("global_pipeline_started")
        self.run_excel()
        self.run_api()
        self.run_scraping()
        logger.info("global_pipeline_finished")

data_pipeline = DataPipeline()