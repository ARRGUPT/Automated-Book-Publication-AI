import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
print("Available collections:", client.list_collections())

try:
    collection = client.get_collection("book_chapters")
    results = collection.get()
    print(results)
except Exception as e:
    print("Error:", e)