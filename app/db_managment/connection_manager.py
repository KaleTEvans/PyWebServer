import psycopg2
from pgcopy import CopyManager
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv
import os

import psycopg2.extras

load_dotenv()

db_params = {
    "host": os.getenv("HOST_URL"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    return psycopg2.connect(**db_params)

def create_sample_tables():
    conn = None
    conn = get_db_connection()

    if conn is not None:
        print("Successfully connected to timescale db")

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS sample_hypertable")
    cursor.execute("DROP TABLE IF EXISTS sample_table")
    conn.commit()
    cursor.close()

    sample_table = """CREATE TABLE sample_table (
                        id SERIAL PRIMARY KEY,
                        strike INTEGER,
                        contract_right VARCHAR(1)
                    );
                    """
    
    sample_hypertable = """
                        CREATE TABLE sample_hypertable (
                            time TIMESTAMPTZ NOT NULL,
                            unix_time BIGINT,
                            contract_id INTEGER,
                            price DOUBLE PRECISION,
                            FOREIGN KEY (contract_id) REFERENCES sample_table (id)
                        );
                        """
    
    query_create_sample_hypertable = "SELECT create_hypertable('sample_hypertable', 'time');"
    
    cursor = conn.cursor()
    cursor.execute(sample_table)
    conn.commit()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute(sample_hypertable)
    cursor.execute(query=query_create_sample_hypertable)
    conn.commit()
    cursor.close()

    print("Created tables successfully")

    sample_cols = ['id', 'strike', 'contract_right']
    hypertable_cols = ['time', 'unix_time', 'contract_id', 'price']

    sample_data = [
        (0, 5520, 'C'),
        (1, 5520, 'P')
    ]

    timestamp = datetime.fromtimestamp(int(1741896364800/1000))

    hypertable_data = [
        (timestamp, 1741896364800, 0, 5521.25),
        (timestamp, 1741896364800, 1, 5519.10)
    ]

    # For eastern time, use tz=timezone(timedelta(hours=-5))
    
    sample_mgr = CopyManager(conn, 'sample_table', sample_cols)
    hypertable_mgr = CopyManager(conn, 'sample_hypertable', hypertable_cols)

    sample_mgr.copy(sample_data)
    hypertable_mgr.copy(hypertable_data)

    conn.commit()
    print("Data inserted successfully")

    query = """
        SELECT 
            h.time,
            h.unix_time,
            h.contract_id,
            h.price,
            s.strike,
            s.contract_right
        FROM 
            sample_hypertable h
        JOIN 
            sample_table s
        ON 
            h.contract_id = s.id;
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query=query)
    sample_items = cursor.fetchall()
    print(sample_items)
    cursor.close()


# create_sample_tables()