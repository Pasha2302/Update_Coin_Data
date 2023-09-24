import fnmatch
import json
from datetime import datetime, timezone, timedelta
import os
import time
import asyncio
import pickle
# import aiohttp
# import logging
from contextlib import contextmanager
from urllib.parse import urlparse, parse_qs, urlencode


class Style:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def find_files_with_extension(extension, folder_path):  # extension = 'txt'; folder_path = '/data_dir'
    # Функция возвращаем список найденных файлов с указанным расширением
    found_files = []
    # Обход файловой системы, начиная с указанной папки
    for root, dirs, files in os.walk(folder_path):
        # root - текущая директория, dirs - список поддиректорий, files - список файлов в текущей директории
        for filename in fnmatch.filter(files, f'*.{extension}'):
            # Фильтруем файлы по расширению, добавляем пути к найденным файлам в список found_files
            found_files.append(os.path.join(root, filename))

    return found_files


def save_txt_data(data_txt, path_file):
    """Сохраняет текстовые данные в файл.
    Args:
        data_txt (str): текстовые данные для сохранения.
        path_file (str): путь к файлу для сохранения данных.
    """
    with open(path_file, 'w', encoding='utf-8') as f:
        f.write(str(data_txt))


def save_txt_data_complementing(data_txt, path_file):
    """Дописывает текстовые данные в конец файла.
    Args:
        data_txt (str): текстовые данные для записи.
        path_file (str): путь к файлу для записи данных.
    """
    with open(path_file, 'a', encoding='utf-8') as f:
        f.write(f"{str(data_txt)}\n")


def download_txt_data(path_file) -> str:
    """Загружает текстовые данные из файла.
    Args:
        path_file (str): путь к файлу для загрузки данных.
    Returns:
        str: загруженные текстовые данные.
    """
    with open(path_file, encoding='utf-8') as f:
        return f.read()


def save_json_complementing(json_data, path_file, ind=False):
    """Дописывает данные в формате JSON в конец файла.
    Args:
        json_data (list[dict] | dict): данные в формате JSON для записи.
        path_file (str): путь к файлу для записи данных.
        ind (bool): Флаг, указывающий на необходимость форматирования записываемых данных.
                    По умолчанию форматирование отключено.
    """
    indent = None
    if ind:
        indent = 4
    if os.path.isfile(path_file):
        # File exists
        with open(path_file, 'a', encoding='utf-8') as outfile:
            outfile.seek(outfile.tell() - 1, os.SEEK_SET)
            outfile.truncate()
            outfile.write(',\n')
            json.dump(json_data, outfile, ensure_ascii=False, indent=indent)
            outfile.write(']')
    else:
        # Create file
        with open(path_file, 'w', encoding='utf-8') as outfile:
            array = [json_data]
            json.dump(array, outfile, ensure_ascii=False, indent=indent)


def save_json_data(json_data, path_file):
    """Сохраняет данные в формате JSON в файл.
    Args:
        json_data (list[dict] | dict): данные в формате JSON для сохранения.
        path_file (str): путь к файлу для сохранения данных.
    """
    with open(path_file, 'w', encoding="utf-8") as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)


def download_json_data(path_file) -> list[dict] | dict:
    """Загружает данные в формате JSON из файла.
    Args:
        path_file (str): путь к файлу для загрузки данных.
    Returns:
        list[dict] | dict: загруженные данные в формате
    """
    with open(path_file, encoding="utf-8") as f:
        return json.load(f)


def save_pickle_data(data_pickle, path_file):
    """Сохраняет данные в файл в формате pickle"""
    with open(path_file, 'wb') as f:
        pickle.dump(data_pickle, f)


def save_complementing_pickle_data(data_pickle, path_file):
    """Дописывает данные в конец файла в формате pickle"""
    with open(path_file, 'ab') as f:
        pickle.dump(data_pickle, f)


def download_pickle_data(path_file):
    """Генератор, который поочередно возвращает объекты из файла в формате pickle"""
    with open(path_file, 'rb') as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break


