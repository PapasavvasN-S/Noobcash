import binascii
import threading

import block
import wallet
import json
import transaction
import time
import blockchain
import requests
import jsonpickle
from time import sleep

from Crypto.PublicKey import RSA

NODES = 10

class Node:
    def __init__(self, ip, port,bootstrap_port, bootstrap_ip, block_capacity, block_difficulty):
        self.block_capacity = block_capacity
        self.block_difficulty = block_difficulty
        self.chain = blockchain.Blockchain()
        self.id=0
        self.ip = ip
        self.bootstrap_port = bootstrap_port
        self.bootstrap_ip = bootstrap_ip
        self.is_bootstrap=False
        self.port = port
        self.ring=[]
        self.UTXO = []
        for i in range (NODES):
            self.UTXO.append([])
        self.wallet = self.create_wallet()
        self.ring = [] #here we store information for every node, as its id, its address (ip:port) its public key and its balance 
        if (self.port==self.bootstrap_port):
            self.id = 0
            self.current_id_count = 0
            self.is_bootstrap = True
            trans = transaction.Transaction('0', '0', str(self.wallet.public_key), NODES*100, [],0,0)
            print("Sent "+str(trans.amount)+" NBC to Bootstrap node")
            self.UTXO[0].append(trans.transaction_outputs[0])
            self.register_me_to_ring(self.wallet.public_key, self.wallet.balance(self.UTXO[0]), ip, port)
            self.generate_genesis()
            self.add_transaction_to_block(trans)

        else:
            self.is_bootstrap = False
            self.request_join_ring()
            
    def create_new_block(self, index, timestamp, transactions, nonce, previous_hash, capacity, difficulty):
        new_block = block.Block(index, timestamp, transactions, nonce, previous_hash, capacity, difficulty)
        return new_block

    
    def request_join_ring(self):
        readyKey = str(self.wallet.public_key)
        requestData = '{"publickey": "' + readyKey + '", "port": "' + str(self.port) + '","ip": "'+ str(self.ip) + '", "balance": "0"}'
        url = "http://"+self.bootstrap_ip+":5000/node/addtoring"
        response = requests.post(url,data = requestData)
        print(response)
    
    
    def generate_genesis(self):
        genesis_block=self.create_new_block(0,time.time(),[],0,1,1,1)
        self.mine_block(genesis_block,0)
        self.chain.add_block(genesis_block)
    
    def create_wallet(self):
        return wallet.Wallet()
		#create a wallet for this node, with a public key and a private key

    def register_node_to_ring(self, address, balance, ip, port):
        self.current_id_count +=1
        node = {
        'id': self.current_id_count,
        'address': str(address),
        'balance': balance,
        'ip': ip,
        'port':port
        }
        node = json.dumps(node)
        node = json.loads(node)
        self.ring.append(node)
        print('Added node '+str(self.current_id_count) + ' to ring')
        startMiningThread = threading.Thread(target = self.set_id_and_update_ring, args = (ip,port));
        startMiningThread.start()
        
    def set_id_and_update_ring(self, ip, port):
        requestData = '{"id": "' + str(self.current_id_count) +'"}'
        url = "http://"+ ip +":"+str(port)+"/node/assignid"
        requests.post(url, data = requestData)
        requestData = jsonpickle.encode(self.ring)
        for node in self.ring:
            url = "http://" + str(node['ip']) + ":"+str(node['port'])+"/node/updateRing"
            requests.post(url, json = {'ring': requestData}) 
        requestData = jsonpickle.encode(self.UTXO)
        for node in self.ring:
            url = "http://" + str(node['ip']) + ":"+str(node['port'])+"/node/updateUTXO"
            requests.post(url, json = {'UTXO': requestData})
        requestData = jsonpickle.encode(self.chain)
        for node in self.ring:
            url = "http://" + str(node['ip']) + ":"+str(node['port'])+"/node/updateChain"
            requests.post(url, json = {'chain': requestData})
        print("creating transaction "+ str(self.ring[self.current_id_count]))
        self.create_transaction(self.wallet.public_key, self.wallet.private_key, self.ring[self.current_id_count]['address'], 100,0,self.current_id_count)
        
        
    def register_me_to_ring(self, address, balance, ip, port):
        node = {
        'id': self.id,
        'address': str(address),
        'balance': balance,
        'ip': ip,
        'port':port
        }
        node = json.dumps(node)
        node = json.loads(node)
        self.ring.append(node)
        print("Added bootstrap node to ring")

		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bottstrap node informs all other nodes and gives the request node an id and 100 NBCs
    def find_id_from_address(self, address):
        for node in self.ring:
            if (node['address'] == str(address)):
                return (node['id'])        
        
    def create_transaction(self, sender_address, sender_private_key, recipient_address, amount, sender_id, receiver_id):
        if (self.ring[sender_id]['balance'] < amount):
            print("Not enough NBC")
        else:
            input_transactions = []
            sum =  0
            for t in self.UTXO[sender_id]:
                sum += t['amount']
                input_transactions.append(t)
                if (sum >=amount):
                    break
            sleep(0.2)
            t = transaction.Transaction(sender_address, sender_private_key, recipient_address, amount, input_transactions,sender_id, receiver_id)
            print("Creating transaction: Sending node "+ str(sender_id) +", Receiving Node " + str(receiver_id)+ ", Amount "+str(amount))
            self.broadcast_transaction(t)



    def broadcast_transaction(self, transaction):
        requestData = jsonpickle.encode(transaction)
        for node in self.ring:
            url = "http://" + str(node['ip']) + ":"+str(node['port'])+"/transaction/validate"
            requests.post(url, json = {'transaction': requestData})


    def validate_transaction(self, transaction):
        sender_id = transaction.sender_id
        verified = transaction.verify_transaction()
        if (verified and self.ring[sender_id]['balance'] >= transaction.amount):
            for t in transaction.transaction_inputs:
                self.UTXO[sender_id].remove(t)
            self.UTXO[transaction.transaction_outputs[0]['receiver_id']].append(transaction.transaction_outputs[0])
            self.ring[transaction.transaction_outputs[0]['receiver_id']]['balance'] = self.wallet.balance(self.UTXO[transaction.transaction_outputs[0]['receiver_id']])
            if (len(transaction.transaction_outputs) == 2):
                self.UTXO[transaction.transaction_outputs[1]['receiver_id']].append(transaction.transaction_outputs[1])
                self.ring[transaction.transaction_outputs[1]['receiver_id']]['balance'] = self.wallet.balance(self.UTXO[transaction.transaction_outputs[1]['receiver_id']])
            return True
        else:
            return False
             

    def add_transaction_to_block(self, transaction):
        if(len(self.chain.blockchain[-1].listOfTransactions) >= self.chain.blockchain[-1].capacity):
            b = self.create_new_block(len(self.chain.blockchain), time.time(), [], 0, self.chain.blockchain[-1].current_hash, self.block_capacity, self.block_difficulty)
            startMiningThread = threading.Thread(target = self.mine_block, args = (b ,transaction));
            startMiningThread.start()
            
        else:
            self.chain.blockchain[-1].add_transaction(transaction)
            print("Added transaction to block "+ str(self.chain.blockchain[-1].index))




    def mine_block(self, block, transaction):
        if (len(self.chain.blockchain) == 0):
            while (self.valid_proof(block) == False):
                block.nonce +=1
            block.current_hash = block.myHash(block.nonce)
        else:
            while ((self.valid_proof(block) == False) and (self.chain.blockchain[-1].current_hash == block.previous_hash)):
                block.nonce +=1
            if (self.chain.blockchain[-1].index == block.index):
                return 0
            else:
                block.current_hash = block.myHash(block.nonce)
                block.add_transaction(transaction)
                print("Node " + str(self.id)+ " found nonce first and is broadcasting block " + str(block.index))
                self.broadcast_block(block)
                print("Added transaction to block "+ str(self.chain.blockchain[-1].index))
                return 0


    def broadcast_block(self, block):
        requestData = jsonpickle.encode(block)
        for node in self.ring:
            url = "http://" + str(node['ip']) + ":"+str(node['port'])+"/block/add"
            requests.post(url, json = {'block': requestData})


    def valid_proof(self, block):
        if (block.myHash(block.nonce).startswith('0'* block.difficulty)):
            return True
        else:
            return False



	#concencus functions

    def validate_block(self, block, chain):
        if (block.index==0):
            return True
        for prevblock in chain:
            if (prevblock.index==block.index-1):    
		#check for the longer chain accroose all nodes
                if (block.current_hash.startswith('0'* block.difficulty) and prevblock.current_hash==block.previous_hash):
                    return True
                else:
                    return False
        
        
    def validate_chain(self, chain):
		#check for the longer chain accroose all nodes
        validatedchain = False
        for block in chain.blockchain:
                if (self.validate_block(block, chain.blockchain)):
                    validatedchain = True
                else:
                    validatedchain = False
                    break;
        return validatedchain

    def resolve_conflicts(self):
        maxlength = len(self.chain.blockchain)
        maxChain = {}
        chosenid = 0
        print("Invalid block, checking if chain need to change")
        for node in (self.ring):
             if node != str(self.id):
                 url = "http://" + str(node['ip']) + ":"+str(node['port'])+"/node/sendChain"
                 data = requests.get(url).json()
                 data = jsonpickle.decode(data['chain'])
                 if len(data)>maxlength:
                     maxChain=data
                     maxlength=len(data)
                     chosenid = node['id']
        if maxlength  > len(self.chain.blockchain):
            self.chain.blockchain = maxChain
            print("Chose longest chain from "+ str(chosenid))


        #         responseDict = json.loads(response.json())
        #         if len(responseDict['chain'])> maxlength:
        #             maxChain = responseDict['chain']
        #             maxlength=len(responseDict['chain'])
                    
        # if maxlength > len(self.chain.blockchain):
        #     self.chain.blockchain = json.dumbs(maxChain)
                    
        # list_of_chains = []
        # list_of_ids = []
        # list_of_rings = []
        # chain = []
        # ring = []
        # chosechainofnode = 0
        # for i in range(5):
        #     print("LAZOS")
        # print("Invalid block, changing chain")
        # for node in self.ring:
        #     if node['id'] == self.id:
        #         continue
        #     url = "http://" + str(node['ip']) + ":"+str(node['port'])+"/node/sendChain"
        #     data = requests.get(url).json()
        #     list_of_chains.append(jsonpickle.decode(data["chain"]))
        #     list_of_ids.append(data["id"])
        #     list_of_rings.append(jsonpickle.decode(data["ring"]))
        #     print("length: "+ str(len(list_of_rings[-1])))
        # if (self.id==0):
        #     maxlen = len(list_of_chains[1])
        #     ring= list_of_rings[1]
        #     chosechainofnode = list_of_ids[1]
        # else:
        #     maxlen = len(list_of_chains[0])
        #     ring= list_of_rings[0]
        #     chosechainofnode = list_of_ids[0]
        # for i in range(len(list_of_chains)):
        #     if(len(list_of_chains[i]) > maxlen) and maxlen<len(self.chain.blockchain):
        #         maxlen = len(list_of_chains[i])
        #         chain = list_of_chains[i]
        #         ring = list_of_rings[i]
        #         chosechainofnode = list_of_ids[i]
        # self.chain.blockchain = chain
        # for i in range(len(self.ring)):
        #     if self.ring[i]['id']==self.id:
        #         continue
        #     self.ring[i]['balance'] = ring[i]['balance']
        #print("Chose longest chain from "+ str(chosechainofnode))
            
		#resolve correct chain
