from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Boolean
import json

class DB():
    def __init__(self) -> None:
        self.db_uri = 'sqlite:///db.db'
        self.engine = create_engine(self.db_uri)
        meta = MetaData()

        self.delayed_message = Table('delayed_message', meta, Column('id', Integer, primary_key=True),
            Column('owner_id', Integer, nullable=False),
            Column('chat_id', Integer, nullable=False),
            Column('dateTime', String, nullable=False),
            Column('data', Text, nullable=False)
        )

        self.message = Table('Message', meta, Column('id', Integer, primary_key=True),
            Column('owner_id', Integer, nullable=False),
            Column('chat_id', Integer, nullable=False),
            Column('data', Text, nullable=False)
        )

    def get_delayed_msgs(self):

        conn = self.engine.connect()
        msgs = conn.execute(self.delayed_message.select()).all()
        conn.close()
        return msgs

    def from_delayed_to_sended(self, msg, data):
        conn = self.engine.connect()
        ins = self.message.insert().values(chat_id = int(data['chat']['id']), owner_id = int(msg[1]), data=json.dumps(data))
        conn.execute(ins)
        ins = self.delayed_message.delete().where(self.delayed_message.c.id == int(msg[0]))
        conn.execute(ins)
        conn.close()