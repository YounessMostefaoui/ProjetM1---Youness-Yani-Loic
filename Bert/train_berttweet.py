import pandas as pd
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import evaluate

# 1. Charger les données
df = pd.read_csv("merged_fake_news_dataset.csv")
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle
df = df[["text", "label"]].dropna()

# 2. Charger le tokenizer
checkpoint = "vinai/bertweet-base"
tokenizer = AutoTokenizer.from_pretrained(checkpoint, normalization=True)

# 3. Tokenisation
def tokenize_function(example):
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=128)

dataset = Dataset.from_pandas(df)
dataset = dataset.map(tokenize_function, batched=True)
dataset = dataset.train_test_split(test_size=0.2)

# 4. Préparer le modèle
model = AutoModelForSequenceClassification.from_pretrained(checkpoint, num_labels=2)

# 5. Metrics
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = torch.argmax(torch.tensor(logits), dim=1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted')
    acc = accuracy_score(labels, predictions)
    return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1}

# 6. Entraînement
training_args = TrainingArguments(
    output_dir="./results_berttweet",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

trainer.train()

# 7. Évaluation
trainer.evaluate()

# 8. Sauvegarde
model.save_pretrained("berttweet_fakenews_model")
tokenizer.save_pretrained("berttweet_fakenews_model")
