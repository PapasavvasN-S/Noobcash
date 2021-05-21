import threading
import time
import random
import requests
import json


NODES = 5

transactionList = []

def read_transactions(directory, port):
    base_url = "http://127.0.0.1:" + str(port) + "/"
    f = open(directory, "r")
    f1 = f.readlines()
    for line in f1:
        inputs = line.split()
        inputs = line.split()
        receiver_id = inputs[0][2]
        amount = inputs[1]
        url = base_url+"transaction/create/" + str(receiver_id) + "/" + str(amount)
        transactionList.append(url)
    return;

if __name__ == '__main__':
    start = time.time()
    threads = []
    transactions =0
    for i in range(NODES):
        directory = 'transactions' + str(i) + '.txt'
        port = 5000
        port += i
        threads.append(threading.Thread(target = read_transactions, args = (directory,port)))
    
    for i in range(NODES):
        threads[i].start()
        
    for i in range(NODES):
        threads[i].join()
    i = 0
    random.shuffle(transactionList)
    for request in transactionList
        i +=1
        if i%50 == 0:
            print("%d th iteration, at time %s" %(i,time.ctime()))
        response = requests.get(request)
        if response.status_code == 200:
            transactions += 1
        time.sleep(0.2)
    
    finish = time.time()
    xronos = finish - start
    print("All transactions finished in %d seconds" %xronos )
    