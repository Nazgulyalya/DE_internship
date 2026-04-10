import re
import json

with open('task1_d.json', 'r', encoding='utf-8') as f:
    data = f.read()

# Обрезаем всё до первой [
data = data[data.find('['):]

# Заменяем => на :
data = re.sub(r'=>', ':', data)

# Кавычки вокруг ключей
data = re.sub(r'([{\s,]):(\w+)', r'\1"\2"', data)

# Кавычки вокруг строковых значений (только если они не в кавычках)
data = re.sub(r':\s*"(.*?)"', r': "\1"', data)  # уже в кавычках — оставляем
data = re.sub(r":\s*'([^']*)'", r': "\1"', data)  # одинарные кавычки
data = re.sub(r':\s*([A-Za-z0-9_.@/-]+)', r': "\1"', data)  # без кавычек

# Ruby nil/true/false → JSON null/true/false
data = re.sub(r':\s*nil', r': null', data)
data = re.sub(r':\s*true', r': true', data)
data = re.sub(r':\s*false', r': false', data)

# Исправляем запятые между объектами (если вдруг нет)
data = re.sub(r'}\s*{', '},\n{', data)

# Теперь парсим
try:
    books = json.loads(data)
except Exception as e:
    print("Ошибка парсинга:", e)
    with open('debug.json', 'w', encoding='utf-8') as f:
        f.write(data)
    exit(1)

with open('books.json', 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print("books.json готов!")