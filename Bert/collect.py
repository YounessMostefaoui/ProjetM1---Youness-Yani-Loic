from atproto import Client
import psycopg2
import time
import re
import emoji
from langdetect import detect, LangDetectException


def nettoyer_texte(texte):
    texte = emoji.replace_emoji(texte, replace='')  # Supprimer les emojis
    texte = re.sub(r"http\S+", "", texte)           # Supprimer les URLs
    texte = re.sub(r"[^a-zA-Z\s]", "", texte)       # Supprimer tout sauf lettres et espaces
    texte = texte.lower()                            # Mettre en minuscules
    texte = re.sub(r"\s+", " ", texte).strip()      # Nettoyer les espaces
    return texte

def est_anglais(texte):
    try:
        return detect(texte) == "en"
    except LangDetectException:
        return False

# Connexion à PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="Tweet_loic",
    user="postgres",
    password="123"
)
cursor_pg = conn.cursor()

cursor_pg.execute("""
    CREATE TABLE IF NOT EXISTS tweets_bluesky (
        date TIMESTAMP,
        auteur TEXT,
        likes INT,
        reposts INT,
        replies INT,
        total_interactions INT,
        contenu TEXT,
        sujet_principal TEXT,
        texte_nettoye TEXT
    );
""")
conn.commit()

client = Client()
client.login('youness.mostefaoui@free.fr', 'Honaine77aa..()')

all_posts = []
cursor = None
hashtag = "political"

while len(all_posts) < 4000:
    params = {"q": hashtag, "limit": 100}
    if cursor:
        params["cursor"] = cursor

    feed = client.app.bsky.feed.search_posts(params)

    # Gérer différentes structures de réponses possibles
    if hasattr(feed, "results"):
        posts = feed.results
    elif hasattr(feed, "feed"):
        posts = feed.feed
    elif hasattr(feed, "posts"):
        posts = feed.posts
    else:
        print("Aucun attribut 'results', 'feed' ou 'posts' trouvé dans la réponse.")
        break

    if not posts:
        print("Plus de posts disponibles, fin de la pagination.")
        break

    print(f"{len(posts)} posts récupérés (total : {len(all_posts) + len(posts)})")
    all_posts.extend(posts)
    cursor = getattr(feed, "cursor", None)

    if not cursor:
        print("Fin de la pagination.")
        break

    time.sleep(1)

print(f"Total posts récupérés : {len(all_posts)}")

for post in all_posts:
    texte = getattr(post.record, "text", "")
    if not texte.strip():
        continue

    if not est_anglais(texte):
        continue

    date = post.record.created_at
    auteur = post.author.handle
    likes = getattr(post, "like_count", 0) or 0
    reposts = getattr(post, "repost_count", 0) or 0
    replies = getattr(post, "reply_count", 0) or 0
    total_interactions = likes + reposts + replies

    if total_interactions <= 1:
        continue

    mots_cles = [mot for mot in texte.lower().split() if mot.isalpha()]
    sujet_principal = mots_cles[0] if mots_cles else "inconnu"
    texte_nettoye = nettoyer_texte(texte)

    cursor_pg.execute("""
        INSERT INTO tweets_bluesky (
            date, auteur, likes, reposts, replies,
            total_interactions, contenu, sujet_principal, texte_nettoye
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        date, auteur, likes, reposts, replies,
        total_interactions, texte, sujet_principal, texte_nettoye
    ))

conn.commit()
cursor_pg.close()
conn.close()

print("Export PostgreSQL terminé.")
