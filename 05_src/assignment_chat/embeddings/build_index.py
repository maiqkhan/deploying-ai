import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

chroma_client = chromadb.PersistentClient(path="./embeddings/chroma_db")

collections = chroma_client.list_collections()
if "travel_guides" in [col.name for col in collections]:
    chroma_client.delete_collection(name="travel_guides")

collection = chroma_client.create_collection(
    name = "travel_guides",
    embedding_function = OpenAIEmbeddingFunction(
        api_key = "any value",
        model_name="text-embedding-3-small",
        api_base='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1',
        default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')}
))

df = pd.read_csv("./embeddings/data/articles.csv")
df = df.dropna(subset=["text"])          # drop any rows with empty text
df = df[df["text"].str.strip() != ""].copy()


batch_size = 10  # keep small to avoid gateway timeouts

for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i + batch_size]
    collection.add(
        ids=batch["id"].astype(str).tolist(),
        documents=batch["text"].tolist(),
        metadatas=[
            {"title": row["title"], "url": row.get("url", "")}
            for _, row in batch.iterrows()
        ],
    )
    print(f"Indexed {min(i + batch_size, len(df))}/{len(df)}")

print(f"\nDone — {collection.count()} documents in collection")