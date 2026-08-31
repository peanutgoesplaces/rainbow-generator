import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

#Connection to SQL Database
conn = psycopg2.connect(
    #host="sakura.proxy.rlwy.net",
    host = os.getenv("DB_HOST"),
    #port=31658,
    port = os.getenv("DB_PORT"),
    #database='railway',
    database = os.getenv("DB_NAME"),
    #user='postgres',
    user=os.getenv("DB_USER"),
    #password='RxSaqrkMEfDTrmKrEDsVaHbPgUsxFIMR'
    password=os.getenv("DB_PASSWORD")
)

