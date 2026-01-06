import pandas as pd
from sqlalchemy import create_engine
import structlog
from config.settings import postgres_config

logger = structlog.get_logger()

class ExcelLoader:
    def __init__(self):
        self.file_path = "data/partenaire_librairies.xlsx"
        self.engine = create_engine(postgres_config.connection_uri, isolation_level="AUTOCOMMIT")

    def load_and_clean(self):
        logger.info("starting_excel_import", file=self.file_path)
        
        try:
            df = pd.read_excel(self.file_path)

            required_cols = ['nom_librairie', 'adresse', 'code_postal', 'ville']
            missing_cols = [c for c in required_cols if c not in df.columns]
            
            if missing_cols:
                logger.error("invalid_format", missing=missing_cols)
                raise ValueError(f"Colonnes manquantes dans l'Excel : {missing_cols}")

            cols_to_remove = ['contact_nom', 'contact_email', 'contact_telephone']
  
            existing_cols_to_remove = [c for c in cols_to_remove if c in df.columns]
            
            logger.info("applying_rgpd_measures", removed_columns=existing_cols_to_remove)
            df_cleaned = df.drop(columns=existing_cols_to_remove)

            df_cleaned['code_postal'] = df_cleaned['code_postal'].astype(str).str.zfill(5)

            df_cleaned.to_sql(
                name='fact_libraries', 
                con=self.engine, 
                if_exists='replace', 
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