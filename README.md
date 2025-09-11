# Бот предложки для сообщества ТТИТ в ВКонтакте

## Общая информация

Данный бот был сделан по заданию учёбной части техникума, для отправки обращений в более приватной форме, чем обсуждение "вопрос-ответ",
на ровне со звонками, но с возможностью прикрепления картинок и фотографий.

Зависимости: python 3.9+ и библиотеки указанные в файле requirements.txt

## Настройка

Требует ключ с правами доступа:
1. управление сообществом
2. сообщения сообщества

В Long Poll API должны быть включены типы событий:

 - Сообщения:
 - [x] Входящее сообщение
 - [x] Исходящее сообщение


Далее для работы создайте конфигурацию в файле .env, следуя примеру из файла .env.example
Скопируйте содержимое файла .env.example в .env и измените значения переменных на свои.

## Запуск

Сначала установите зависимости:

```bash
pip install -r requirements.txt
```

Затем запустите бота:

```bash
python main.py
```

Либо используйте docker-compose:

```bash
docker-compose up -d
```
-----
P.S. Инструкция по запуску бота при помощи systemd

<details><summary>Userspace</summary>
Для запуска бота при помощи systemd, создайте файл /etc/systemd/system/vk-callback-bot.service с содержимым:

```ini
[Unit]
Description=Callback Bot for VK
After=network.target

[Service]
User=ИМЯ_ПОЛЬЗОВАТЕЛЯ
Group=ИМЯ_ГРУППЫ
WorkingDirectory=/ПУТЬ_ДО_ПРОЕКТА
ExecStart=/usr/bin/python3 main.py
Restart=always
BurstLimit=0
BurstLimitInterval=300s
BurstLimitBurst=0

[Install]
WantedBy=multi-user.target
```

Затем выполните следующие команды:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vk-callback-bot.service
sudo systemctl start vk-callback-bot.service
```
</details>

<details><summary>Docker-Compose</summary>
Если используете docker-compose,то создайте файл /etc/systemd/system/vk-callback-bot-docker-compose.service с содержимым:

```ini
[Unit]
Description=Callback Bot for VK with docker-compose
After=network.target

[Service]
User=ИМЯ_ПОЛЬЗОВАТЕЛЯ
Group=ИМЯ_ГРУППЫ
WorkingDirectory=/ПУТЬ_ДО_ПРОЕКТА
ExecStart=/usr/bin/docker-compose up -d
Restart=always
BurstLimit=0
BurstLimitInterval=300s
BurstLimitBurst=0

[Install]
WantedBy=multi-user.target
```

Затем выполните следующие команды:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vk-callback-bot-docker-compose.service
sudo systemctl start vk-callback-bot-docker-compose.service
```
</details>
