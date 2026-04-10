import json
import sqlite3

# Load the cleaned JSON
with open('books.json', 'r', encoding='utf-8') as f:
    books = json.load(f)

# Connect to SQLite
conn = sqlite3.connect('books.db')
cur = conn.cursor()

# Create table
cur.execute('''
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    genre TEXT,
    publisher TEXT,
    year INTEGER,
    price TEXT
)
''')

# Insert data
for book in books:
    cur.execute('''
        INSERT OR IGNORE INTO books (id, title, author, genre, publisher, year, price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(book.get('id')),
        book.get('title'),
        book.get('author'),
        book.get('genre'),
        book.get('publisher'),
        book.get('year'),
        book.get('price')
    ))

conn.commit()
print("Row count in books:", cur.execute('SELECT COUNT(*) FROM books').fetchone()[0])
conn.close()