import sqlite3
import json
import numpy as np
from ollama import Client 

client = Client()

conn = sqlite3.connect("knowledge.db")

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )

while True:
    query = ""
    while query == "":
        query = input("\nSearch (or 'exit'): ").strip()

    if query.lower() in ["exit", "quit"]:
        break

    response = client.embed(
        model="nomic-embed-text",
        input=query
    )

    query_embedding = response["embeddings"][0]

    rows = conn.execute("""
        SELECT
            tweet_id,
            tweet_url,
            name,
            description,
            tags,
            raw_text,
            embedding
        FROM knowledge
    """)

    results = []

    for row in rows:

        stored_embedding = json.loads(row[6])

        score = cosine_similarity(
            query_embedding,
            stored_embedding
        )

        results.append((score, row))

    results.sort(key=lambda x: x[0], reverse=True)

    per_page = 5
    total_pages = (len(results) + per_page - 1) // per_page
    page = 1

    while True:
        start = (page - 1) * per_page
        end = start + per_page
        page_results = results[start:end]

        if not page_results:
            print("\nNo more results.")
            break

        print(f"\nResults (page {page}/{total_pages}):\n")

        for score, row in page_results:
            tweet_id = row[0]
            tweet_url = row[1]
            name = row[2]
            description = row[3]
            tags = json.loads(row[4])
            raw_text = row[5]

            print("=" * 80)
            print(f"Score: {score:.3f}")
            print(f"Title: {name}")
            print(f"Tags: {', '.join(tags)}")
            print(f"Description: {description}")
            print(f"Tweet: {tweet_url}")
            print()
            print(raw_text[:300])
            print()

        cmd = input(f"[n]ext / [p]rev / [q]uit / page # ({page}/{total_pages}): ").strip().lower()

        if cmd == "q" or cmd == "quit":
            break
        elif cmd == "n" or cmd == "next":
            if page < total_pages:
                page += 1
            else:
                print("Already on last page.")
        elif cmd == "p" or cmd == "prev":
            if page > 1:
                page -= 1
            else:
                print("Already on first page.")
        elif cmd.isdigit():
            p = int(cmd)
            if 1 <= p <= total_pages:
                page = p
            else:
                print(f"Page must be between 1 and {total_pages}.")
        else:
            print("Unknown command.")
