# 🔍 Как получить Railway URL

**Дата:** 2025-11-27

---

## 📋 Способ 1: Через Railway Dashboard

1. Откройте [Railway Dashboard](https://railway.app)
2. Выберите проект **AI-Automating-customer-messages**
3. Откройте сервис **ПРИЛОЖЕНИЯ** (не PostgreSQL!)
4. Перейдите на вкладку **Settings**
5. Найдите раздел **Domains** или **Networking**
6. Скопируйте URL (например: `https://your-app-name.up.railway.app`)

---

## 📋 Способ 2: Через Deploy Logs

1. Railway Dashboard → Сервис приложения
2. Откройте вкладку **Deployments** или **Logs**
3. Найдите строку с URL в логах запуска

---

## 📋 Способ 3: Через Railway CLI

```bash
railway status
```

Или:

```bash
railway domain
```

---

## 🧪 После получения URL

Выполните тестирование:

```bash
./test_railway_api.sh https://YOUR_RAILWAY_URL
```

Или вручную:

```bash
# Health check
curl https://YOUR_RAILWAY_URL/health

# Full health check
curl https://YOUR_RAILWAY_URL/health/full

# Create message
curl -X POST https://YOUR_RAILWAY_URL/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test_123", "content": "Привет!"}'
```

---

**После получения URL выполним тесты и настроим фронтенд!** 🚀

