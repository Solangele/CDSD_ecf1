# Documentation de Conformité RGPD - Projet DataPulse

Ce document détaille les mesures prises pour assurer la conformité au Règlement Général sur la Protection des Données (RGPD) au sein de l'architecture DataPulse.


## 1. Inventaire des données à caractère personnel (DCP)
Dans le cadre de ce projet, j'ai collecté et traité les données suivantes :

| Source | Donnée collectée | Finalité | État après traitement |
| :--- | :--- | :--- | :--- |
| **Excel Partenaires** | Nom de la librairie | Identification du partenaire | Conservée |
| **Excel Partenaires** | Adresse postale | Géocodage et cartographie | Conservée |
| **Excel Partenaires** | Nom/Prénom Gérant | Contact commercial | **Supprimée (Minimisation)** |
| **Excel Partenaires** | Email / Téléphone | Contact commercial | **Supprimée (Minimisation)** |
| **Quotes to Scrape** | Noms d'auteurs | Attribution des citations | Conservée (Donnée publique) |
| **Logs Système** | Adresse IP | Sécurité et debug | Non stockée de façon persistante |

---

## 2. Bases légales du traitement
Le traitement des données repose sur les bases légales définies par l'Article 6 du RGPD :

* **Intérêt Légitime (Art 6.1.f) :** Traitement des adresses professionnelles des librairies pour permettre leur visualisation cartographique et enrichissement via l'API Adresse.
* **Obligation Contractuelle (Art 6.1.b) :** Gestion des informations nécessaires à la relation avec les partenaires libraires.
* **Données Publiques :** Le scraping de citations concerne des données rendues publiques par leurs auteurs.

---

## 3. Mesures de protection mises en œuvre
Afin de garantir la sécurité et la confidentialité des données, les mesures suivantes sont intégrées nativement ("Privacy by Design") :

### A. Minimisation des données
Le module `ExcelLoader` effectue un nettoyage systématique dès la lecture du fichier source. Les données non nécessaires à la finalité du projet (noms des gérants, emails, téléphones) sont supprimées avant toute insertion dans la base de données PostgreSQL.

### B. Sécurité technique
* **Isolation réseau :** Les bases de données PostgreSQL (données structurées) et MongoDB (données brutes) sont isolées dans un réseau virtuel Docker, non exposé directement sur Internet.
* **Gestion des secrets :** Les identifiants de connexion aux bases de données et aux services (MinIO) sont stockés dans un fichier `.env` exclu du versionnage Git.
* **Anonymisation des fichiers :** Les images stockées sur MinIO sont renommées de manière à ne contenir aucune information personnelle identifiable.

### C. Stratégie de mise à jour
L'utilisation du mode `if_exists='replace'` pour l'import des partenaires garantit que si une donnée est supprimée de la source (exercice du droit à l'oubli), elle est également supprimée de l'architecture de données lors de la prochaine exécution du pipeline.

---

## 4. Procédure d'exercice des droits (Droit à l'effacement)
Conformément aux articles 15 à 21 du RGPD, toute personne peut demander l'accès, la rectification ou la suppression de ses données.

**Procédure technique de suppression :**
1.  **Identification :** Recherche de l'entrée via l'ID unique dans la table `fact_libraries`.
2.  **Suppression SQL :** Exécution de la commande `DELETE FROM fact_libraries WHERE id = X;`.
3.  **Nettoyage NoSQL :** Suppression des documents associés dans MongoDB (le cas échéant).
4.  **Suppression Objet :** Retrait des fichiers liés (images) sur le serveur MinIO.

---
*Document généré le : 06 Janvier 2026*
*Responsable de traitement : [Ton Nom/Prénom]*