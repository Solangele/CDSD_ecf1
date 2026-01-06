import pandas as pd
from sqlalchemy import create_engine
import structlog
from config.settings import postgres_config

logger = structlog.get_logger()

class ExcelLoader:
    def __init__(self):
        self.engine = create_engine(postgres_config.connection_uri)
        self.file_path = "data/partenaire_librairies.xlsx"
        self.engine = create_engine(postgres_config.connection_uri,isolation_level="AUTOCOMMIT")

    def load_and_clean(self):
        logger.info("starting_excel_import", file=self.file_path)
        
        try:
            df = pd.read_excel(self.file_path)
            print(df.head())
            
            cols_to_remove = ['contact_nom', 'contact_email', 'contact_telephone']
            
            logger.info("applying_rgpd_measures", removed_columns=cols_to_remove)
            df_cleaned = df.drop(columns=cols_to_remove)
            

            df_cleaned['code_postal'] = df_cleaned['code_postal'].astype(str).str.zfill(5)
            
            df_cleaned.to_sql(
                name='fact_libraries', 
                con=self.engine, 
                if_exists='append', 
                index=False
            )
            
            logger.info("excel_import_success", rows=len(df_cleaned))
            return df_cleaned
            
        except Exception as e:
            logger.error("excel_import_failed", error=str(e))
            return None

if __name__ == "__main__":
    loader = ExcelLoader()
    loader.load_and_clean()