# 🚀 Быстрый старт: Деплой на Railway + Vercel

**Дата:** 2025-11-26

---

## ⚡ Быстрая инструкция

### 1. Railway (БД) - 5 минут

1. Зайдите на [railway.app](https://railway.app)
2. **New Project** → **Add PostgreSQL**
3. Скопируйте `DATABASE_URL` из Variables
4. Измените формат: `postgresql://` → `postgresql+asyncpg://`

### 2. Vercel (Backend) - 5 минут

```bash
# Инициализация
vercel

# Настройте переменные в Dashboard:
# - DATABASE_URL (из Railway)
# - OPENAI_API_KEY
# - SECRET_KEY

# Деплой
vercel --prod
```

### 3. Проверка

```bash
curl https://your-project.vercel.app/health
```

---

## 📚 Подробные инструкции

- `DEPLOYMENT_COMPLETE_GUIDE.md` - Полное руководство
- `STEP_BY_STEP_DEPLOY.md` - Пошаговая инструкция
- `RAILWAY_SETUP.md` - Настройка Railway
- `VERCEL_SETUP_GUIDE.md` - Настройка Vercel

---

## 🌐 Netlify vs Vercel

**Рекомендация:** Используйте **Vercel** для FastAPI бэкенда.

См. `NETLIFY_COMPARISON.md` для сравнения.

---

**Готово к деплою!** 🚀

