import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# --- Connexion à PostgreSQL via psycopg2 ---
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="Tweet_loic",
    user="postgres",
    password="123"
)

# Charger les tweets (ici la colonne texte est "contenu" dans ta table)
df = pd.read_sql_query("SELECT date, auteur, contenu FROM tweets_bluesky", conn)
conn.close()

# --- Charger le modèle fine-tuné ---
model_path = "./berttweet_fakenews_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# --- Fonction de prédiction ---
def predict(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        preds = torch.argmax(probs, dim=1)
    return preds.cpu().numpy(), probs[:, 1].cpu().numpy()

# --- Prédiction par batchs pour gérer la mémoire ---
batch_size = 32
results = []

for i in range(0, len(df), batch_size):
    batch_texts = df['contenu'].iloc[i:i+batch_size].tolist()
    pred_classes, pred_probs = predict(batch_texts)
    for date_, auteur_, pred, prob in zip(df['date'].iloc[i:i+batch_size], df['auteur'].iloc[i:i+batch_size], pred_classes, pred_probs):
        results.append((date_, auteur_, pred, prob))

df_results = pd.DataFrame(results, columns=["date", "auteur", "prediction", "fake_proba"])

# --- Sauvegarde des résultats dans PostgreSQL via SQLAlchemy ---
engine = create_engine("postgresql://postgres:123@localhost:5432/Tweet_loic")
df_results.to_sql("resultats_predictions", engine, if_exists="replace", index=False)

print("Prédictions sauvegardées dans la table 'resultats_predictions'.")
