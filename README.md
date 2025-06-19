# ProjetM1---Youness-Yani-Loic

📰 Fake News Detection on Bluesky — Guide Utilisateur --- BERT
📦 Présentation du projet

Ce projet vise à collecter des posts depuis la plateforme Bluesky, les stocker dans une base PostgreSQL, et à entraîner un modèle de classification pour détecter les fake news, en s'appuyant sur un ensemble de données fusionnées provenant de LIAR, FakeNewsNet et PHEME. Le modèle utilise BERTweet, une version optimisée de BERT pour les tweets.
📁 Structure du projet

    collect.py : collecte les posts de Bluesky et les insère dans PostgreSQL.

    test.py : fusionne les jeux de données LIAR, FakeNewsNet, PHEME, les nettoie, les insère dans PostgreSQL.

    test_berttweet.py : utilise un modèle BERTweet pour évaluer les tweets collectés.

    merged_fake_news_dataset.csv : dataset fusionné prêt à l'emploi pour l'entraînement/évaluation.

⚙️ Prérequis
Python Packages

Installe les dépendances nécessaires :

pip install -r requirements.txt

Base de données PostgreSQL

Deux bases de données sont utilisées :

    Tweet_loic : stocke les tweets collectés sur Bluesky.

    Training : stocke les jeux de données annotés (LIAR, FakeNewsNet, PHEME).

🛰️ 1. Script collect.py — Collecte de tweets sur Bluesky

Ce script :

    Se connecte à l'API de Bluesky via atproto.

    Cherche jusqu'à 4000 posts avec un hashtag (par défaut #political).

    Filtre les posts non anglais ou peu engageants.

    Nettoie le texte (suppression des emojis, URLs, etc.).

    Insère les tweets dans la base PostgreSQL Tweet_loic, table tweets_bluesky.

🔧 Configuration à modifier

    Identifiants Bluesky :

    client.login('TON_EMAIL', 'TON_MOT_DE_PASSE')

    Connexion PostgreSQL (host, user, password, dbname).

💻 Exécution

python collect.py

📊 2. Script test.py — Fusion et insertion des datasets annotés

Ce script :

    Charge les jeux de données LIAR, FakeNewsNet et PHEME.

    Nettoie les textes (suppression hashtags, mentions, URLs).

    Remappe les labels (1 = vrai, 0 = fake).

    Fusionne le tout dans un DataFrame unique.

    Sauvegarde un CSV local merged_fake_news_dataset.csv.

    Crée la table fake_news dans la base Training et y insère les données.

📁 Structure attendue

Assurez-vous que les fichiers suivants sont présents dans le dossier :

    train.tsv, test.tsv, valid.tsv (pour LIAR)

    politifact_real.csv, politifact_fake.csv, gossipcop_real.csv, gossipcop_fake.csv (pour FakeNewsNet)

    Dossier phemerumourschemedataset/pheme-rumour-scheme-dataset/threads/en (pour PHEME)

💻 Exécution

python test.py

🤖 3. Script test_berttweet.py — Détection de fake news via BERTweet

