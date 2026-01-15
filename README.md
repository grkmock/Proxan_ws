# Proxan Reservation System Backend

Bu proje, yüksek trafikli bir etkinlik platformu için tasarlanmış **Çift Aşamalı Rezervasyon Sistemi** (Hold & Confirm) backend servisidir. Proje; veri tutarlılığı, eşzamanlılık (concurrency) yönetimi ve otomatik kapasite iadesi süreçlerini kapsar.

## 🛠 Teknik Mimari

- **Framework:** FastAPI (Asenkron yapı)
- **Veritabanı & ORM:** PostgreSQL & SQLAlchemy
- **İşlem Yönetimi:** `SELECT FOR UPDATE` ile veritabanı seviyesinde kilitleme (Row-level Locking)
- **Arka Plan Görevleri:** `APScheduler` (Süresi dolan hold kayıtlarının temizlenmesi için)
- **Test:** Pytest (Asenkron Entegrasyon ve Unit testleri)
- **Güvenlik:** JWT tabanlı kimlik doğrulama (Auth)

---

## 📂 Proje Yapısı

```text
Proxan_ws/
├── app/
│   ├── main.py              # Uygulama giriş noktası ve Scheduler başlatma
│   ├── models.py            # SQLAlchemy veritabanı modelleri
│   ├── schemas.py           # Pydantic şemaları (Request/Response)
│   ├── db.py                # Veritabanı bağlantı ayarları
│   ├── tasks.py             # Background job: Süresi dolan kayıtları temizleme
│   └── routers/             # API Endpoint'leri (Auth, Events, Reservations)
├── tests/
│   ├── conftest.py          # Test fixture'ları ve Mock DB ayarları
│   └── ...                  # Entegrasyon ve senaryo testleri
├── requirements.txt         # Bağımlılık listesi
└── README.md                # Kurulum ve kullanım kılavuzu

```
---

## ⚙️ Çekirdek Mantık ve Eşzamanlılık Yönetimi

Sistem, teknik mülakat kriterlerinde ve PDF dokümanında belirtilen kritik gereksinimleri karşılamak adına şu yaklaşımları kararlı bir şekilde uygular:

### 1. Database Level Locking (Eşzamanlılık Yönetimi)
Rezervasyon oluşturma (`HOLD`) aşamasında, aynı etkinliğe aynı anda gelen çok sayıda talebin kapasiteyi eksiye düşürmemesi (overselling) için SQLAlchemy üzerinden **`with_for_update()`** (SELECT FOR UPDATE) kullanılmıştır. 
- Bu yöntem, ilgili etkinlik satırını işlem (transaction) bitene kadar kilitler.
- Diğer talepler sıraya alınır ve kapasite kontrolü her zaman en güncel veri üzerinden yapılır.
- Böylece yarış durumu (race condition) hataları tamamen engellenmiş olur.

### 2. Çift Aşamalı Onay Süreci (Double-Phase Commit)
- **Aşama 1 (HOLD):** Kullanıcı bir yer ayırttığında, kapasite geçici olarak düşürülür ve veritabanında 5 dakikalık bir `expires_at` süresiyle "HOLD" statüsünde bir kayıt oluşturulur.
- **Aşama 2 (CONFIRM):** Kullanıcı 5 dakika içinde `/confirm` endpoint'ine istek atarsa, kayıt statüsü "CONFIRMED" olarak güncellenir ve kapasite kalıcı olarak eksiltilmiş olur.

### 3. Otomatik Kapasite İadesi (Background Job)
`APScheduler` kütüphanesi kullanılarak uygulama içerisinde her 1 dakikada bir çalışan bir temizlik görevi (`cleanup_expired_holds`) kurgulanmıştır:
- **Tespit:** `state == 'HOLD'` olan ve `expires_at` zamanı geçmiş olan tüm kayıtlar taranır.
- **İptal:** Süresi dolan kayıtlar veritabanından silinir.
- **İade:** Silinen her bir geçersiz rezervasyon için ilgili etkinliğin `available_capacity` değeri otomatik olarak arttırılarak kapasite sisteme geri kazandırılır.

