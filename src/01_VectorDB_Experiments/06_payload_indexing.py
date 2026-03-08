from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

# 1. Qdrant'a Bağlan
client = QdrantClient(host="localhost", port=6333)
collection_name = "ailab_archive"

print("--- AILab: Payload Indexing ---")

# --- NEDEN INDEX YAPIYORUZ? ---
# SQL'deki 'Full Table Scan' kavramını hatırlayalım. Eğer index yoksa,
# veritabanı 1 milyon satırı tek tek gezer. Index varsa,
# aradığı değeri (örneğin 'Ar-Ge') bir sözlükten bulur gibi anında çeker.

# 2. KEYWORD INDEX (Metin Bazlı Filtreler İçin)
# SQL: CREATE INDEX idx_dept ON archive(dept)
# 'dept' gibi tam eşleşme (match) aradığımız alanlar için KEYWORD kullanılır.
client.create_payload_index(
    collection_name=collection_name,
    field_name="dept",
    field_schema=PayloadSchemaType.KEYWORD,
)
print("'dept' alanı için Keyword Index oluşturuldu. (Hızlı Departman Filtreleme)")

# 3. INTEGER INDEX (Sayısal Aralıklar İçin)
# SQL: CREATE INDEX idx_yil ON archive(yil)
# 'yil' gibi büyüktür/küçüktür (range) sorgusu yapacağımız alanlar için INTEGER kullanılır.
client.create_payload_index(
    collection_name=collection_name,
    field_name="yil",
    field_schema=PayloadSchemaType.INTEGER,
)
print("'yil' alanı için Integer Index oluşturuldu. (Hızlı Tarih Sorgulama)")

# 4. INDEX DURUMUNU KONTROL ETME
# Koleksiyonun detaylarına bakarak indexlerin başarıyla tanımlandığını doğrulayalım.
collection_info = client.get_collection(collection_name)
active_indexes = list(collection_info.payload_schema.keys())

print(f"Aktif Performans Indexleri: {active_indexes}")
print("Artık milyonlarca doküman arasında filtreleme yapmak sadece birkaç milisaniye sürecek.")