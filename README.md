**Управление геопространственной базой данных (тестовое задание 1 DATUM Group)**

Необходим PostgreSQL/PostGIS и геоинформационная библиотека gdal

**Установка** 
``` bash
conda create --name <my-env>
conda activate <my-env>
pip install -r requirements.txt
```
Вписать данные в файл .env
В settings.py url и путь к gdall библиотеке 

**Запуск**
``` bash 
python .\manage.py runserver <url>
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
1. area: bool - площадь объекта в квадратных метрах
2. bbox x_min y_min x_max y_max
3. type_geo_output: ['simple', 'feature'] default feature - определение формата вывода ответа
4. total area: bool - суммарная площадь всех объектов в ответе (пагинации)

**Пагинация**
1. limit and offset
2. page
