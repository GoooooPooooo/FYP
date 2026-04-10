from machine import UART
from umqtt.simple import MQTTClient
import time
import network

# Настройки Wi-Fi
WIFI_SSID = "wifi_ssid"
WIFI_PASSWORD = "wifi_password"

# Настройки MQTT
MQTT_CLIENT_ID = "user_816e63ee_ROBOT_BAUMAN"
MQTT_BROKER = "srv2.clusterfly.ru"
MQTT_PORT = 9991
MQTT_SSL = False
MQTT_USER = "user_816e63ee"
MQTT_PASSWORD = "D5AnSsTYx2V-6"
MQTT_TOPIC_PUB = "user_816e63ee/pub"
MQTT_TOPIC_SUB = "user_816e63ee/sub"

# Инициализация UART (UART2, пины GPIO16/GPIO17)
uart = UART(2, 9600)
uart.init(baudrate=9600, bits=8, parity=0, stop=2)

# Функция для подключения к Wi-Fi
def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Подключаемся к Wi-Fi...")
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        start_time = time.time()
        while not sta_if.isconnected():
            if time.time() - start_time > 10:
                print("Не удалось подключиться к Wi-Fi")
                return False
            time.sleep(1)
        print("Wi-Fi подключен:", sta_if.ifconfig())
        return True

# Функция для отправки команды через UART
def send_command(command):
    commands = command.split("\r\n")
    for cmd in commands:
        if cmd:
            # Публикуем отправляемую команду в MQTT
            try:
                client.publish(MQTT_TOPIC_PUB, f"Sent command:{cmd}")
                print("Опубликована отправленная команда в MQTT:", cmd)
            except Exception as e:
                print("Ошибка публикации отправленной команды:", e)

            uart.write(cmd + '\r\n')  # Отправляем команду
            time.sleep(1)  # Задержка между командами

            response = read_response()  # Чтение ответа
            if response:
                print("Ответ от устройства:", response)
                try:
                    client.publish(MQTT_TOPIC_PUB, f"Response:{response}")
                    print("Опубликовано в MQTT:", response)
                except Exception as e:
                    print("Ошибка публикации ответа:", e)
                time.sleep(1)
            time.sleep(1)

# Функция для чтения ответа через UART
def read_response():
    time.sleep(1)
    if uart.any():
        response = uart.read().decode('utf-8')
        print(response)
        return response
    return None

# Функция для обработки входящих сообщений MQTT
def on_message(topic, msg):
    print("Получено сообщение:", msg.decode(), "в топике:", topic.decode())
    # Отправляем команду на устройство через UART
    command = msg.decode()
    send_command(command)
    # Читаем ответ от устройства
    response = read_response()
    # Публикуем ответ в MQTT
    if response:
        client.publish(MQTT_TOPIC_PUB, response)
        print("Опубликовано сообщение в MQTT:", response)

def main():
    # Подключение к Wi-Fi
    if not connect_wifi():
        return

    # Создание MQTT клиента
    global client
    client = MQTTClient(
        client_id=MQTT_CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASSWORD,
        ssl=MQTT_SSL
    )
    client.set_callback(on_message)

    # Подключение к MQTT брокеру
    try:
        client.connect()
        print("Подключено к MQTT брокеру")
    except Exception as e:
        print("Ошибка подключения к MQTT брокеру:", e)
        return

    client.subscribe(MQTT_TOPIC_SUB)
    print("Подписались на топик:", MQTT_TOPIC_SUB)

    # Основной цикл
    try:
        while True:
            client.check_msg()  # Проверка входящих сообщений
            time.sleep(1)
    except Exception as e:
        print("Ошибка:", e)
    finally:
        # Отключение от MQTT брокера
        client.disconnect()
        print("Отключено от MQTT брокера")

# Запуск основной функции
if __name__ == "__main__":
    main()