import argparse
import os
import time

from openai import OpenAI
import psycopg

parser = argparse.ArgumentParser()
parser.add_argument(
    "--skip-reload",
    action="store_true",
    help="Skip the reload process if this flag is provided.",
)
args = parser.parse_args()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
CHUNK_SIZE = 2048

opeani = OpenAI()

database_url = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:6432/rag_demo"
)
db = psycopg.Connection.connect(database_url)


# This is very naive chunking. LangChain has excellent chunking libraries.  Do not use
# this technique in production as it will yield very bad results.
def split_string_by_length(input_string, length):
    return [input_string[i : i + length] for i in range(0, len(input_string), length)]


# Loop through files in the data directory and create embeddings in the database
if not args.skip_reload:
    print("Cleaning database...")
    db.execute("TRUNCATE TABLE items")

    tic = time.perf_counter()
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)

        with open(file_path, "r") as file:
            content = file.read()

        for chunk in split_string_by_length(content, CHUNK_SIZE):
            response = opeani.embeddings.create(
                model="text-embedding-3-large",
                input=chunk,
            )
            print("Creating embedding...", len(chunk))
            db.execute(
                "INSERT INTO items (embedding, chunk) VALUES (%s, %s)",
                [str(response.data[0].embedding), chunk],
            )

    print(f"\nTotal index time: {time.perf_counter() - tic}ms")
    db.commit()

question = input("\nEnter question: ")

# Create embedding from question.  Many RAG applications use a query rewriter before querying
# the vector database.  For more information on query rewriting, see this whitepaper:
#    https://arxiv.org/abs/2305.14283
response = opeani.embeddings.create(
    model="text-embedding-3-large",
    input=question,
)

embedding = str(response.data[0].embedding)
result = db.execute(
    "SELECT 1 - (embedding <=> %s) as score, chunk FROM items ORDER BY embedding <-> %s LIMIT 5",
    [embedding, embedding],
)
rows = list(result)


print("scores: ", [row[0] for row in rows])
context = "\n\n".join([row[1] for row in rows])

prompt = f"""
Answer the question using only the following context:

{context}

Question: {question}
"""

response = opeani.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assisstant."},
        {"role": "user", "content": [{"type": "text", "text": prompt}]},
    ],
)

print(f"\nUsing {len(rows)} chunks in answer. Answer:\n")
print(response.choices[0].message.content)

view_prompt = input("\nWould you like to see the raw prompt? [Yn] ")
if view_prompt == "Y":
    print("\n" + prompt)
