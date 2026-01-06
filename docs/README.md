# ECF1

## Projet demandé 
Vous êtes recruté(e) comme **Data Engineer** chez **DataPulse Analytics**, une startup spécialisée dans l'agrégation et l'analyse de données multi-sources.

Le directeur technique vous confie la mission suivante :

> *"Nous avons besoin d'une plateforme capable de collecter des données depuis plusieurs sources hétérogènes : sites web, APIs, fichiers partenaires. Ces données doivent être stockées, nettoyées et rendues disponibles pour nos analystes. Je compte sur vous pour proposer une architecture adaptée et l'implémenter."*

## Prérequis
### Environnement techniques

- Docker et docker compose
- Python 3.14
- Vscode 
- Connexion internet

### Connaissances requises

- Bases de python
- Notion HTML et HTTP
- Docker
- MongoDB
- SQL
- Minio

# Partie 1 : Mise en place de l'infrastructure
## Arborescence du projet
```
│   .env
│   .gitignore
│   docker-compose.yml
│   main.py
│   requirements.txt
│
├───config
│   │   settings.py
│   │   __init__.py
│   │
│   └───__pycache__
│           settings.cpython-314.pyc
│           __init__.cpython-314.pyc
│
├───data
│       partenaire_librairies.xlsx
│
├───docs
│       ECF-DataPulse-MultiSources.md
│       README.md
│       RGPD_conformite.md
│
├───sql
│       analyses.sql
│
├───src
│   │   pipeline.py
│   │   __init__.py
│   │
│   ├───processors
│   │   │   api_enricher.py
│   │   │   excel_loader.py
│   │   │
│   │   └───__pycache__
│   │           api.cpython-314.pyc
│   │           api_enricher.cpython-314.pyc
│   │           excel_loader.cpython-314.pyc
│   │
│   ├───scrapers
│   │   │   ecom_scraper.py
│   │   │   quotes_scraper.py
│   │   │
│   │   └───__pycache__
│   │           ecom_scraper.cpython-314.pyc
│   │           quotes_scraper.cpython-314.pyc
│   │           __init__.cpython-314.pyc
│   │
│   ├───storage
│   │   │   minio_client.py
│   │   │   mongo_client.py
│   │   │   postgres_client.py
│   │   │   __init__.py
│   │   │
│   │   └───__pycache__
│   │           minio_client.cpython-314.pyc
│   │           mongo_client.cpython-314.pyc
│   │           postgres_client.cpython-314.pyc
│   │           __init__.cpython-314.pyc
│   │
│   └───__pycache__
│           pipeline.cpython-314.pyc
│           __init__.cpython-314.pyc
│
└───tests
```


## Architecture cible

```
SOURCES                     PIPELINE (ETL)                    DESTINATIONS
┌──────────────────┐        ┌────────────────────────┐        ┌──────────────────────┐
│  Fichier Excel   ├───────►│      ExcelLoader       ├───────►│      PostgreSQL      │
│  (Librairies)    │        │  (Nettoyage Pandas)    │        │   (fact_libraries)   │
└──────────────────┘        └──────────┬─────────────┘        └──────────┬───────────┘
                                       │                                 │
┌──────────────────┐        ┌──────────▼─────────────┐                   │
│   API Geo.api    │◄──────►│      APIEnricher       │◄──────────────────┘
│  (OpenStreetMap) │        │ (Adresse ➔ Lat/Long)   │ (Mise à jour SQL)
└──────────────────┘        └────────────────────────┘

┌──────────────────┐        ┌────────────────────────┐        ┌──────────────────────┐
│  WebScraper.io   ├───────►│    EcommerceScraper    ├───────►│      PostgreSQL      │
│  (E-commerce)    │        │ (Parsing + Upsert SQL) ├───────►│    (dim_products)    │
└──────────────────┘        └──────────┬─────────────┘        └──────────────────────┘
                                       │                      ┌──────────────────────┐
                                       ├─────────────────────►│       MongoDB        │
                                       │                      │  (Logs + Metadata)   │
                                       │                      └──────────────────────┘
                                       │                      ┌──────────────────────┐
                                       └─────────────────────►│        MinIO         │
                                                              │   (Product Images)   │
                                                              └──────────────────────┘

┌──────────────────┐        ┌────────────────────────┐        ┌──────────────────────┐
│ QuotesToScrape   ├───────►│     QuotesScraper      ├───────►│       MongoDB        │
│ (Citations)      │        │   (Parsing Soup)       ├───────►│  (Quotes & Authors)  │
└──────────────────┘        └────────────────────────┘        └──────────────────────┘
```

## Répartition des données

|Type de donnée	|PostgreSQL	|MongoDB	|MinIO|
|------------------|----------|-------|-------|
|Librairies (Excel) |✅ Oui	|❌ Non	|❌ Non|
|Produits (E-com)	|✅ Oui	|✅ Oui	|❌ Non|
|Images (E-com)	|❌ Non	|❌ Non	|✅ Oui|
|Citations (Quotes)	|❌ Non	|✅ Oui	|❌ Non|


