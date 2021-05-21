import blockchain
import hashlib
import json
import transaction
import copy

class Block:
    def __init__(self, index, timestamp, transactions, nonce, previous_hash, capacity, difficulty):
        self.index = index
        self.timestamp = timestamp
        self.nonce = nonce
        self.previous_hash = previous_hash
        self.current_hash = self.myHash(nonce)
        self.capacity = capacity
        self.difficulty = difficulty
        self.listOfTransactions=[]


    def myHash(self, nonce):
        self.block_data = {
            'block_index': self.index,
            'block_previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'block_nonce': self.nonce
            }
        block_serialized = json.dumps(self.block_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(block_serialized).hexdigest()

	#def add_transaction(transaction transaction, blockchain blockchain):
    def add_transaction(self, transaction):
        self.listOfTransactions.append(transaction)

        
    def print_block(self):
        print("***************************************************")
        print("index = " + str(self.index))
        print("nonce = " + str(self.nonce))
        print("current_hash = " + self.current_hash)
        print("capacity = " + str(self.capacity))
        print("difficulty = " + str(self.difficulty))
        print("listOfTransactions = " + str(len(self.listOfTransactions)))
        print("***************************************************")
