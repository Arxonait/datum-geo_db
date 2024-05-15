**Управление геопространственной базой данных (тестовое задание 1 DATUM Group)**

Необходим PostgreSQL/PostGIS и геоинформационная библиотека gdal, OSGeo4W

Установка
```
conda env create -n <name-env> -f environment.yaml
conda activate <name-env>
```

Создать файл .env 
```
NAME_DB=...
USER_DB=...
PASSWORD_DB=...
HOST_DB=...
PORT_DB=...
GDAL_LIBRARY= ... + .dll
OSGEO4W= ... (Ex: C:\OSGeo4W)
```

**Запуск**
```
python .\manage.py runserver
```

**Endpoints**
1. countries/
2. countries/<int:country_id>
3. cities/
4. cities/<int:city_id>
5. countries/<int:country_id>/cities
6. cities/<int:city_id>/images
7. cities/<int:city_id>/images/<int:num_image>
8. capitals/
9. capitals/<int:capital_id>
10. countries/<int:country_id>/capital

**GET params**
1. area - площадь объекта в квадратных метрах
2. bbox x_min y_min x_max y_max
3. total area - суммарная площадь всех объектов в ответе (пагинации)

**Пагинация**
1. limit and offset
2. page
