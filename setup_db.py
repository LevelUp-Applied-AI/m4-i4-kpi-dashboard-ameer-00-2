import psycopg2

# Connect to the default postgres database to create the amman_market database
conn = psycopg2.connect(
    host="127.0.0.1",
    database="postgres",
    user="postgres",
    password="postgres",
    port=5432
)

conn.autocommit = True  # Needed for CREATE DATABASE

# Create a cursor
cur = conn.cursor()

# Create the database if it doesn't exist
cur.execute("SELECT 1 FROM pg_database WHERE datname = 'amman_market'")
exists = cur.fetchone()
if not exists:
    cur.execute("CREATE DATABASE amman_market")
    print("Database amman_market created.")
else:
    print("Database amman_market already exists.")

# Close the connection to postgres
cur.close()
conn.close()

# Now connect to amman_market
conn = psycopg2.connect(
    host="127.0.0.1",
    database="amman_market",
    user="postgres",
    password="postgres",
    port=5432
)

# Create a cursor
cur = conn.cursor()

# Read and execute schema.sql
with open('schema.sql', 'r') as f:
    schema_sql = f.read()

cur.execute(schema_sql)
conn.commit()

# Read and execute seed_data.sql
with open('seed_data.sql', 'r') as f:
    seed_sql = f.read()

cur.execute(seed_sql)
conn.commit()

# Close the connection
cur.close()
conn.close()

print("Database setup complete!")