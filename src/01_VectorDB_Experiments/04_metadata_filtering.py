import random
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range
from sentence_transformers import SentenceTransformer
from qdrant_client.models import OrderBy

# 1. Qdrant'a Bağlan
print("--- AILab: Büyük Arşiv Filtreleme Deneyi Başlıyor ---")
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)
collection_name = "ailab_archive"

# Koleksiyonu sıfırdan kuralım
if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)


# 2. 200 Adet Rastgele Belge Üretiyoruz
def create_documents(count=200):
    depts = ["Ar-Ge", "İK", "Finans", "Pazarlama", "Hukuk"]
    tips = ["pdf", "docx", "xlsx"]
    topics = ["Yapay Zeka", "Bütçe", "Siber Güvenlik", "Pazar Analizi", "Sürdürülebilirlik"]

    archive = []
    for i in range(1, count + 1):
        year = random.randint(2020, 2026)
        topic = random.choice(topics)
        doc = {
            "id": i,
            "text": f"{year} Yılı {topic} Raporu",
            "metadata": {
                "dept": random.choice(depts),
                "yil": year,
                "gizlilik": random.randint(1, 10),  # 10 en gizli
                "tip": random.choice(tips)
            }
        }
        archive.append(doc)
    return archive


documents = create_documents(100)

# 3.Payload ile Verileri Vektörleştirme ve Qdrant'a Yükleme
points = []
for doc in documents:
    vector = model.encode(doc["text"]).tolist()
    # Hem metni hem metadatayı 'payload' içine koyuyoruz
    payload = {**doc["metadata"], "text": doc["text"]}
    points.append(PointStruct(id=doc["id"], vector=vector, payload=payload))

client.upsert(collection_name=collection_name, points=points)
print(f"{len(documents)} adet belge başarıyla yüklendi!")


# 4.Filtreli Hibrit Arama | Filtered Vector Search
# Senaryo: "Siber güvenlik hakkında bir şeyler bul ama sadece Ar-Ge departmanının 2023 ve sonrası belgeleri olsun."
# Burada Qdrant'a şunu diyorsun: "Bana kelime kelime 'siber' veya 'güvenlik' geçenleri değil, anlam olarak siber güvenlik ve ağ korumasına en yakın olan belgeleri getir.
# Sistem bu cümleyi bir sayı dizisine (vektör) çeviriyor ve uzaydaki yerini belirliyor.
query_text = "Siber güvenlik ve ağ koruması"
query_vector = model.encode(query_text).tolist()

#query_filter: Qdrant milyarlarca veriyi tarayabilir ama biz ona bazı "gümrük şartları" koşuyoruz.
# Bu şartları sağlamayanlar, anlamsal olarak ne kadar yakın olurlarsa olsunlar kapıdan içeri giremiyorlar.
# Pre-filtering : Qdrant bu filtreleri "arama bittikten sonra" değil, "arama yaparken" uygular.
# Yani şartı sağlamayanlar daha en baştan elendiği için hızdan ödün verilmez
results = client.query_points(
    collection_name=collection_name,
    query=query_vector,
    query_filter=Filter(
        # must bloğu içindeki her şey, SQL'deki AND operatörü gibidir
        must=[
            # Sadece Ar-Ge departmanına ait belgeleri getir.
            FieldCondition(key="dept", match=MatchValue(value="Ar-Ge")),
            # Bana güncel veriler lazım eski arşivlere bakma.
            FieldCondition(key="yil", range=Range(gte=2023)),  # Greater than or equal 2023
            # Gizlilik seviyesi 8, 9 ve 10 olanlar 'Çok Gizli' belgelerdir. Benim yetkim sadece 8'den küçüklere (1-7 arası) yetiyor, onları filtrele
            FieldCondition(key="gizlilik", range=Range(lt=8))  # Gizliliği 8'den az olanlar (Yetki kısıtı)
        ]
    ),
    limit=5
).points

advanced_results = client.query_points(
    collection_name=collection_name,
    query=query_vector,
    query_filter=Filter(
        must=[
            FieldCondition(key="yil", range=Range(gte=2023)),  # 2023 ve sonrası zorunlu
        ],
        should=[
            FieldCondition(key="dept", match=MatchValue(value="Ar-Ge")), # Ar-Ge ise öncelik ver
            FieldCondition(key="oncelik", match=MatchValue(value="kritik")) # Kritikse öncelik ver
        ],
        must_not=[
            FieldCondition(key="tip", match=MatchValue(value="xlsx")), # Excel'leri gösterme
            FieldCondition(key="gizlilik", range=Range(gte=9)) # Çok gizlileri (9-10) sakın getirme
        ]
    ),
    limit=5
).points


# 5. Sonuçları İnceleme
print(f"Sorgu: '{query_text}' (Filtre: Ar-Ge + 2023+ + Yetki: <8)")
print("-" * 50)
if not advanced_results:
    print("Kriterlere uygun belge bulunamadı. Filtreleri esnetmeyi deneyin!")
else:
    for res in advanced_results:
        p = res.payload
        print(f"[*] Skor: {res.score:.4f} | Belge: {p['text']}")
        print(f"    Detay: {p['dept']} | {p['yil']} | Gizlilik: {p['gizlilik']} | Tip: {p['tip']}\n")