def add_work_days(current_date):
    """Если текущая дата выподает на выходной возвращает ближайшую рабочую дату."""

    # Преобразовываем переданную дату в объект datetime
    current_datetime = datetime.fromtimestamp(current_date)
    # Определяем, является ли текущий день выходным
    is_weekend = current_datetime.weekday() >= 5
    if is_weekend:
        # Определяем количество дней, которое нужно добавить к текущей дате
        days_to_add = 7 - current_datetime.weekday()
        # Добавляем нужное количество дней к текущей дате
        current_datetime += timedelta(days=days_to_add)
    # Возвращаем результат в формате timestamp
    return current_datetime.timestamp()


def date_str(time_int, utc=False, seconds=False, standart=False):
    """Возвращает строку с датой в формате '%d/%m/%y %H:%M' или '%H:%M:%S' (если seconds=True).
            Если standart=True - '%y-%m-%d'
           Если utc=True, то время будет возвращено в UTC"""
    if time_int > 1670000000000:
        time_int = time_int // 1000
    if standart:
        form_str = '%Y-%m-%d'
    else:
        form_str = '%H:%M:%S' if seconds else '%d/%m/%y %H:%M'
    return datetime.fromtimestamp(time_int, tz=timezone.utc).strftime(form_str) if utc else datetime.fromtimestamp(
        time_int).strftime(form_str)


def date_file(time_int):
    """Возвращает строку с датой и временем в формате '%d-%m-%Y_%H-%M-%S' для имени файла"""
    if time_int > 1670000000000:
        time_int = time_int // 1000
    form_str = '%d-%m-%Y_%H-%M-%S'
    return datetime.fromtimestamp(time_int).strftime(form_str)


def time_it(func):
    """
    Декоратор для замера времени выполнения функции в формате часы:минуты:секунды.
    Выводит время выполнения функции в консоль.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        total_time = end_time - start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = round((total_time % 3600) % 60, 4)
        print(f"\nВремя выполнения функции {func.__name__}: {hours:02d}:{minutes:02d}:{seconds:.4f}")
        return result
    return wrapper


class TimeDelta:
    """
    Класс, представляющий временной интервал между двумя датами
        :param past_date: прошлая дата
        :param current_date: нынешняя или будущая
    """
    def __init__(self, past_date, current_date):
        if isinstance(past_date, datetime) and isinstance(current_date, datetime):
            self.timestamp1 = past_date.timestamp()
            self.timestamp2 = current_date.timestamp()
        elif isinstance(past_date, (int, float)) and isinstance(current_date, (int, float)):
            self.timestamp1 = past_date
            self.timestamp2 = current_date
        else:
            raise TypeError("Неподдерживаемый тип данных для past_date и current_date")

        self._calculate_diff()

    def _calculate_diff(self):
        """Вычисляет разницу между датами и записывает ее в атрибуты класса"""
        dt1 = datetime.fromtimestamp(self.timestamp1)
        dt2 = datetime.fromtimestamp(self.timestamp2)
        diff = dt2 - dt1
        self.days = diff.days
        self.hours = diff.seconds // 3600
        self.minutes = (diff.seconds // 60) % 60
        self.seconds = diff.seconds % 60

    def __str__(self):
        """Возвращает строку с описанием временного интервала"""
        return f"Разница между датами: " \
               f"{self.days} дней, {self.hours} часов, {self.minutes} минут, {self.seconds} секунд"


# class AiohttpSession:
#     def __init__(self, limit=25, ssl=True, total=320, sock_connect=160, sock_read=160, trust_env=True, logger=None):
#         """
#         Конструктор класса AiohttpSession.
#
#         :param limit: максимальное количество одновременных соединений
#         :param ssl: использовать ли SSL-шифрование для соединений
#         :param total: общее время ожидания для HTTP-запросов
#         :param sock_connect: время ожидания соединения с сервером
#         :param sock_read: время ожидания ответа от сервера
#         :param trust_env: использовать ли значения настроек из системных переменных окружения
#         :param logger: объект логгера для записи сообщений
#         ---------------------------------------------------------------------------------------
#         Обработка ошибок: добавлен объект logger,
#         который можно использовать для записи сообщений о возникших ошибках и
#         проблемах. При возникновении исключений можно использовать методы
#         logger.exception() или logger.error() для записи соответствующей информации в лог.
#         """
#         self.limit = limit
#         self.ssl = ssl
#         self.total = total
#         self.sock_connect = sock_connect
#         self.sock_read = sock_read
#         self.trust_env = trust_env
#         self.logger = logger or logging.getLogger(__name__)
#
#     async def create_session(self) -> aiohttp.client.ClientSession:
#         """
#         Создает объект сессии для выполнения HTTP-запросов.
#         :return: объект ClientSession
#         """
#         conn = aiohttp.TCPConnector(
#             limit=self.limit,
#             ssl=self.ssl,
#             enable_cleanup_closed=True,  # включить очистку закрытых соединений
#             # keepalive_timeout=120,  # время жизни соединения в секундах
#         )
#
#         timeout = aiohttp.ClientTimeout(
#             total=self.total,
#             sock_connect=self.sock_connect,
#             sock_read=self.sock_read
#         )
#
#         cookie_jar = aiohttp.CookieJar()  # инициализация объекта для хранения кук
#
#         session = aiohttp.ClientSession(
#             connector=conn,
#             timeout=timeout,
#             trust_env=self.trust_env,
#             # cookie_jar=cookie_jar
#         )
#
#         self.logger.debug("Создан новый объект ClientSession")
#
#         return session


