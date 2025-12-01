# 🐛 Исправление: Утечка памяти в таймерах

**Дата:** 2025-11-27  
**Файл:** `frontend/app/demo/page.tsx`

---

## 🔍 Проблема

В функции `sendMockMessage` таймер создавался на строке 51, но сохранялся в `timerRefs` только на строке 60. Если между этими строками происходила ошибка (например, в `queryClient.invalidateQueries`), таймер терялся и не мог быть очищен.

**Сценарий проблемы:**
1. Таймер создается: `const timer = setTimeout(...)`
2. Происходит ошибка в `queryClient.invalidateQueries`
3. Выполнение переходит в блок `catch`
4. Таймер не сохранен в `timerRefs`, поэтому не может быть очищен
5. Таймер все равно выполнится через 2 секунды, но не будет отслеживаться
6. **Результат:** Утечка памяти и потенциальные проблемы с состоянием UI

---

## ✅ Решение

### 1. Сохранение таймера сразу после создания

Таймер теперь сохраняется в `timerRefs` сразу после создания, до выполнения других операций:

```typescript
timer = setTimeout(() => {
  // ...
}, 2000)

// Store timer reference immediately to ensure it can be cleaned up
timerRefs.current.set(message.id, timer)
```

### 2. Локальная переменная для отслеживания таймера

Добавлена локальная переменная `timer` в начале блока `try`, чтобы отслеживать созданный таймер:

```typescript
let timer: NodeJS.Timeout | null = null

try {
  // ... operations ...
  
  timer = setTimeout(() => {
    // ...
  }, 2000)
  
  timerRefs.current.set(message.id, timer)
}
```

### 3. Улучшенная очистка в блоке catch

В блоке `catch` теперь проверяются оба места - локальная переменная и ref:

```typescript
catch (error: any) {
  // ... error handling ...
  
  // Clear timer if exists (check both local timer and ref)
  if (timer) {
    clearTimeout(timer)
    timerRefs.current.delete(message.id)
  } else {
    // Fallback: check ref in case timer was created but variable wasn't set
    const existingTimer = timerRefs.current.get(message.id)
    if (existingTimer) {
      clearTimeout(existingTimer)
      timerRefs.current.delete(message.id)
    }
  }
}
```

---

## 📝 Изменения

### До:
```typescript
try {
  // ... operations ...
  
  const timer = setTimeout(() => {
    // ...
  }, 2000)
  
  timerRefs.current.set(message.id, timer) // Timer saved here, but error could occur before this
}
```

### После:
```typescript
let timer: NodeJS.Timeout | null = null

try {
  // ... operations ...
  
  timer = setTimeout(() => {
    // ...
  }, 2000)
  
  // Store timer reference immediately to ensure it can be cleaned up
  timerRefs.current.set(message.id, timer) // Timer saved immediately after creation
}
catch (error: any) {
  // ... error handling ...
  
  // Clear timer if exists (check both local timer and ref)
  if (timer) {
    clearTimeout(timer)
    timerRefs.current.delete(message.id)
  } else {
    // Fallback check
    const existingTimer = timerRefs.current.get(message.id)
    if (existingTimer) {
      clearTimeout(existingTimer)
      timerRefs.current.delete(message.id)
    }
  }
}
```

---

## ✅ Преимущества решения

1. **Нет утечек памяти:** Таймер всегда отслеживается и может быть очищен
2. **Безопасная обработка ошибок:** Таймер очищается даже при ошибках
3. **Двойная проверка:** Проверяются и локальная переменная, и ref для надежности
4. **Корректная очистка:** `useEffect` cleanup может очистить все таймеры при размонтировании

---

## ✅ Проверка

- ✅ TypeScript проверка типов: Успешно
- ✅ Линтер: Нет ошибок
- ✅ Утечка памяти исправлена
- ✅ Таймеры правильно отслеживаются и очищаются

---

## 🎯 Результат

Теперь:
- ✅ Таймеры всегда отслеживаются в `timerRefs`
- ✅ Нет утечек памяти при ошибках
- ✅ Таймеры правильно очищаются в блоке catch
- ✅ Cleanup в `useEffect` может очистить все таймеры
- ✅ Состояние UI остается корректным даже при ошибках

---

**Исправление применено успешно!** ✅

