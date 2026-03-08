from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# 1. Modeli Yükle (Dünyanın en popüler küçük modellerinden biri)
model = SentenceTransformer('all-MiniLM-L6-v2') # Bu model 384 boyutlu vektör üretir

# 2. Qdrant'a Bağlan
client = QdrantClient(host="localhost", port=6333)
collection_name = "text_search_deneme"

# 3. Koleksiyonu Oluştur (Model 384 boyutlu olduğu için size=384 yaptık)
if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

# 4. Metinleri Vektöre Çevir ve Yükle
documents = [
    {"id": 1, "text": "Yapay zeka geleceği şekillendiriyor.", "cat": "tech"},
    {"id": 2, "text": "Doğayı çok severim.", "natural": "environment"},
    {"id": 3, "text": "Veri bilimi öğrenmek çok heyecan verici.", "cat": "education"},
    {"id": 4, "text": "Çam ormanlarının arasındaki patikalarda yürümek ruhu dinlendirir.", "cat": "nature"},
    {"id": 5, "text": "Masmavi suların kıyıya vurduğu ıssız kumsallar huzur veriyor.",    "cat": "nature" },
]

points = []
for doc in documents:
    vector = model.encode(doc["text"]).tolist() # Metni vektöre çeviriyoruz
    points.append(PointStruct(id=doc["id"], vector=vector, payload=doc))

client.upsert(collection_name=collection_name, points=points)

# 5. ARAMA YAP
#query_text = "Teknoloji dünyasındaki gelişmeler"
query_text = "Tatil rotası önerisi"
query_vector = model.encode(query_text).tolist()

results = client.query_points(
    collection_name=collection_name,
    query=query_vector,
    limit=1
).points

print(f"Sorgu: {query_text}")
for res in results:
    print(f"En Yakın Sonuç: {res.payload['text']} (Skor: {res.score:.4f})")