## 1.Choix d'architecture globale
### Quelle architecture est proposée ? 
Je propose une Architecture Hybride qui combine les forces du Data Warehouse et du Data Lake.
Le Data Warehouse (PostgreSQL) : Pour les données structurées (Librairies, Produits).
Le Data Lake / NoSQL (MongoDB & MinIO) : Pour les données semi-structurées (Citations) et les fichiers bruts/images (Objets).


### Pourquoi ce choix ? 
Honnêtement, j'ai fais mon projet petit à petit, donc je n'ai pas choisis au départ, c'est une fois le projet en partie terminée que je me suis aperçue du rendu. 
Mais finalement, si j'avais tout mis dans PostgreSQL, le stockage des images aurait saturé la base de données et ralenti les performances. 

Donc l'hybride me permet d'utiliser "le bon outil pour la bonne donnée" :
SQL pour la cohérence et les calculs.
NoSQL pour la flexibilité du scraping.
Object Storage pour le stockage de fichiers volumineux (images).


### Avantages et inconvénients
Avantages
Flexibilité : On peut ajouter de nouveaux scrapers sans modifier le schéma des bases existantes (grâce à MongoDB).
Scalabilité : Les images sont déportées sur MinIO, ce qui permet de stocker des millions de produits sans alourdir les requêtes SQL.
Performance : L'enrichissement API est très performant sur PostgreSQL grâce aux index et aux clés primaires.
Sécurité des données : Les données critiques (prix, adresses) sont protégées par les contraintes d'intégrité du SQL.

Inconvénients 
Complexité de maintenance : Il faut gérer trois technologies différentes (Postgres, Mongo, MinIO) au lieu d'une seule.
Consistance des données : Si un produit est supprimé, il faut penser à le supprimer dans SQL, Mongo et MinIO.


