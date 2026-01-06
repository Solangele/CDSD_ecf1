import argparse
from src.pipeline import data_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DataPulse Pipeline Orchestrator")
    parser.add_argument(
        '--step', 
        choices=['excel', 'api', 'scraping', 'all'], 
        default='all',
        help="Choisir l'étape à exécuter (default: all)"
    )

    args = parser.parse_args()

    if args.step == 'excel':
        data_pipeline.run_excel()
    elif args.step == 'api':
        data_pipeline.run_api()
    elif args.step == 'scraping':
        data_pipeline.run_scraping()
    else:
        data_pipeline.run_all()