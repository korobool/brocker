### 0.0 Ознакомление
```
    GET /home
```
### 1.0 Вход
```
    POST /login
    data: {“login”: “login”, “pwd”: “password”}
```
### 1.1 Регистрация
```
    POST /register
    data: {“login”: “login”, “pwd”: “password”}
```
### 1.0.1 Восстановление пароля
```
    POST /login/reminder
    data: {“email”: “email@email.com”}
```

### 2.0 Список приложений
```
    GET /apps
    response: [...] // list of apps
    ??? /install
    ??? /share
```

### 2.1 Фильтр
    Cache instead of requests

### H3 3.0 Профиль
```
    GET /apps/profile?id=app-123-456
    data: {“id”: “app-123-456”}
```
### H3 4.0 Топ приложений
```
    GET /apps/top
    [{"id": 123, "desc": "", "price": "$2"}, ...]
```
    ??? /install
    ??? /share

### 4.1 Детально приложение
```
    GET /apps/details?id=app-123-456
    In: {“id”: “app-123-456”}
    Out: {"name": "appName", "desc": "", "price": "$2.26"}
```
    ??? /install
    ??? /share

### H3 5 Топ Вебмастеров
```
    GET /apps/webmasters
    Out: [{"name": "Name", "rate": 190}, ...]
```

### 6.0 Настройки
    ??? /settings
### H3 7.0 Профиль
    ??? /account

### 8.0 Вывод
```
    POST /withdraw
    data: {“type”: “webmoney”, “country”: “UA”}
```
### 8.1 Подтверждение номера тел.
```
    POST /phone/confirm
    data: {"phone": "+380505552233"}
```
    Need some short message service
    
### 8.1.1 Выбор страны
    Consumption: The correspondance list is stored in app locally.

### 8.2 Выбор страны

### 8.3 Выбор метода вывода
```
    GET /withdraw/types
```

### 9.0 Расскажи…
```
    POST /shorten
    data: {"appId": "app-123", ...}
    ??? /share
```
### 9.1 Список контактов и приложений
```
    POST /contacts
```
    Do we need refresh?

### 10.0 Уведомления
```
    GET /notifications (/alerts, /news, /feed)
```

### 11.0 Меню
```
    GET /account
    GET /notifications
    GET /payments
    GET /support
    GET /help
    GET /settings
    GET /share
```