Ce script (incomplet dans l'extrait fourni) :

    Se connecte à la base Tweet_loic.

    Charge les tweets collectés.

    Applique un modèle BERTweet (vinai/bertweet-base ou fine-tuné) pour prédire leur fiabilité.

    Affiche ou sauvegarde les prédictions.

📌 À compléter

    Le chargement des données et l’inférence du modèle semblent inachevés.

    Ajouter :

        Chargement du tokenizer + modèle AutoTokenizer/AutoModelForSequenceClassification

        Traitement batch des tweets

        Sauvegarde ou affichage des résultats

🗃️ Structure des tables PostgreSQL
Table tweets_bluesky (Tweet_loic)
Colonne	Type	Description
date	TIMESTAMP	Date de création du tweet
auteur	TEXT	Identifiant de l'auteur
likes	INT	Nombre de likes
reposts	INT	Nombre de reposts
replies	INT	Nombre de réponses
total_interactions	INT	Somme des likes, reposts, réponses
contenu	TEXT	Texte brut du post
sujet_principal	TEXT	Mot-clé principal extrait
texte_nettoye	TEXT	Texte nettoyé pour NLP
Table fake_news (Training)
Colonne	Type	Description
text	TEXT	Texte nettoyé
label	INTEGER	1 = vrai, 0 = fake
source	VARCHAR	Nom de la source (LIAR, FNN, PHEME)
🧪 Test rapide (pipeline minimal)

# Étape 1 : collecter les tweets
python collect.py

# Étape 2 : préparer le jeu de données annoté
python test.py

# Étape 3 : exécuter l'analyse BERTweet
python test_berttweet.py  # une fois complété

🚧 À améliorer

    Sécurisation des identifiants (via .env)

    Ajout d’un script d’évaluation de performance (accuracy, F1-score)

    Option CLI pour choisir hashtag ou volume

    Interface web (ex: Dash/Streamlit) pour visualisation en direct


    📰 Fake News Detection on Bluesky — Guide Utilisateur --- Regression Logistic


⚙️ Prérequis
📦 Librairies Python

Installer les dépendances :

pip install -r requirements.txt

requirements.txt :

atproto
emoji
langdetect
pandas
scikit-learn
joblib
sqlalchemy
psycopg2

🐘 PostgreSQL

Une base PostgreSQL doit être en place (modifiable dans test.py).

CREATE DATABASE Tweet_loic;

🧩 Détail des scripts
📥 collect.py – Récupération de tweets depuis Bluesky
🎯 Objectif :

    Se connecter à l’API Bluesky.

    Collecter les posts contenant un hashtag donné.

    Nettoyer et filtrer les posts (langue anglaise, interactions significatives).

    Sauvegarder les données dans tweets_bluesky_.csv.

🔧 Paramètres clés :

    Hashtag : modifiable dans hashtag = "political"

    Limite : 4000 posts par défaut

    Filtrage :

        Langue : anglais uniquement

        Suppression des emojis, URL, symboles

        Filtrage des posts avec interactions faibles (≤1)

▶️ Exécution :

python collect.py

Le fichier tweets_bluesky_.csv contiendra :
date	auteur	likes	reposts	replies	total_interactions	contenu	sujet_principal	texte_nettoye
🧠 traitement.py – Entraînement du modèle ML
🎯 Objectif :

    Charger le dataset train.tsv (dataset LIAR).

    Nettoyer les textes.

    Transformer les labels en binaire (fake vs true).

    Entraîner un modèle de régression logistique avec TF-IDF.

    Sauvegarder le modèle et le vectorizer.

🔧 Détails :

    Mapping des labels :

        pants-fire, false, barely-true → 0 (Fake)

        half-true, mostly-true, true → 1 (True)

    Nettoyage : suppression emojis, ponctuation, URL, etc.

📦 Sorties :

    modele_fakenews.joblib

    vectorizer_fakenews.joblib

    tweets_avec_score.csv (si prédiction directe sur tweets_bluesky_.csv)

▶️ Exécution :

python traitement.py

🔮 test.py – Application du modèle sur les données Bluesky
🎯 Objectif :

    Charger les tweets nettoyés depuis PostgreSQL.

    Charger le modèle et le vectorizer.

    Appliquer le modèle sur les textes.

    Écrire les scores de fiabilité dans une nouvelle table.

🐘 Connexion PostgreSQL :

Modifiable dans ces lignes :

host = "localhost"
port = "5432"
database = "Tweet_loic"
user = "postgres"
password = "123"

📦 Table attendue :

Table tweets_bluesky avec la colonne texte_nettoye.
📦 Table créée :

tweets_bluesky_scores avec colonnes :
| id | date | auteur | score_fiabilite |
▶️ Exécution :

python test.py

📈 Exemple d'utilisation

# Étape 1 : Collecte de données
python collect.py

# Étape 2 : Entraînement modèle
python traitement.py

# Étape 3 : Application du modèle sur nouveaux tweets
python test.py

🛡️ Sécurité et bonnes pratiques

    Ne jamais versionner vos identifiants Bluesky : stockez-les dans un fichier .env ou utilisez des variables d’environnement.

    Vérifiez que modele_fakenews.joblib n’est pas sur-appris (overfitting).

    Vous pouvez tester avec d'autres modèles : SVM, RandomForest, BERTweet (via HuggingFace).

🔭 Perspectives

    Améliorer la détection avec des modèles plus puissants (BERTweet).

    Ajouter une analyse visuelle des scores (via Dash, Plotly...).

    Étendre la détection aux tweets en français.

    Mesurer l’empreinte carbone des modèles.