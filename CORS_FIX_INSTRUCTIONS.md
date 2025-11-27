# 🔧 Инструкция: Исправление CORS

**Дата:** 2025-11-27  
**Проблема:** Фронтенд показывает "Backend is not available ❌"

---

## 🔍 Причина

Фронтенд на Vercel не может подключиться к Railway API из-за CORS политики. Vercel URL не добавлен в `allowed_origins`.

---

## ✅ Решение

### Способ 1: Через Railway Dashboard (Рекомендуется)

1. **Откройте Railway Dashboard:**
   - https://railway.com/project/4d2e02dc-89b3-4d70-9fed-13ee99bce07a

2. **Откройте сервис приложения:**
   - Нажмите на **AI-Automating-customer-messages**

3. **Перейдите в Variables:**
   - В верхней части страницы найдите вкладку **Variables**

4. **Добавьте переменную:**
   - Нажмите **+ New Variable**
   - **Key:** `ALLOWED_ORIGINS`
   - **Value:** `https://frontend-qawc41iml-olegs-projects-d32cda90.vercel.app,https://*.vercel.app,http://localhost:3000,http://localhost:8000`
   - Нажмите **Add**

5. **Перезапустите сервис:**
   - Railway автоматически перезапустит сервис
   - Или перейдите в **Deployments** → **Redeploy**

### Способ 2: Через Railway CLI

```bash
cd "/Users/apple/AI Automating customer messages "
railway login
railway link
railway variables set ALLOWED_ORIGINS="https://frontend-qawc41iml-olegs-projects-d32cda90.vercel.app,https://*.vercel.app,http://localhost:3000,http://localhost:8000"
```

---

## 🔍 Проверка

После добавления переменной:

1. **Дождитесь перезапуска сервиса** (1-2 минуты)

2. **Обновите страницу фронтенда:**
   - https://frontend-qawc41iml-olegs-projects-d32cda90.vercel.app/?_vercel_share=EnXUyqTopQQdPmwuUCT5FCHmxVUw1hGX

3. **Проверьте статус:**
   - Должно показать "Backend is available ✅"
   - Консоль браузера (F12) не должна показывать CORS ошибки

---

## 📋 Значение переменной

```
ALLOWED_ORIGINS=https://frontend-qawc41iml-olegs-projects-d32cda90.vercel.app,https://*.vercel.app,http://localhost:3000,http://localhost:8000
```

**Включает:**
- ✅ Production Vercel URL
- ✅ Все Vercel preview URLs (`*.vercel.app`)
- ✅ Локальная разработка (`localhost:3000`, `localhost:8000`)

---

**После добавления переменной фронтенд будет работать полностью!** 🚀

