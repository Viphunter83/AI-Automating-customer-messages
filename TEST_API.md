# 🧪 Тестирование API Railway

**Дата:** 2025-11-27

---

## 📋 Шаги тестирования

1. Получить Railway URL приложения
2. Протестировать health endpoints
3. Протестировать создание сообщения
4. Настроить фронтенд

---

## 🔍 Получение Railway URL

Railway URL можно найти в:
- Railway Dashboard → Сервис приложения → Settings → Domains
- Или в Deploy Logs

**Формат:** `https://your-app-name.up.railway.app` или `https://your-app-name.railway.app`

---

## ✅ Тестирование endpoints

### 1. Health Check

```bash
curl https://YOUR_RAILWAY_URL/health
```

### 2. Full Health Check

```bash
curl https://YOUR_RAILWAY_URL/health/full
```

### 3. Создание сообщения

```bash
curl -X POST https://YOUR_RAILWAY_URL/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test_client_123",
    "content": "Привет! Мне нужна помощь"
  }'
```

---

**После получения Railway URL выполним тесты!**

