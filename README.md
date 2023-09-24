# Установите докер:
<html>
<body>
    <a href="https://docs.docker.com/engine/install/ubuntu/">
      <img src="https://docs.docker.com/assets/favicons/docs@2x.ico">
    </a>
</body>
</html>

## Создайте образ с Python3.11 с помошью файла Docker:
    docker build -t my_custom_image .  (Запускайте команду из дериктории программы [.] - текушая дериктория.)

## Запустите контейнер с базой данных MySql:
#### Загрузка образа MySql с параметрами:
    docker run --name mysql_docker -v /home/pavelpc/mysql_data_docker/data_v01:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=passroot -d mysql:8.1.0
    
    ('это путь до директории где будет хранить сои данны MySql запущенная в Docker:
    /home/pavelpc/mysql_data_docker/data_v01 Создайте свою директорию и укажите свой путь.')

#### Создание пользователя и передачи ему прав Root:
    docker exec -it mysql_docker bash (Если mysql в Docker контейнере)

    mysql -u root -p (Входим как root)

    CREATE USER 'new_user'@'%' IDENTIFIED BY 'new_password';  (Создаем пользователя)

    FLUSH PRIVILEGES;   (Обновляем привелегии.)


### Запустите скрипт из созданного образа python3.11 в контейнере:
##### Запускать контейнер так-же нужно из директории скрипта.
    - docker run -d -v $(pwd):/app -p 5000:5000 <имя образа или id>


