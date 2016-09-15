import pika
import time
import os
import json
import sys
import operator
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import *
from sqlalchemy.orm import create_session,sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from collections import Counter, defaultdict
##### config
caffe_root = os.environ['CAFFE_HOME']+'/'
postgres_url = os.environ['POSTGRES_URL']
sys.path.insert(0, caffe_root + 'python')

import caffe
#### classifier config
caffe.set_device(0)
caffe.set_mode_gpu()

highProb = 5
plt.rcParams['figure.figsize'] = (10, 10)
plt.rcParams['image.interpolation'] = 'nearest'
plt.rcParams['image.cmap'] = 'gray'

model_def = caffe_root + 'models/bvlc_alexnet/deploy.prototxt'
model_weights = caffe_root + 'models/bvlc_alexnet/bvlc_alexnet.caffemodel'
net = caffe.Net(model_def,
                model_weights,
                caffe.TEST)

mu = np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy')
mu = mu.mean(1).mean(1)
transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})

transformer.set_transpose('data', (2,0,1))
transformer.set_mean('data', mu)
transformer.set_raw_scale('data', 255)
transformer.set_channel_swap('data', (2,1,0))

net.blobs['data'].reshape(50,3,227, 227)


Base = declarative_base()
engine = create_engine(postgres_url)
metadata = MetaData(bind=engine)

class Tasks(Base):
    __table__ = Table('tasks', metadata, autoload=True)

class Users(Base):
    __table__ = Table('users', metadata, autoload=True)

session = sessionmaker(bind=engine)()

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='classify', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

def indices(time_list,dictionary,lst, items= None):
    j = 0
    items, ind= set(lst) if items is None else items, defaultdict(list)
    items, probSet= set(lst) if items is None else items, defaultdict(list)
    for i, v in enumerate(lst):
        if v in items:
            ind[v].append(i)
            probSet[v].append(dictionary[(i/highProb)+1][i%highProb][1])
    return ind,probSet

def classifyImage(imagePath):
    if imagePath is not None:
        image = caffe.io.load_image(imagePath)
        transformed_image = transformer.preprocess('data', image)
        plt.imshow(image)

        net.blobs['data'].data[...] = transformed_image
        output = net.forward()
        output_prob = output['prob'][0]
        labels_file = caffe_root + 'data/ilsvrc12/synset_words.txt'
        labels = np.loadtxt(labels_file, str, delimiter='\t')
        top_inds = output_prob.argsort()[::-1][:highProb]
        top_labels = labels [top_inds];
        cleanLabels = []
        for index in top_labels:
            cleanLabels.append(index[10:])
        print cleanLabels
        return cleanLabels

def classifyVideo(dirPath,time_list,indices_list):
    index = 1
    dictionary = {}
    labelsPercent = 0.4
    for filename in dirPath:
        imagePath = filename
        #print imagePath
        image = caffe.io.load_image(imagePath)
        transformed_image = transformer.preprocess('data', image)
        plt.imshow(image)

        net.blobs['data'].data[...] = transformed_image

        output = net.forward()

        output_prob = output['prob'][0]

        labels_file = caffe_root + 'data/ilsvrc12/synset_words.txt'
        labels = np.loadtxt(labels_file, str, delimiter='\t')
        top_inds = output_prob.argsort()[::-1][:highProb]
        labelsProb = output_prob[top_inds]
        labelsNames = labels[top_inds];
        zippedLabelsProb = [[],[],[],[],[]]

        for x in range(0, highProb):
            zippedLabelsProb[x]=[labelsNames[x], labelsProb[x]]
        dictionary[index] = zippedLabelsProb
        caffe.set_device(0)
        caffe.set_mode_gpu()
        net.forward()
        index += 1


    #This is the last one that was working
    labelsList = []
    for  k, v in dictionary.items():
        for x in range(0, highProb):
            labelsList.append(dictionary[k][x][0])
    labelsSet = set(labelsList)
    uniqueProb = [0] * len(labelsSet)
    new = indices(time_list, dictionary,labelsList, labelsList)
    finalLabels = new[0]
    #print finalLabels
    probs = new[1]
    accProb = {}
    for key,lis in probs.items():
        accProb[key] = sum(lis)

    highestProb = sorted(accProb.items(), key=operator.itemgetter(1), reverse=True)  # This is to sort the tuple of the probabilities based on its value

    labelsIterations = int(labelsPercent*len(probs))
    firstProbs = Counter(accProb).most_common(labelsIterations)

    newlist = []
    for (a, b) in firstProbs:
        newlist.append(a)

    finalOutput = {}    #This is the dictionary of the final labels with the their accumilated accuracies
    for key in newlist:
        value = finalLabels[key]
        #print key
        finalOutput[key[10:]]= value

    #from collections import defaultdict
    labels_times = defaultdict(list)
    labels_IDs = defaultdict(list)
    for k, v in finalOutput.iteritems():
        for x in v:
            #print (x/3)
            val =  time_list[x/highProb]
            labels_times[k].append(val)
            index = indices_list[x/highProb]
            labels_IDs[k].append(index)

    return labels_IDs

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    task = session.query(Tasks).filter_by(id=int(body)).first()
    task.status = "recieved by classifier, running classifier"
    session.commit()
    result = {}
    task = session.query(Tasks).filter_by(id=int(body)).first()
    if task.type == 'image':
        result = {0:classifyImage(json.loads(task.file)[0])}
        os.rename(json.loads(task.file)[0], os.path.abspath('../sav-app/assets/user_data/'+str(task.userId)+'/'+str(task.id)+'/'+json.loads(task.file)[0].split('/')[-1]))
        task.file = json.dumps([os.path.abspath('../sav-app/assets/user_data/'+str(task.userId)+'/'+str(task.id)+'/'+json.loads(task.file)[0].split('/')[-1])])
        session.commit()
    else:
        keyframes = sorted(map(int,json.loads(task.dataKeyFrames)))
        print keyframes
        time_list = sorted(json.loads(task.timeList))
        files = sorted(json.loads(task.file))
        result_temp = classifyVideo(files, time_list,map(str,keyframes))
        result = {}
        for key, value in result_temp.iteritems():
            for frame in value:
                if int(frame) not in result.keys():
                    result[int(frame)] = [key]
                else:
                    result[int(frame)].append(key)
    task = session.query(Tasks).filter_by(id=int(body)).first()
    task.status = "finished classifying, check results"
    task.dataClassify = json.dumps(result)
    session.commit()
    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='classify')

channel.start_consuming()