## 🚀 Kurulum ve Çalıştırma Rehberi

Projeyi yerel ortamınızda veya farklı bir bilgisayarda sorunsuz çalıştırmak için aşağıdaki adımları sırasıyla takip edin:

### 1. Projeyi Hazırlama
Öncelikle kaynak kodları yerel makinenize indirin ve proje klasörüne gidin:
```bash
git clone <repository-url>
cd Proxan_ws
```
### 2. Sanal Ortam (Virtual Environment) Oluşturma
Bağımlılıkların sistem genelindeki diğer Python paketleriyle çakışmaması için izole bir ortam oluşturun ve aktif edin:

**Windows (PowerShell veya CMD) için:**
```powershell
# Sanal ortamı oluştur
python -m venv .venv

# Ortamı aktif et
.\.venv\Scripts\activate
```
### 3. Bağımlılıkların Yüklenmesi
Projenin çalışması için gerekli olan tüm kütüphaneleri (FastAPI, SQLAlchemy, APScheduler ve Test araçları) `requirements.txt` dosyasını kullanarak yükleyin:

```bash
# pip aracını güncelleyin (opsiyonel ama önerilir)
pip install --upgrade pip

# Tüm bağımlılıkları tek seferde yükleyin
pip install -r requirements.txt
```
### 4. Uygulamayı Başlatma
Bağımlılıklar yüklendikten sonra, API sunucusunu başlatmak için aşağıdaki komutu kullanın. Uygulama başlatıldığında **Background Scheduler** (Arka Plan Görevi) otomatik olarak devreye girecek ve süresi dolan kayıtları temizlemeye başlayacaktır:

```bash
uvicorn app.main:app --reload
```
### 5. Testlerin Koşturulması
Projenin tüm iş mantığını (Business Logic), eşzamanlılık (concurrency) güvenliğini ve arka plan görevlerinin (background job) entegrasyonunu doğrulamak için testleri çalıştırın. 

> **Not:** Testler **SQLite In-Memory** veritabanı kullandığı için herhangi bir harici veritabanı kurulumu veya yapılandırması gerektirmez; her test koşturulduğunda veritabanı sıfırdan oluşturulur ve temizlenir.

**Windows (PowerShell) için:**
```powershell
# PYTHONPATH ayarıyla 'app' modülünün bulunmasını sağlayın
$env:PYTHONPATH = "."
.venv\Scripts\pytest -v
```
## 🚦 API Uç Noktaları (Endpoints)

Uygulama ayağa kalktığında tüm uç noktalara ve şema detaylarına **Swagger UI** üzerinden erişilebilir: `http://127.0.0.1:8000/docs`

### 🔐 Kimlik Doğrulama (Auth)
| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/auth/register` | Yeni kullanıcı kaydı oluşturur. |
| `POST` | `/auth/token` | Kullanıcı girişi yapar ve JWT access token döner. |

### 📅 Etkinlik Yönetimi (Events)
| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/events/` | **Admin:** Yeni etkinlik ve başlangıç kapasitesi oluşturur. |
| `GET` | `/events/{id}` | Etkinliğin kalan kapasitesini, aktif HOLD ve CONFIRMED sayılarını döner. |
| `GET` | `/events/` | Tüm aktif etkinlikleri listeler. |

### 🎟 Rezervasyon Süreci (Reservations)
| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/reservations/hold` | Belirli bir etkinlik için 5 dakikalık geçici yer ayırır (HOLD). |
| `POST` | `/reservations/confirm/{id}` | HOLD statüsündeki rezervasyonu kesinleştirir (CONFIRMED). |
| `GET` | `/reservations/my` | Giriş yapmış kullanıcının kendi rezervasyon geçmişini listeler. |

---

> **İpucu:** Rezervasyon uç noktaları JWT Token gerektirir. Swagger arayüzündeki **"Authorize"** butonu üzerinden token ekleyerek test yapabilirsiniz.