# TG_bot_sсhedule-novsu
Телеграм бот для получения информации о расписании колледжей

## Как запустить бота
### 1. Необходимо наличие python и сторонних библиотек на вашем ПК
Для установки сторонних библотек: 
```
pip install <Название библиотеки>
```

### 2. Необходима база данных PostgreSQL
Нужно либо подключиться, либо создать свою. Создание баз данных находится в файле `Rebuild_Databases.sql`
Если база данных своя, то логин и пароль изменяете под свой перед подключением

### 3. Необходимо иметь ссылку на бота в тг, либо создать своего. 
Для создания необходим бот `@BotFather`, в котором создаём своего и получаем токен, который вставляем в код программы заместо текущего. 
