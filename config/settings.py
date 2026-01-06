import os
from pathlib import Path 
from dataclasses import dataclass, field
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


@dataclass
class MinIOConfig:
    endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key: str = os.getenv("MINIO_ACCESS_KEY")
    secret_key: str = os.getenv("MINIO_SECRET_KEY")
    secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    bucket_images: str = "product-images"
    bucket_exports: str = "data-exports"
    bucket_backups: str = "backups"


@dataclass
class MongoDBConfig:
    host: str = os.getenv("MONGO_HOST", "localhost")
    port: int = int(os.getenv("MONGO_PORT", "27017"))
    username: str = os.getenv("MONGO_USER")
    password: str = os.getenv("MONGO_PASSWORD")
    database: str = os.getenv("MONGO_DB", "ecommerce_db")
    
    @property
    def connection_string(self) -> str:
        return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"


@dataclass
class SiteConfig:
    name: str
    base_url: str
    delay: float = 0.1
    max_pages: int = 10

@dataclass
class ScraperConfig:
    timeout: int = 30
    max_retries: int = 3
    sites: dict[str, SiteConfig] = field(default_factory=dict)

    def __post_init__(self):
        self.sites = {
            "webscraper": SiteConfig(
                name="WebScraper IO",
                base_url="https://webscraper.io/test-sites/e-commerce/allinone"
            ),
            "autre_site": SiteConfig(
                name="Partenaire Librairie",
                base_url="https://quotes.toscrape.com"
            )
        }

@dataclass
class PostgresConfig:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER")
    password: str = os.getenv("POSTGRES_PASSWORD")
    database: str = os.getenv("POSTGRES_DB", "datapulse_db")

    @property
    def connection_uri(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


postgres_config = PostgresConfig()
minio_config = MinIOConfig()
mongo_config = MongoDBConfig()
scraper_config = ScraperConfig()



if __name__ == "__main__":
    print("=== Configuration MinIO ===")
    print(f"Endpoint: {minio_config.endpoint}")
    print(f"Buckets: {minio_config.bucket_images}, {minio_config.bucket_exports}")
    
    print("\n=== Configuration MongoDB ===")
    print(f"Host: {mongo_config.host}:{mongo_config.port}")
    print(f"Database: {mongo_config.database}")
    
    print("\n=== Configuration Scraper ===")
    print(f"Timeout global: {scraper_config.timeout}s")
    for key, site in scraper_config.sites.items():
        print(f"Site [{key}]: {site.name} -> {site.base_url} (Délai: {site.delay}s)")