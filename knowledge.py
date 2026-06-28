import json
import re
import sqlite3
from pathlib import Path

from ollama import Client 

client = Client()

DB = "knowledge.db"

###############################################################################
# DATABASE
###############################################################################

conn = sqlite3.connect(DB)

conn.execute("""
CREATE TABLE IF NOT EXISTS knowledge (
    tweet_id TEXT PRIMARY KEY,
    tweet_url TEXT,
    raw_text TEXT,
    name TEXT,
    description TEXT,
    tags TEXT,
    embedding TEXT
)
""")

###############################################################################
# LOAD LIKES
###############################################################################

content = Path("like.js").read_text(encoding="utf-8")

content = re.sub(
    r"^window\.YTD\.like\.part0\s*=\s*",
    "",
    content
)

likes = json.loads(content)

###############################################################################
# HELPERS
###############################################################################

def classify_tweet(text):
    prompt = f"""
You are organizing a personal knowledge database.

Return JSON only.
Do not include explanations.
Do not use markdown code fences.

Tweet:
{text}

Schema:

{{
  "name": "short title",
  "description": "1-2 sentence summary",
  "tags": ["tag1","tag2","tag3"]
}}

Rules:
- name under 8 words
- description under 50 words
- 1-5 tags
"""

    response = client.chat(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}],
        format={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
        "required": ["name", "description", "tags"]
        }
    )

    print("response", response)

    content = response["message"]["content"]
    
    print("content", content)

    try:
        meta = json.loads(content)

        required = {"name", "description", "tags"}
        if not isinstance(meta, dict):
            raise ValueError(f"Expected dict, got {type(meta)}")

        if not required.issubset(meta):
            raise ValueError(
                f"Model violated schema. Keys: {list(meta.keys())}"
            )

        return meta
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", content, re.S)
        if match:
            return json.loads(match.group(0))
        raise

def get_embedding(text):
    embedding_response = client.embed(
        model="nomic-embed-text",
        input=text
    )

    return embedding_response["embeddings"][0]


###############################################################################
# PROCESS
###############################################################################

for item in likes:
    like = item["like"]
    tweet_id = like["tweetId"]
    raw_text = like["fullText"]
    tweet_url = f"https://x.com/i/web/status/{tweet_id}"

    try:

        meta = classify_tweet(raw_text)
        embedding = get_embedding(
            f"{meta['name']}\n{meta['description']}\n{raw_text}"
        )

        conn.execute(
            """
            INSERT OR REPLACE INTO knowledge
            (
                tweet_id,
                tweet_url,
                raw_text,
                name,
                description,
                tags,
                embedding
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tweet_id,
                tweet_url,
                raw_text,
                meta["name"],
                meta["description"],
                json.dumps(meta["tags"]),
                json.dumps(embedding)
            )
        )

        print("Processed", tweet_id)
    except Exception as e:
        print("Failed", tweet_id, e)

conn.commit()

print("Done.")
