import structlog
from src.scrapers.quotes_scraper import QuotesScraper
from src.scrapers.ecom_scraper import EcommerceScraper
from src.processors.excel_loader import ExcelLoader

logger = structlog.get_logger()

def run_pipeline():
    logger.info("global_pipeline_started")
    
    logger.info("step_1_excel_import_starting")
    loader = ExcelLoader()
    loader.load_and_clean()
    
    logger.info("step_2_quotes_starting")
    quotes = QuotesScraper()
    quotes.run()
    
    logger.info("step_3_ecommerce_starting")
    ecom = EcommerceScraper()
    ecom.run()
    
    logger.info("global_pipeline_finished")

if __name__ == "__main__":
    run_pipeline()