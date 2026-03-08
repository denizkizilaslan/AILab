from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. Bağlantı
client = QdrantClient(host="localhost", port=6333)
collection_name = "deneme_koleksiyonu"

# 2. Koleksiyon Oluşturma
if not client.collection_exists(collection_name=collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    print(f"'{collection_name}' sıfırdan oluşturuldu.")
else:
    print(f"'{collection_name}' zaten var, mevcut olan kullanılıyor.")

# 3. Veri Yükleme (Upsert)
client.upsert(
    collection_name=collection_name,
    points=[
        PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"city": "Istanbul"}),
        PointStruct(id=2, vector=[0.9, 0.8, 0.7, 0.6], payload={"city": "Ankara"}),
    ],
)
print("Veriler başarıyla yüklendi!")

# 4. Arama
response = client.query_points(
    collection_name=collection_name,
    query=[0.1, 0.2, 0.3, 0.4], # Sorgu vektörümüz
    limit=2
)

print("Arama Sonuçları:")
for res in response.points:
    print(f"ID: {res.id}, Skor: {res.score}, Payload: {res.payload}")