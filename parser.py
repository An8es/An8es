# parser.py

import requests
import json
from bs4 import BeautifulSoup

def parse_laws():
    # Пример URL для Уголовного кодекса РФ
    url = "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102100000&rdk=0"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    laws = []
    # Пример извлечения статей (уточните селекторы для вашего случая)
    for item in soup.select(".law-article"):  # Селектор для статей
        title = item.select_one(".article-title").text.strip()
        link = item.select_one("a")["href"]
        laws.append({"title": title, "link": link})

    # Сохраняем законы в JSON-файл
    with open("laws.json", "w", encoding="utf-8") as f:
        json.dump(laws, f, ensure_ascii=False, indent=4)

    return laws

if __name__ == "__main__":
    laws = parse_laws()
    print(f"Сохранено {len(laws)} статей в файл laws.json")