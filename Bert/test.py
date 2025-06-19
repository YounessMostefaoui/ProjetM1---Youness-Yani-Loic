import pandas as pd
import os
import json
import re
import psycopg2
from psycopg2 import sql

def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)  # URLs
    text = re.sub(r"@\w+", "", text)     # mentions
    text = re.sub(r"#\w+", "", text)     # hashtags
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ---- LIAR ----
def process_liar():
    liar_dfs = []
    for file in ["train.tsv", "test.tsv", "valid.tsv"]:
        cols = ["label", "statement", "subject", "speaker", "job", "state", "party", "barely_true", "false", 
                "half_true", "mostly_true", "pants_on_fire", "context"]
        df = pd.read_csv(file, sep='\t', names=cols, encoding='utf-8')
        label_map = {
            "true": 1, "mostly-true": 1, "half-true": 1,
            "barely-true": 0, "false": 0, "pants-fire": 0
        }
        df = df[df["label"].isin(label_map)]
        df["label"] = df["label"].map(label_map)
        df = df[["statement", "label"]].rename(columns={"statement": "text"})
        df["source"] = "LIAR"
        liar_dfs.append(df)
    liar_all = pd.concat(liar_dfs)
    liar_all["text"] = liar_all["text"].apply(clean_text)
    return liar_all

# ---- FakeNewsNet ----
def process_fakenewsnet():
    data = []
    sources = [
        ("politifact_real.csv", 1, "politifact"),
        ("politifact_fake.csv", 0, "politifact"),
        ("gossipcop_real.csv", 1, "gossipcop"),
        ("gossipcop_fake.csv", 0, "gossipcop"),
    ]
    for file, label, source in sources:
        if not os.path.exists(file):
            print(f"[⚠️] Fichier introuvable : {file}")
            continue

        df = pd.read_csv(file)
        print(f"[📄] {file} colonnes : {df.columns.tolist()} - lignes : {len(df)}")

        if 'title' in df.columns:
            df = df[["title"]].dropna()
            df["label"] = label
            df["source"] = "FakeNewsNet"
            df["text"] = df["title"].apply(clean_text)
            df = df[["text", "label", "source"]]
            data.append(df)
        else:
            print(f"[⚠️] Aucune colonne utilisable trouvée dans {file}")
    if not data:
        print("[❌] Aucun fichier valide à concaténer dans FakeNewsNet")
    return pd.concat(data) if data else pd.DataFrame(columns=["text", "label", "source"])

# ---- PHEME ----
def process_pheme(pheme_dir="phemerumourschemedataset/pheme-rumour-scheme-dataset/threads/en"):
    data = []

    if not os.path.exists(pheme_dir):
        return pd.DataFrame(columns=["text", "label", "source"])

    for event in os.listdir(pheme_dir):
        event_path = os.path.join(pheme_dir, event)
        if not os.path.isdir(event_path):
            continue

        for thread in os.listdir(event_path):
            thread_path = os.path.join(event_path, thread)
            tweet_dir = os.path.join(thread_path, "source-tweets")
            if not os.path.isdir(tweet_dir):
                continue

            for json_file in os.listdir(tweet_dir):
                if json_file.endswith(".json"):
                    json_path = os.path.join(tweet_dir, json_file)
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            tweet = json.load(f)
                            text = tweet.get("text", "").strip()
                            if text:
                                data.append({"text": clean_text(text), "label": 0, "source": "PHEME"})
                    except Exception:
                        pass

    return pd.DataFrame(data)

# ---- Insert into PostgreSQL via psycopg2 ----
def insert_into_postgres_psycopg2(df, user, password, host, port, database, table_name="fake_news"):
    import psycopg2
    from psycopg2 import sql

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = conn.cursor()

        # Crée ou remplace la table
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name)))
        cursor.execute(sql.SQL("""
            CREATE TABLE {} (
                text TEXT,
                label INTEGER,
                source VARCHAR(50)
            )
        """).format(sql.Identifier(table_name)))

        # Nettoie les chaînes pour éviter les erreurs d'encodage
        df["text"] = df["text"].astype(str).apply(lambda x: x.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore"))

        # Insère les données
        for _, row in df.iterrows():
            cursor.execute(
                sql.SQL("INSERT INTO {} (text, label, source) VALUES (%s, %s, %s)").format(sql.Identifier(table_name)),
                (row["text"], row["label"], row["source"])
            )

        conn.commit()
        print(f"[✅] Données insérées dans la table '{table_name}' de la base '{database}'")

    except Exception as e:
        print(f"[❌] Erreur PostgreSQL : {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---- Main script ----
if __name__ == "__main__":
    df_liar = process_liar()
    df_fnn = process_fakenewsnet()
    df_pheme = process_pheme()

    df_all = pd.concat([df_liar, df_fnn, df_pheme], ignore_index=True)
    print(df_all.head())
    print(f"Total lignes : {len(df_all)}")

    # Sauvegarde locale
    df_all.to_csv("merged_fake_news_dataset.csv", index=False)

    # Paramètres PostgreSQL
    user = "postgres"
    password = "123"
    host = "localhost"
    port = 5432
    database = "Training"

    insert_into_postgres_psycopg2(df_all, user, password, host, port, database)

