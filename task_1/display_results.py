import sqlite3

conn = sqlite3.connect('books.db')
cur = conn.cursor()

# Create summary table
with open('summary.sql', 'r') as f:
    cur.executescript(f.read())

# Show row counts
print("Row count in books:", cur.execute('SELECT COUNT(*) FROM books').fetchone()[0])
print("Row count in summary:", cur.execute('SELECT COUNT(*) FROM summary').fetchone()[0])

# Display summary table
for row in cur.execute('SELECT * FROM summary ORDER BY publication_year'):
    print(row)

conn.close()