# 🧪 Полное руководство по тестированию и настройке

**Дата:** 2025-11-27

---

## 📋 План действий

### 1. ✅ Получить Railway URL

**Где найти:**
- Railway Dashboard → Сервис приложения → Settings → Domains
- Или в Deploy Logs

**Формат:** `https://your-app-name.up.railway.app`

---

### 2. 🧪 Протестировать API

#### Health Check
```bash
curl https://YOUR_RAILWAY_URL/health
```

**Ожидаемый ответ:**
```json
{"status": "healthy", "database": "connected"}
```

#### Full Health Check
```bash
curl https://YOUR_RAILWAY_URL/health/full
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "database": {"status": "connected", ...},
  "openai": {"status": "connected", ...},
  "webhook": {...},
  "scheduler": {...}
}
```

#### Создание сообщения
```bash
curl -X POST https://YOUR_RAILWAY_URL/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test_client_123",
    "content": "Привет! Мне нужна помощь с настройкой"
  }'
```

**Ожидаемый ответ:**
```json
{
  "status": "success",
  "original_message_id": "...",
  "is_first_message": true,
  "priority": "low",
  "classification": {...},
  "response": {...}
}
```

---

### 3. 🚀 Настроить фронтенд для Vercel

#### Шаг 1: Создать .env.production.local

```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=https://YOUR_RAILWAY_URL" > .env.production.local
```

#### Шаг 2: Деплой на Vercel

```bash
cd frontend
vercel
```

Или через MCP:
- Используйте `mcp_Vercel_deploy_to_vercel` для деплоя

#### Шаг 3: Настроить переменные в Vercel Dashboard

1. Vercel Dashboard → Проект → Settings → Environment Variables
2. Добавьте:
   ```
   NEXT_PUBLIC_API_URL = https://YOUR_RAILWAY_URL
   ```
3. Выберите окружения: ✅ Production, ✅ Preview, ✅ Development

---

## ✅ Чеклист

- [ ] Railway URL получен
- [ ] Health endpoints протестированы
- [ ] Создание сообщения протестировано
- [ ] Фронтенд задеплоен на Vercel
- [ ] Переменные окружения настроены в Vercel
- [ ] Фронтенд подключен к Railway API
- [ ] Все работает!

---

**После получения Railway URL выполним все шаги!** 🚀

