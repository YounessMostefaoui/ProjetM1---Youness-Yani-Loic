import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import emoji
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib

# Charger le fichier TSV (adapte le chemin si besoin)
df = pd.read_csv("train.tsv", sep='\t', header=None)

# Afficher les premières lignes pour voir la structure
print(df.head())

# Afficher un résumé des colonnes pour comprendre leur contenu
print(df.info())

# Récupérer les modalités uniques de la colonne 1 (index 1)
modalites = df[1].dropna().unique()

print("Modalités uniques dans la colonne 1 :")
for modalite in sorted(modalites):
    print(modalite)


# On fait le mapping des labels en binaire
mapping = {
    "pants-fire": 0,
    "false": 0,
    "barely-true": 0,
    "half-true": 1,
    "mostly-true": 1,
    "true": 1
}

df['label_binary'] = df[1].map(mapping)

# Vérifie que le mapping a bien fonctionné
print(df[[1, 'label_binary']].head(10))
print(df['label_binary'].value_counts())



# Fonction de nettoyage
def nettoyer_texte(texte):
    texte = str(texte)
    texte = emoji.replace_emoji(texte, replace='')  # Enlever les emojis
    texte = re.sub(r"http\S+", "", texte)           # Enlever les URLs
    texte = re.sub(r"[^a-zA-Z\s]", "", texte)        # Enlever la ponctuation
    texte = texte.lower()                            # Minuscule
    texte = re.sub(r"\s+", " ", texte).strip()       # Nettoyage des espaces
    return texte

# Nettoyage des textes
df['texte_nettoye'] = df[2].apply(nettoyer_texte)

# Séparer X et y
X = df['texte_nettoye']
y = df['label_binary']

# Découper en train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Vectorisation TF-IDF
vectorizer = TfidfVectorizer(max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)


# Entraînement du modèle
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# Prédictions
y_pred = model.predict(X_test_vec)

# Évaluation
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nMatrice de confusion :\n", confusion_matrix(y_test, y_pred))
print("\nRapport de classification :\n", classification_report(y_test, y_pred))


# Pour un texte donné, on veut la probabilité d’être “True”
def score_fiabilite(texte):
    texte_nettoye = nettoyer_texte(texte)
    texte_vect = vectorizer.transform([texte_nettoye])
    proba = model.predict_proba(texte_vect)[0][1]  # probabilité que ce soit une vraie info
    return round(proba, 3)




# Sauvegarde du modèle
joblib.dump(model, "modele_fakenews.joblib")

# Sauvegarde du vectorizer
joblib.dump(vectorizer, "vectorizer_fakenews.joblib")

print("✅ Modèle et vectorizer sauvegardés.")



# Charger modèle et vectorizer
model = joblib.load("modele_fakenews.joblib")
vectorizer = joblib.load("vectorizer_fakenews.joblib")

# Fonction pour prédire un score entre 0 (fake) et 1 (fiable)
def score_fiabilite(texte):
    vect = vectorizer.transform([texte])
    proba = model.predict_proba(vect)[0][1]  # proba que ce soit une vraie info
    return round(proba, 3)

# Charger les tweets Bluesky déjà nettoyés
df = pd.read_csv("tweets_bluesky_.csv")

# Vérification de la colonne "texte_nettoye"
if "texte_nettoye" not in df.columns:
    raise ValueError("La colonne 'texte_nettoye' est manquante dans le CSV.")

# Calcul du score de fiabilité pour chaque ligne
df["score_fiabilite"] = df["texte_nettoye"].apply(score_fiabilite)

# Sauvegarde dans un nouveau fichier
df.to_csv("tweets_avec_score.csv", index=False, encoding="utf-8")
print("✅ Prédictions terminées. Résultats enregistrés dans 'tweets_avec_score.csv'.")
