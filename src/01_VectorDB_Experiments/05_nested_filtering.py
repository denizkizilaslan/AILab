from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, PointStruct, VectorParams, Distance, NestedCondition
)
from sentence_transformers import SentenceTransformer

# 1. Qdrant'a Bağlan
client = QdrantClient(host="localhost", port=6333)
model = SentenceTransformer('all-MiniLM-L6-v2')
collection_name = "nested_archive"

# DROP TABLE IF EXISTS
if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# 2. Hiyerarşik (Nested) Veri Seti
# Burada her belgenin içinde 'onay_zinciri' adında bir liste (Array of Objects) var.
# SQL dünyasında bu, bir tablonun başka bir tabloyla bire-çok (one-to-many) ilişkisi gibidir.
documents = [
    {
        "id": 1,
        "text": "Yapay Zeka Etik Kullanım Kılavuzu",
        "metadata": {
            "onay_zinciri": [
                {"kisi": "Ahmet", "rol": "Müdür", "durum": "onaylandi"},
                {"kisi": "Mehmet", "rol": "CEO", "durum": "beklemede"}
            ],
            "dept": "Ar-Ge"
        }
    },
    {
        "id": 2,
        "text": "Bulut Altyapı Güvenlik Protokolü",
        "metadata": {
            "onay_zinciri": [
                {"kisi": "Ali", "rol": "Müdür", "durum": "onaylandi"},
                {"kisi": "Can", "rol": "CTO", "durum": "onaylandi"}
            ],
            "dept": "IT"
        }
    }
]

# Verileri Vektörleştirme ve Payload ile Yükleme
points = []
for doc in documents:
    vector = model.encode(doc["text"]).tolist()
    points.append(PointStruct(id=doc["id"], vector=vector, payload=doc["metadata"]))

client.upsert(collection_name=collection_name, points=points)
print("Hiyerarşik veriler yüklendi.")

# 3. KRİTİK NOKTA: Nested Condition (İç İçe Sorgu)
# PROBLEM: Sadece "Müdür olanı bul" ve "Onaylandı olanı bul" deseydik;
# Müdürün RED verdiği ama başka birinin ONAY verdiği belgeler de (ID: 2 gibi) yanlışlıkla gelirdi.
# ÇÖZÜM: NestedCondition kullanarak "Aynı obje içinde hem Müdür olsun hem de durumu Onaylandi olsun" diyoruz.
print("\n--- NESTED FILTERING: Müdür Onayı Almış Belgeler ---")

search_result = client.query_points(
    collection_name=collection_name,
    query=model.encode("güvenlik ve etik").tolist(),
    query_filter=Filter(
        must=[
            NestedCondition(
                key="onay_zinciri",
                filter=Filter(
                    must=[
                        FieldCondition(key="rol", match=MatchValue(value="Müdür")),
                        FieldCondition(key="durum", match=MatchValue(value="onaylandi"))
                    ]
                )
            )
        ]
    ),
    limit=5
).points

# Sonuçları Listeleme
if not search_result:
    print("Kriterlere uygun nested eşleşme bulunamadı.")
else:
    for res in search_result:
        print(f"[*] Eşleşen Belge ID: {res.id}")
        # Onay verenleri doğrulayalım
        for onay in res.payload['onay_zinciri']:
            print(f"    -> Yetkili: {onay['kisi']} | Rol: {onay['rol']} | Durum: {onay['durum']}")