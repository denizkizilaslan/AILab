from qdrant_client import QdrantClient

# 1. Qdrant'a Bağlan
client = QdrantClient(host="localhost", port=6333)
collection_name = "ailab_archive"

print("--- AILab: Pagination & Scrolling Lab ---")

# --- NEDEN SAYFALAMA YAPIYORUZ? ---
# Bir Google araması düşünün; size 1 milyon sonuç bulur ama sadece ilk 10'unu gösterir.
# Bu hem internet trafiğini korur hem de uygulamanın takılmasını engeller.

# 2. YÖNTEM A: Basit Sayfalama (Limit & Offset)
# SQL: SELECT * FROM archive LIMIT 5 OFFSET 10
# (10 kayıt atla, sonraki 5 kaydı getir = Sayfa 3)
print("\n[A] BASİT SAYFALAMA: 10. kayıttan sonraki 5 belge getiriliyor...")
page_results, next_page_offset = client.scroll(
    collection_name=collection_name,
    limit=5,          # Kaç kayıt gelsin?
    offset=10,         # Kaç kayıt atlasın?
    with_payload=True, # Metadata gelsin mi?
    with_vectors=False # Vektörler gelmesin (Hız kazandırır)
)

for i, point in enumerate(page_results):
    print(f" -> {i+11}. Kayıt ID: {point.id} | Başlık: {point.payload['text'][:30]}...")

# 3. YÖNTEM B: Akıllı Kaydırma (Scrolling / Cursor)
# Problem: Offset değeri çok büyürse (örn: 1.000.000), veritabanı yavaşlar.
# Çözüm: Qdrant'ın döndürdüğü 'next_page_offset' (bir nevi ayraç) kullanılır.
print("[B] AKILLI SCROLLING: Kaldığımız yerden devam ediyoruz...")
# İlk sayfa için offset vermiyoruz (veya 0 veriyoruz)
first_batch, next_offset = client.scroll(
    collection_name=collection_name,
    limit=3,
    with_payload=True
)
print(f"İlk 3 kayıt alındı. Bir sonraki sayfa anahtarı: {next_offset}")

# Bu 'next_offset' değerini bir sonraki sorguda 'offset' yerine yazarsan
# veritabanı kaldığı yeri hatırlar ve çok daha hızlı devam eder.
# İkinci sayfa için 'next_offset' değerini kullanıyoruz
if next_offset is not None:
    second_batch, _ = client.scroll(
        collection_name=collection_name,
        limit=3,
        offset=next_offset # Bir önceki sorgudan gelen anahtarı buraya koyduk
    )
    print(f"İkinci sayfa başarıyla yüklendi. (Hızlı ve verimli geçiş)")

    for i, point in enumerate(second_batch):
        print(f" -> {i + 11}. Kayıt ID: {point.id} | Başlık: {point.payload['text'][:30]}...")