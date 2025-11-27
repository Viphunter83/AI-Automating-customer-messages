# 🌐 Создание Railway Domain (Public URL)

**Дата:** 2025-11-27

---

## ✅ Проблема

На Hobby плане Railway **не создает публичный URL автоматически**. Нужно создать домен вручную.

---

## 🔍 Как создать Railway Domain

### Способ 1: Через Railway Dashboard (Рекомендуется)

1. **Откройте Railway Dashboard:**
   - https://railway.com/project/4d2e02dc-89b3-4d70-9fed-13ee99bce07a

2. **Откройте сервис приложения:**
   - Нажмите на **AI-Automating-customer-messages** (не PostgreSQL!)

3. **Найдите раздел Networking:**
   - В верхней части страницы найдите вкладку **Networking**
   - Или в боковом меню найдите **Networking** / **Domains**

4. **Создайте домен:**
   - Найдите кнопку **Generate Domain** или **Create Domain**
   - Нажмите на неё
   - Railway создаст URL вида: `https://your-app-name.up.railway.app`

### Способ 2: Через Railway CLI

Если у вас установлен Railway CLI:

```bash
# Авторизация (если еще не авторизованы)
railway login

# Переход в проект
cd "/Users/apple/AI Automating customer messages"
railway link

# Создание домена
railway domain
```

### Способ 3: Через Railway API

Если у вас есть Railway API токен:

```bash
# Получить список доменов
curl -H "Authorization: Bearer YOUR_RAILWAY_TOKEN" \
  https://api.railway.app/v1/services/59527d4f-17ea-420b-b611-163e1a24dbe3/domains

# Создать домен
curl -X POST \
  -H "Authorization: Bearer YOUR_RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"serviceId": "59527d4f-17ea-420b-b611-163e1a24dbe3"}' \
  https://api.railway.app/v1/services/59527d4f-17ea-420b-b611-163e1a24dbe3/domains
```

---

## 📋 После создания домена

**Пришлите Railway URL**, и я выполню:

1. ✅ Тестирование `/health` и `/health/full`
2. ✅ Тестирование создания сообщения
3. ✅ Настройка фронтенда для подключения к Railway
4. ✅ Деплой фронтенда на Vercel через MCP

---

## 🚀 Готовый скрипт для тестирования

После получения URL:

```bash
cd "/Users/apple/AI Automating customer messages"
chmod +x test_railway_api.sh
./test_railway_api.sh https://your-app-name.up.railway.app
```

---

**Пришлите Railway URL после создания домена!** 🚀