## 2.Choix des technologies
### Technologie utilisée pour les données brutes 
Technologie utilisée : MongoDB (NoSQL orienté Document) et MinIO (Stockage d'objets).
Justification : Le web scraping génère des données "imprévisibles" (une citation peut être très longue, un produit peut avoir des caractéristiques variables). MongoDB accepte le format JSON sans schéma rigide. 
Pour les images, MinIO est indispensable car stocker des fichiers binaires dans une base de données ralentit tout le système.

Alternative : Amazon S3 (Cloud).
Comparaison : S3 est le standard industriel mais payant et dépendant d'Internet. MinIO offre les mêmes fonctionnalités en étant gratuit, open-source et installable localement via Docker, ce qui est idéal pour le développement et la souveraineté des données.

### Technologie utilisée pour les données transformées
Technologie utilisée : PostgreSQL (SGBD Relationnel).
Justification : Une fois les données nettoyées (adresses normalisées, prix convertis en nombres), elles deviennent structurées. PostgreSQL est l'outil parfait pour garantir l'intégrité de ces données (pas de doublons, types de données stricts) et permettre des relations complexes (ex: lier un produit à une catégorie).

Alternative : Google BigQuery (Data Warehouse Cloud).
Comparaison : BigQuery est surpuissant pour des pétaoctets de données, mais très coûteux pour des petits volumes. PostgreSQL est extrêmement performant pour des volumes moyens, gratuit, et supporte des extensions puissantes comme PostGIS pour la géolocalisation.

### Technologie utilisée pour l'interrogation SQL
Technologie utilisée : PostgreSQL (via SQL standard) et Pandas (Python).
Justification : SQL est le langage universel de la donnée. Il permet de répondre à des questions complexes en quelques lignes. Pour les analyses rapides dans le code, j'utilise Pandas qui permet de manipuler les tables comme des fichiers Excel ultra-puissants.

Alternative : NoSQL Aggregation Framework (MongoDB).
Comparaison : Faire des calculs complexes ou des jointures dans MongoDB est beaucoup plus verbeux et moins performant que le SQL standard. Le SQL permet également de connecter facilement des outils de visualisation (PowerBI, Tableau) que le NoSQL ne supporte pas nativement.

## 3.Organisation des données
### Comment les données sont-elles organisées dans l'architecture ?
J'organise les données selon une approche multicouche et multi-format pour séparer les responsabilités :

Organisation par Format :
Relationnel (PostgreSQL) : Les données structurées et nettoyées (Librairies, Produits).
Documentaire (MongoDB) : Les données semi-structurées ou changeantes (Citations, Métadonnées brutes).
Objets (MinIO) : Les fichiers binaires volumineux (Images JPG).

Organisation par Schéma : J'utilise un modèle en étoile simplifié dans PostgreSQL, avec des tables de faits (fact_libraries) et des tables de dimensions (dim_products).

### Quelles sont les couches de transformation et pourquoi ? 
Oui, j'adopte une architecture vue en cours qui est Bronze/Silver/Gold:
Couche Bronze (données brutes) : C'est le stockage des données brutes telles qu'elles arrivent (HTML des scrapers, JSON brut dans MongoDB, Excel original).
Pourquoi ? Pour pouvoir relancer le traitement sans rescraper si une erreur survient.

Couche Silver (données nettoyées et enrichies) : Les données sont nettoyées par Pandas et enrichies par l'API Geo. C'est ici que l'on normalise les formats de prix et qu'on ajoute les coordonnées GPS.
Pourquoi ? Pour garantir que les données sont prêtes à l'analyse.

Couche Gold (prête à l'utilisation) : Ce sont les tables finales dans PostgreSQL et les exports CSV/Parquet prêts pour le reporting.
Pourquoi ? Pour offrir une source de vérité unique aux utilisateurs finaux.

### Convention de nommage
snake_case (tout en minuscules avec des underscores).


## 4.Modélisation des données 
### Modèle de données proposées
Je propose un Schéma en étoile simplifié. C'est le standard du Data Warehousing. Il sépare les données en deux types de tables :
Table de Faits : Contient les événements ou les objets centraux (les librairies).
Tables de Dimensions : Contiennent les attributs descriptifs (les produits).

### Description des tables
2. Schéma Entité-Relation (ERD)
Voici la représentation visuelle des tables dans PostgreSQL :
fact_libraries_enriched :
id (PK)
nom_librairie
adresse
code_postal
ville
ca_annuel
specialite
date_partenariat

dim_geoloc :
id (PK)
library_id (FK)
latitude
longitude

dim_products :
id (PK)
source
title
price_euro
rating
category 
minio_image_uri (Lien vers le stockage objet)
scraped_at



### Justification des choix
Pourquoi un schéma en étoile ?
Simplicité des requêtes : Pour un analyste, il est très facile de faire un SELECT sur les librairies et de filtrer par spécialité ou localisation sans faire des jointures infinies.

Performance : Ce modèle est optimisé pour la lecture et l'agrégation de données (ex: calculer la moyenne des prix par catégorie).

Pourquoi l'utilisation de clés primaires (PK) et de types stricts ?
Intégrité : En utilisant le SKU ou un ID unique, j'empêche les doublons lors des mises à jour (méthode upsert).
Typage : Stocker le prix en FLOAT et les coordonnées en DECIMAL permet de faire des calculs mathématiques directs en SQL, ce qui serait impossible avec du texte brut.

Pourquoi avoir séparé les images du modèle relationnel ?
Le modèle relationnel ne stocke que la référence (le chemin MinIO). Cela respecte le principe de séparation du stockage : la base de données reste légère et rapide, tandis que les fichiers lourds sont gérés par un système dédié au stockage d'objets.


## Conformité RGPD
### Quelles sont les données personnelles dans les sources ? 
Source Excel (Librairies) : les données contact_nom et contact_mail ainsi que le CA.
Dans le projet : les identifiants et mots de passes des différentes interfaces

### Mesures de protection
Excel : Ces données sont toujours dans le CSV mais sont supprimées dans la base de données. Concernant le chiffre d'affaire annuel, il apparaît, mais il est essentiel de limiter l'accès aux données aux personnes habilitées uniquement. 
Le projet : création d'un fichier .env contenant tous les identifiants et les mots de passe. Ce fichier est dans le .gitignore afin qu'il reste privé. 

### Le droit à l'effacement
Traçabilité : Grâce à la modélisation avec des clés primaires, je peux identifier précisément une ligne de donnée et la supprimer sans affecter le reste de la base.
Suppression en cascade : l'orchestrateur pipeline.py peut être configuré pour supprimer une donnée sur tous les supports :
- Suppression de la ligne dans PostgreSQL.
- Suppression du document dans MongoDB.
- Suppression de l'image associée dans MinIO.


## Infrastructure Docker
```yml
services:
  # Stockage objet S3-compatible
  minio:
    image: minio/minio:latest
    container_name: ecf-minio
    ports:
      - "9000:9000"   
      - "9001:9001"   
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - tp-network

  # Base de données documentaire
  mongodb:
    image: mongo:7.0
    container_name: ecf-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: ecommerce_db
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - tp-network

  # Interface web pour MongoDB
  mongo-express:
    image: mongo-express:latest
    container_name: ecf-mongo-express
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: ${MONGO_USER}
      ME_CONFIG_MONGODB_ADMINPASSWORD: ${MONGO_PASSWORD}
      ME_CONFIG_MONGODB_URL: mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/
      ME_CONFIG_BASICAUTH: false
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - tp-network

  # Base de données relationnelle SQL
  postgres:
    image: postgres:16
    container_name: ecf-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: datapulse_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - tp-network

  # Interface web pour PostgreSQL
  pgadmin:
    image: dpage/pgadmin4
    container_name: ecf-pgadmin
    depends_on:
      - postgres
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD}
    ports:
      - "8080:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - tp-network

volumes:
  postgres_data:
  minio_data:
  mongo_data:
  pgadmin_data:

networks:
  tp-network:
    driver: bridge

```


# Partie 2 : Collecte des données
Voir code et RGPD_conformite.md

# Partie 3 : Pipeline ETL
De 3.1 à 3.3 tout est exécuté dans le code. 

## Requêtes analytiques