# 📤 Инструкции для push в Git

## ✅ Что уже сделано:

1. ✅ Все секреты удалены из кода
2. ✅ Большие файлы (tickets.json, training_dataset.json) исключены из коммита
3. ✅ Обновлен .gitignore для всех .env файлов
4. ✅ Коммит создан: `6aa2a90`
5. ✅ Remote добавлен: `zerocoder` → `https://github.com/zerocodertech/neiromatrius.git`

## 🔐 Настройка доступа к репозиторию

Для push в `zerocodertech/neiromatrius` нужна аутентификация. Выберите один из вариантов:

### Вариант 1: Personal Access Token (HTTPS)

1. Создайте Personal Access Token на GitHub:
   - Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token (classic)
   - Выберите scope: `repo` (полный доступ к репозиториям)
   - Скопируйте токен

2. Используйте токен для push:
```bash
git push https://YOUR_TOKEN@github.com/zerocodertech/neiromatrius.git main
```

Или настройте credential helper:
```bash
git remote set-url zerocoder https://YOUR_TOKEN@github.com/zerocodertech/neiromatrius.git
git push zerocoder main
```

### Вариант 2: SSH ключ

1. Проверьте наличие SSH ключа:
```bash
ls -la ~/.ssh/id_rsa.pub
```

2. Если ключа нет, создайте:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

3. Добавьте публичный ключ в GitHub:
   - Settings → SSH and GPG keys → New SSH key
   - Скопируйте содержимое `~/.ssh/id_rsa.pub`

4. Используйте SSH URL:
```bash
git remote set-url zerocoder git@github.com:zerocodertech/neiromatrius.git
git push zerocoder main
```

### Вариант 3: GitHub CLI

```bash
gh auth login
git push zerocoder main
```

## 📋 Текущий статус

- **Коммит:** `6aa2a90` - "Prepare for Dokploy deployment: update env configs, remove secrets, add service documentation, exclude large data files"
- **Remote:** `zerocoder` → `https://github.com/zerocodertech/neiromatrius.git`
- **Ветка:** `main`
- **Файлов в коммите:** 192 измененных файлов

## 🚀 После настройки доступа выполните:

```bash
git push zerocoder main
```

Или если хотите изменить origin:

```bash
git remote set-url origin https://github.com/zerocodertech/neiromatrius.git
git push origin main
```