@contextmanager
def create_loop():
    loop_contex = None
    try:
        loop_contex = asyncio.new_event_loop()
        yield loop_contex
    finally:
        if loop_contex:
            if not loop_contex.is_closed():
                all_tasks = asyncio.all_tasks(loop_contex)
                if not all_tasks:
                    print("\nВсе задачи выполнены...")
                else:
                    for t, task in enumerate(all_tasks, start=1):
                        # print(f"[{t}] {task}\n{task.done()=}")
                        # print('--' * 40)
                        task.cancel()
                loop_contex.close()
                time.sleep(2)


class UrlParser:
    def __init__(self, url):
        # Разбиваем URL на составляющие и сохраняем в self.parsed_url
        self.parsed_url = urlparse(url)
        # Получаем параметры запроса и сохраняем в self.query_params
        self.query_params = parse_qs(self.parsed_url.query)

    def get_scheme(self):
        # Возвращает схему (http, https, ftp и т.д.)
        return self.parsed_url.scheme

    def get_domain(self):
        # Возвращает доменное имя
        return self.parsed_url.netloc

    def get_path(self):
        # Возвращает путь
        return self.parsed_url.path

    def get_query_params(self):
        # Возвращает параметры запроса в виде словаря
        return self.query_params

    def set_query_param(self, key, value):
        # Изменяет значение параметра запроса с заданным ключом на заданное значение
        self.query_params[key] = [value]

    def set_query_params(self, params: dict):
        # Задает новые параметры запроса
        # принимает словарь параметров запроса, а метод
        self.query_params = params

    def build_url(self):
        # Преобразует словарь параметров запроса в строку запроса и возвращает полный URL-адрес
        query_string = urlencode(self.query_params, doseq=True)
        return f"{self.get_scheme()}://{self.get_domain()}{self.get_path()}?{query_string}"


# class OpenAITranscriber:
#     def __init__(self, api_key):
#         self.api_key = api_key
#         openai.api_key = self.api_key
#
#     def transcribe_audio(self, model, audio_path):
#         with open(audio_path, "rb") as audio_file:
#             transcript = openai.Audio.transcribe(model, audio_file)
#             return transcript


if __name__ == '__main__':
    pass
    # import openai
    # import configparser
    #
    # config = configparser.ConfigParser()
    # config.read("config_bot.ini")
    # api_key_bot = config['TG_BOT']['API_KEY_BOT']
    #
    # transcriber = OpenAITranscriber(api_key=api_key_bot)
    # transcript = transcriber.transcribe_audio(model="whisper-1", audio_path="audio.mp3")
    # print(transcript)

    # start_time = time.time()
    # time.sleep(10)
    # current_time = time.time()

    # start_time = datetime(2023, 9, 1)
    # current_time = datetime(2023, 9, 6)
    #
    # print(f"\n{start_time=}\n{current_time=}\n")
    #
    # time_d = TimeDelta(past_date=start_time, current_date=current_time)
    # print(time_d)

    # print(date_str(1681166436))
    # print(date_str(int(time.time()) - 3600 * 3))
