import pika
import glob
import time
import json
import os
import subprocess
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
channel_classify = connection.channel()

channel.queue_declare(queue='extract', durable=True)
channel_classify.queue_declare(queue='classify', durable=True)

print(' [*] Waiting for messages. To exit press CTRL+C')

def extractKF(filename, userId, taskId):
    ffmpeg = '/usr/bin/ffmpeg'
    ffprobe = '/usr/bin/ffprobe'
    base_url = "user_data/"+userId+"/"+taskId+'/'
    outFile = base_url+'%07d.JPEG'
    timeFile = base_url+'time.txt'
    indicesFile  = base_url+'frame_indices.txt'
    cmd1 = [ffmpeg ,'-i', filename,'-vf',"select=gt(scene\,0.5)",'-vsync','vfr',outFile]
    subprocess.call(cmd1)
    cmd = [ffprobe ,' -show_frames -f lavfi "movie=',filename,',select=gt(scene\,.5)" | grep "pkt_pts_time=" >> ' ,timeFile]
    cmd2 = ' '.join(cmd)
    os.system(cmd2)
    cmd3 = [ffprobe ,' -show_frames -f lavfi "movie=',filename,',select=gt(scene\,.5)" | grep -n I| cut -d : -f 1 > ',indicesFile]
    cmd4 = ' '.join(cmd3)
    os.system(cmd4)
    infile = base_url+"time.txt"
    delete_list = ["pkt_pts_time="]
    fin = open(infile)
    out = []
    for line in fin:
        for word in delete_list:
            line = line.replace(word, "")
        out.append(line)
    old_time_list = [word.strip() for word in out]
    time_list = []
    for item in old_time_list:
        time_list.append(time.strftime('%H:%M:%S', time.gmtime(float(item))))
    with open(indicesFile) as f:
        indices_list = f.readlines()
        print f.readlines()
    indices_list = [indices_list.rstrip('\n') for indices_list in open(indicesFile)]
    os.remove(indicesFile)
    os.remove(timeFile)
    return time_list, indices_list

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    task = session.query(Tasks).filter_by(id=int(body)).first()
    task.status = "recieved by extractor, running extractor"
    session.commit()
    task = session.query(Tasks).filter_by(id=int(body)).first()
    timelist, result = extractKF(json.loads(task.file)[0],str(task.userId),str(task.id))
    filelist = []
    for imagefile in glob.glob("user_data/"+str(task.userId)+'/'+str(task.id)+'/*.JPEG'):
        os.rename(os.path.abspath(imagefile), os.path.abspath('../sav-app/assets/user_data/'+str(task.userId)+'/'+str(task.id)+'/'+imagefile.split('/')[-1]))
        filelist.append(os.path.abspath('../sav-app/assets/user_data/'+str(task.userId)+'/'+str(task.id)+'/'+imagefile.split('/')[-1]))
    task.file = json.dumps(sorted(filelist))
    task.status = "finished extracting, sending to classifier"
    task.dataKeyFrames = json.dumps(sorted(map(int,result)))
    task.timeList = json.dumps(sorted(timelist))
    session.commit()
    channel_classify.basic_publish(exchange='', routing_key="classify", body=body)
    task = session.query(Tasks).filter_by(id=int(body)).first()
    task.status = "sent to classifier"
    session.commit()
    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='extract')

channel.start_consuming()
