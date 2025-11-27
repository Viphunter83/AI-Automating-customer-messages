# 🚀 Исправление через Railway CLI

**Дата:** 2025-11-27  
**Способ:** Использование Railway CLI для добавления переменных

---

## ✅ Преимущества CLI

- Быстрее, чем через Dashboard
- Можно автоматизировать
- Меньше ошибок при копировании

---

## 📋 Шаги

### Шаг 1: Авторизация (если не авторизованы)

```bash
railway login
```

### Шаг 2: Выберите проект

```bash
railway link
```

Или если проект уже связан:
```bash
railway status
```

### Шаг 3: Получите DATABASE_URL из PostgreSQL

```bash
# Переключитесь на PostgreSQL сервис
railway service

# Выберите PostgreSQL сервис из списка
# Затем получите переменные:
railway variables
```

Скопируйте `DATABASE_URL` и измените формат:
```
postgresql://... → postgresql+asyncpg://...
```

### Шаг 4: Переключитесь на сервис приложения

```bash
railway service
# Выберите сервис приложения (не PostgreSQL!)
```

### Шаг 5: Добавьте переменные

```bash
# DATABASE_URL
railway variables set DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway"

# OPENAI_API_KEY (замените на ваш реальный ключ)
railway variables set OPENAI_API_KEY="sk-your-api-key-here"

# SECRET_KEY (замените на случайную строку минимум 32 символа)
railway variables set SECRET_KEY="your-secret-key-minimum-32-characters-long"
```

### Шаг 6: Проверьте переменные

```bash
railway variables
```

Должны быть видны:
- ✅ `DATABASE_URL`
- ✅ `OPENAI_API_KEY`
- ✅ `SECRET_KEY`

### Шаг 7: Перезапустите сервис

```bash
railway restart
```

Или через Dashboard: Settings → Restart Service

---

## 🔍 Альтернативный способ: Через файл

Создайте файл `.railway.env` в корне проекта:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway
OPENAI_API_KEY=sk-your-api-key-here
SECRET_KEY=your-secret-key-minimum-32-characters-long
```

Затем:
```bash
railway variables --file .railway.env
```

**⚠️ ВАЖНО:** Не коммитьте `.railway.env` в Git! Добавьте в `.gitignore`.

---

## ✅ Проверка

После добавления переменных:

1. Проверьте логи:
   ```bash
   railway logs
   ```

2. Проверьте health endpoint:
   ```bash
   curl https://your-project.railway.app/health
   ```

---

## 🎯 Быстрый способ (если знаете значения)

```bash
# 1. Авторизация
railway login

# 2. Связь с проектом
railway link

# 3. Выбор сервиса приложения
railway service

# 4. Добавление переменных (замените значения!)
railway variables set DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway"
railway variables set OPENAI_API_KEY="sk-your-api-key-here"
railway variables set SECRET_KEY="your-secret-key-minimum-32-characters-long"

# 5. Перезапуск
railway restart

# 6. Проверка
railway logs
```

---

**ГЛАВНОЕ:** Убедитесь, что вы в правильном сервисе (приложение, не PostgreSQL)! 🚀

