# 🚀 Paikallinen Suoritus - Local Execution Guide

## Nopea Käynnistys

### 1. Käynnistä kaikki palvelut:
```bash
./start_local.sh
```

### 2. Pysäytä kaikki palvelut:
```bash
./stop_local.sh
```

---

## Palvelut ja Portit

| Palvelu | Portti | URL | Status |
|---------|--------|-----|--------|
| **Main API** | 8000 | http://localhost:8000 | ✅ |
| **Lock Security** | 8001 | http://localhost:8001 | ✅ |
| **Emissions Testing** | 8002 | http://localhost:8002 | ✅ |
| **Pre-Sale Inspection** | 8003 | http://localhost:8003 | ✅ |

---

## Testaus

### Testaa API:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/
curl http://localhost:8000/docs
```

### Testaa Lock Security:
```bash
curl http://localhost:8001/health
curl http://localhost:8001/test/vulnerable
curl http://localhost:8001/test/secure
```

### Testaa Emissions:
```bash
curl http://localhost:8002/health
```

### Testaa Pre-Sale:
```bash
curl http://localhost:8003/health
```

---

## Venice AI Testaus

```bash
python3 test_venice_ai.py
```

---

## Yksittäisten Palveluiden Käynnistys

### Main API:
```bash
cd api
source ../venv/bin/activate
uvicorn simple_main:app --host 0.0.0.0 --port 8000 --reload
```

### Lock Security:
```bash
cd lock-security-testing/backend
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Emissions Testing:
```bash
cd emissions-testing/backend
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### Pre-Sale Inspection:
```bash
cd pre-sale-inspection/backend
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

---

## Ongelmatilanteet

### Portti varattu:
```bash
# Etsi prosessi
lsof -i :8000

# Tapa prosessi
kill -9 <PID>
```

### Riippuvuudet puuttuu:
```bash
source venv/bin/activate
pip install -r api/requirements.txt
pip install -r lock-security-testing/backend/requirements.txt
pip install -r emissions-testing/backend/requirements.txt
pip install -r pre-sale-inspection/backend/requirements.txt
```

### Virtual environment puuttuu:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

---

## Logit

### API Logit:
```bash
tail -f api/logs/*.log
```

### Kaikki logit:
```bash
tail -f **/*.log
```

---

## Tila

### Tarkista käynnissä olevat palvelut:
```bash
ps aux | grep uvicorn
```

### Tarkista portit:
```bash
lsof -i :8000
lsof -i :8001
lsof -i :8002
lsof -i :8003
```

---

## API Dokumentaatio

Kun palvelut ovat käynnissä, avaa selaimessa:

- **Main API Docs**: http://localhost:8000/docs
- **Lock Security Docs**: http://localhost:8001/docs
- **Emissions Docs**: http://localhost:8002/docs
- **Pre-Sale Docs**: http://localhost:8003/docs

---

## Ympäristömuuttujat

Skripti asettaa automaattisesti:

```bash
VENICE_API_KEY=tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz
VENICE_BASE_URL=https://api.venice.ai/api/v1
VENICE_MODEL=venice-uncensored
DATABASE_URL=sqlite:///./local.db
DEBUG=true
LOG_LEVEL=INFO
```

---

## Seuraavat Askeleet

1. ✅ Käynnistä palvelut: `./start_local.sh`
2. ✅ Testaa yhteydet: `curl http://localhost:8000/health`
3. ✅ Avaa dokumentaatio: http://localhost:8000/docs
4. ✅ Testaa Venice AI: `python3 test_venice_ai.py`
5. ✅ Kehitä ja testaa paikallisesti

---

**✅ Kaikki valmiina paikalliseen suoritukseen!**

