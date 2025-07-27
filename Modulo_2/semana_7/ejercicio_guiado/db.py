from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import insert, select
import jwt

metadata_obj = MetaData()

user_table = Table(
    "users",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("username", String(30)),
    Column("password", String),
)


class DB_Manager:
    def __init__(self):
        self.engine = create_engine('postgresql+psycopg2://lggm:1234@localhost:5432/semana_7_db')
        metadata_obj.create_all(self.engine)
        
    def insert_user(self, username, password):
        stmt = insert(user_table).returning(user_table.c.id).values(username=username, password=password)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.all()[0]

    def get_user(self, username, password):
        stmt = select(user_table).where(user_table.c.username == username).where(user_table.c.password == password)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            users = result.all()

            if(len(users)==0):
                return None
            else:
                return users[0]

    def get_user_by_id(self, id):
        stmt = select(user_table).where(user_table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            users = result.all()
            if(len(users)==0):
                return None
            else:
                return users[0]


class JWT_Manager:
    def __init__(self, secret, algorithm):
        self.secret = secret
        self.algorithm = algorithm

    def encode(self, data):
        try:
            encoded = jwt.encode(data, self.secret, algorithm=self.algorithm)
            return encoded
        except:
            return None

    def decode(self, token):
        try:
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return decoded
        except Exception as e:
            print(e)
            return None