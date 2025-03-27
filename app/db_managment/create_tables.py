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

conn = get_db_connection()

def create_underlying_tables(conn=conn):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS SPX_underlying_significant_prices")
    cursor.execute("DROP TABLE IF EXISTS SPX_underlying_one_minute_data")

    conn.commit()

    query_create_significant_prices_table = """
        CREATE TABLE SPX_underlying_significant_prices (
            time TIMESTAMPTZ NOT NULL,
            low_13_week DOUBLE PRECISION,
            high_13_week DOUBLE PRECISION,
            low_26_week DOUBLE PRECISION,
            high_26_week DOUBLE PRECISION,
            low_52_week DOUBLE PRECISION,
            high_52_week DOUBLE PRECISION
        );
    """

    query_create_underlying_one_minute_table = """
        CREATE TABLE SPX_underlying_one_minute_data (
            time TIMESTAMPTZ NOT NULL,
            unix_time BIGINT,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            daily_high DOUBLE PRECISION,
            daily_low DOUBLE PRECISION,
            total_call_volume INTEGER,
            total_put_volume INTEGER,
            option_implied_volatility DOUBLE PRECISION,
            call_open_interest BIGINT,
            put_open_interest BIGINT,
            futures_open_interest INTEGER
        );
    """

    cursor.execute(query_create_significant_prices_table)
    cursor.execute(query_create_underlying_one_minute_table)

    conn.commit()

    cursor.execute("SELECT create_hypertable('SPX_underlying_significant_prices', by_range('time'));")
    cursor.execute("SELECT create_hypertable('SPX_underlying_one_minute_data', by_range('time'));")

    print("Underlying hypertables created successfully.")

    cursor.close()

create_underlying_tables()