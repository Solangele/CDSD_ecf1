-- 1. Requête d'agrégation simple
-- Objectif : Calculer le CA total et moyen par spécialité de librairie
SELECT 
    specialite,
    COUNT(*) as nombre_librairies,
    ROUND(SUM(ca_annuel)::numeric, 2) as ca_total,
    ROUND(AVG(ca_annuel)::numeric, 2) as ca_moyen
FROM fact_libraries_enriched
GROUP BY specialite
ORDER BY ca_total DESC;


-- 2. Requête avec jointure
-- Objectif : Lister les librairies avec leur position GPS exacte
SELECT 
    l.nom_librairie,
    l.ville,
    l.specialite,
    g.latitude,
    g.longitude
FROM fact_libraries_enriched l
INNER JOIN dim_geoloc g ON l.id = g.library_id
ORDER BY l.ville;


-- 3. Requête avec fonction de fenêtrage (Window Function)
-- Objectif : Calculer le rang de chaque librairie par CA au sein de sa propre ville
SELECT 
    nom_librairie,
    ville,
    ca_annuel,
    RANK() OVER(PARTITION BY ville ORDER BY ca_annuel DESC) as rang_ca_par_ville
FROM fact_libraries_enriched;


-- 4. Requête de classement (Top N)
-- Objectif : Identifier les 5 produits les mieux notés du catalogue e-commerce
SELECT 
    title,
    category,
    price_euro,
    rating
FROM dim_products
WHERE rating IS NOT NULL
ORDER BY rating DESC, price_euro ASC
LIMIT 5;


-- 5. Requête croisant au moins 2 sources de données
-- Objectif : Comparer le CA des librairies avec le prix moyen des produits scrapés
SELECT 
    l.specialite as categorie_librairie,
    ROUND(AVG(l.ca_annuel)::numeric, 2) as ca_moyen_librairies,
    (SELECT ROUND(AVG(price_euro), 2) FROM dim_products) as prix_moyen_catalogue_global
FROM fact_libraries_enriched l
GROUP BY l.specialite;