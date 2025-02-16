# Описание
«Фудграм» — сайт, на котором пользователи публикуют свои рецепты, добавляют чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

[Пример сайта](https://foodgramgladdo.myftp.biz/recipes)

# Как установить / развернуть
#### Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/GladDmitry/foodgram.git
```

```
cd foodgram
```

#### Создать в корневой директории проекта файл .env и добавить следующие переменные:

##### Переменные которые необходимо указать в .env:
```
SECRET_KEY
DEBUG
ALLOWED_HOSTS
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
HOST
PORT
```

#### Запустить Docker Compose:

Под Windows:
```
docker compose docker-compose.production.yml up
```

Под Linux:
```
sudo docker compose -f docker-compose.production.yml up -d
```

#### Выполнить миграции:

Под Windows:
```
docker compose docker-compose.production.yml exec backend python manage.py migrate

docker compose docker-compose.production.yml exec backend python manage.py collectstatic

docker compose docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

Под Linux:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate

sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic

sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

# Технологии
* Django
* Django REST Framework
* Docker
* Nginx
* PostgreSQL

# Автор
[Гладилин Дмитрий Олегович](https://github.com/GladDmitry)
