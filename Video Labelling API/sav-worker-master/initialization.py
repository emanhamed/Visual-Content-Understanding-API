import pika
import magic
import time
import os
import json
from sqlalchemy import *
from sqlalchemy.orm import create_session,sessionmaker
from sqlalchemy.ext.declarative import declarative_base

#Create and engine and get the metadata
Base = declarative_base()
engine = create_engine(os.environ['POSTGRES_URL'])
metadata = MetaData(bind=engine)

#Reflect each database table we need to use, using metadata
class Tasks(Base):
    __table__ = Table('tasks', metadata, autoload=True)

class Users(Base):
    __table__ = Table('users', metadata, autoload=True)


#Create a session to use the tables
session = sessionmaker(bind=engine)()

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()
channel_extract = connection.channel()
channel_classify = connection.channel()

channel.queue_declare(queue='initialization', durable=True)
channel_extract.queue_declare(queue='extract', durable=True)
channel_classify.queue_declare(queue='classify', durable=True)

print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    task = session.query(Tasks).filter_by(id=int(body)).first()
    if not os.path.exists("user_data/"+str(task.userId)):
        os.makedirs("user_data/"+str(task.userId))
    if not os.path.exists("../sav-app/assets/user_data"):
        os.makedirs("../sav-app/assets/user_data")
    if not os.path.exists("user_data"):
        os.makedirs("user_data")
    if not os.path.exists("../sav-app/assets/user_data/"+str(task.userId)):
        os.makedirs("../sav-app/assets/user_data/"+str(task.userId))
    os.makedirs("user_data/"+str(task.userId)+'/'+body)
    os.makedirs("../sav-app/assets/user_data/"+str(task.userId)+'/'+body)
    task.status = "Validating file"
    session.commit()
    task = session.query(Tasks).filter_by(id=int(body)).first()
    filename = json.loads(task.file)[0]
    filetype = magic.from_file(filename, mime=True)
    if task.type == 'image':
        task.dataKeyFrames = [0]
        task.status = "confrimed image file, sending to classifier"
        session.commit()
        channel_classify.basic_publish(exchange='', routing_key="classify", body=body)
        task = session.query(Tasks).filter_by(id=int(body)).first()
        task.status = "sent to classifier"
        session.commit()
    else:
        task.status = "confrimed video file, sending to extractor"
        session.commit()
        task = session.query(Tasks).filter_by(id=int(body)).first()
        channel_extract.basic_publish(exchange='', routing_key="extract", body=body)
        task.status = "sent to extractor"
        session.commit()

    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='initialization')

channel.start_consuming()
