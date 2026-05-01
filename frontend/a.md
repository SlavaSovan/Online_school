# Файлы проекта
### Точка входа и сборка
<b>index.html</b> - Хост-файл. Vite использует его как точку входа, подставляя скрипты через <sсript type="module"> (главная страница, туда Vue сам всё вставит).  
<b>vite.config.ts</b> - Конфиг сборщика.	Настраивает плагины (@vitejs/plugin-vue), алиасы (@/), прокси, разделение чанков.  
<b>src/main.ts</b> - Клиентский энтрипоинт.	Создает экземпляр Vue (createApp), монтирует в #app, подключает роутер и стор. 

<b>index.html</b> — точка входа для браузера, <b>main.ts</b> — точка входа для Vue-приложения.

### Конфигурация окружения
<b>.editorconfig</b> - Базовые настройки редактора. Отступы, кодировка, перевод строк. Перебивает настройки IDE.  
<b>.gitattributes</b> - Нормализация CRLF/LF. Чтобы в Windows не ломались хеши при коммите.  
<b>.gitignore</b> - Исключения для Git. node_modules, dist, .env.local и т.д.  

### Линтинг и форматирование

<b>eslint.config.ts</b> - ESLint 9+ flat config. Проверяет логические ошибки и стиль кода. Для Vue использует eslint-plugin-vue.  
<b>.oxlintrc.json</b> - OxLint (Rust-линтер). Заменяет ESLint по производительности, но с меньшим количеством правил. Используется параллельно или вместо.  
<b>.prettierrc.json</b> - Форматтер. Отвечает только за расстановку скобок, кавычек, отступов.  

### TypeScript
<b>tsconfig.json</b> - Базовый конфиг, ссылается на остальные  
<b>tsconfig.app.json</b> - Для кода в src/ (строгие проверки, декораторы отключены)  
<b>tsconfig.node.json</b> - Для Node.js-файлов (vite.config.ts) — другая модульная система, другие типы  
<b>env.d.ts</b> - Расширение типов для import.meta.env (переменные Vite)  


# Будет использоваться

<b>src/</b> - Исходники  
<b>src/App.vue</b> - Корневой компонент. Тут <rоuter-view> или просто разметка  
<b>src/components/</b> - Переиспользуемые UI-блокию. Тут Button.vue, Modal.vue  
<b>src/views/ или src/pages/</b> - Страницы (если есть Router). Тут HomeView.vue, AboutView.vue  
<b>src/router/</b> - Конфиг маршрутов. Тут index.ts с createRouter()  
<b>src/stores/</b> - Хранилища Pinia. Тут userStore.ts, cartStore.ts  
<b>src/assets/</b> - Статика (CSS, изображения). Тут main.css, logo.png  
<b>public/</b> - Статика без обработки сборщиком. Тут favicon.ico, robots.txt

# Дополнительные библиотеки
<b>axios</b> - работа с API

# Команды
Установка зависимостей  
```
npm install
```

Запуск сервера.
```
npm run dev
```
