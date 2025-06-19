import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import joblib
import re
import emoji

# 🔁 Paramètres de connexion à PostgreSQL
host = "localhost"
port = "5432"
database = "Tweet_loic"
user = "postgres"
password = "123"  # 🔒 Remplace par ton mot de passe réel

# ✅ Connexion avec SQLAlchemy
engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}')

# 🧽 Fonction de nettoyage
def nettoyer_texte(texte):
    texte = str(texte)
    texte = emoji.replace_emoji(texte, replace='')  # Supprimer les emojis
    texte = re.sub(r"http\S+", "", texte)           # Supprimer les URLs
    texte = re.sub(r"[^a-zA-Z\s]", "", texte)        # Supprimer ponctuation et chiffres
    texte = texte.lower()                            # Minuscules
    texte = re.sub(r"\s+", " ", texte).strip()       # Nettoyer les espaces
    return texte

# 📥 Charger les tweets depuis PostgreSQL avec date et auteur
query = """
    SELECT texte_nettoye, date, auteur
    FROM tweets_bluesky
    WHERE texte_nettoye IS NOT NULL;
"""
df = pd.read_sql_query(query, engine)

# 🆔 Ajouter un identifiant basé sur l'index (utile pour traçabilité)
df = df.reset_index().rename(columns={"index": "id"})

# 🔃 Nettoyage
df["texte_nettoye"] = df["texte_nettoye"].apply(nettoyer_texte)

# 📦 Charger le modèle et le vectorizer
model = joblib.load("modele_fakenews.joblib")
vectorizer = joblib.load("vectorizer_fakenews.joblib")

# 🧠 Fonction de prédiction
def score_fiabilite(texte):
    vect = vectorizer.transform([texte])
    proba = model.predict_proba(vect)[0][1]
    return round(proba, 3)

# ⚙️ Application du modèle
df["score_fiabilite"] = df["texte_nettoye"].apply(score_fiabilite)

# 💾 Sauvegarde avec date et auteur pour analyse
df[["id", "date", "auteur", "score_fiabilite"]].to_sql("tweets_bluesky_scores", engine, if_exists="replace", index=False)

print("✅ Prédictions terminées. Scores enregistrés dans la table 'tweets_bluesky_scores'.")
