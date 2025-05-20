# DNS Proxy Suite

## Struktur
- **dns_proxy/server/**: DNS Proxy Server (blocking, safesearch, ACL)
- **dns_proxy/blacklist_updater/**: Update & sinkronisasi database blacklist domain dari sumber eksternal
- **dns_proxy/log_parser/**: Parser & API statistik log DNS untuk dashboard

## Cara Menjalankan

### 1. DNS Proxy Server
```bash
python main.py
```

### 2. Update Blacklist
```bash
python update_blacklist_db.py
```

### 3. Log Parser & API Dashboard
```bash
python parse_dns_log.py
# Akses API di http://localhost:8000/
```

## Kebutuhan
- Python 3.x
- Lihat `requirements.txt` untuk dependensi

---

**Struktur, modularitas, dan maintainability sudah diutamakan.**