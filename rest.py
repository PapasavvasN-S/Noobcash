import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import binascii

from Crypto.PublicKey import RSA
import block
import node
import blockchain
import wallet
import transaction
import wallet
import json
import jsonpickle

#import urllib.parse as urlparse
#from urllib.parse import parse_qs


### JUST A BASIC EXAMPLE OF A REST API WITH FLASK



app = Flask(__name__)
CORS(app)
blockchain = blockchain.Blockchain()
current_node = None
port = None
#.......................................................................................

@app.route('/nodes/showring', methods=['GET'])
def show_ring():
    response = {'ring': current_node.ring}
    return jsonify(response), 200


@app.route('/nodes/showbalance', methods=['GET'])
def show_balance():
    response = {'balance': current_node.wallet.balance(current_node.UTXO[current_node.id])}
    return jsonify(response), 200


@app.route('/nodes/showid', methods=['GET'])
def show_id():
    response = {'id': current_node.id}
    return jsonify(response), 200


@app.route('/node/addtoring', methods=['POST'])
def add_to_ring():
    requestData = request.data
    requestDecoded = requestData.decode()
    requestData = json.loads(requestDecoded)
    ip = requestData["ip"]
    port = int(requestData["port"])
    balance = int(requestData["balance"])
    publickey = requestData["publickey"]
    publickey = RSA.importKey(binascii.unhexlify(publickey))
    current_node.register_node_to_ring(publickey,balance,ip,port)
    response = {'message': ('Added node ' + ip + '/' + str(port) +' to ring' )}
    return jsonify(response), 200


@app.route('/node/assignid', methods=['POST'])
def set_my_id():
    requestData = request.data
    requestDecoded = requestData.decode()
    requestData = json.loads(requestDecoded)
    id = int(requestData["id"])
    current_node.id = id
    response = { "message" : ("Sent id = " + str(id) + " to node "+ ip + '/' + str(port) )}
    return jsonify(response),200
    
    

@app.route('/node/updateRing', methods=['POST'])
def update_ring():
    jsonData = request.json['ring']
    ring = jsonpickle.decode(jsonData)
    current_node.ring = ring
    return "Ring Updated OK" ,200
    
    
@app.route('/node/updateUTXO', methods=['POST'])
def update_UTXO():
    jsonData = request.json['UTXO']
    UTXO = jsonpickle.decode(jsonData)
    current_node.UTXO = UTXO
    return "UTXO Updated OK" ,200



@app.route('/node/updateChain', methods=['POST'])
def update_chain():
    jsonData = request.json['chain']
    chain = jsonpickle.decode(jsonData)
    if current_node.validate_chain(chain):
        current_node.chain = chain
    return "Chain Updated OK" ,200
    

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    response = []
    for t in current_node.chain.blockchain[-1].listOfTransactions:
        response.append({'sender id: ' : t.sender_id,
                         'receiver id: ' : t.receiver_id,
                         'amount: ' : t.amount
                         })
    return jsonify(response),200

@app.route('/transaction/create/<int:receiver_id>/<int:amount>')
def create_transaction(receiver_id, amount):
    t = current_node.create_transaction(current_node.wallet.public_key, current_node.wallet.private_key, current_node.ring[receiver_id]['address'], amount, current_node.id, receiver_id)
#    response = { "message" : ("Transaction Done from id = " + str(current_node.id) + " to id =  "+ receiver_id + 'the amount of ' + str(amount)  + ' and now we have ' + str(t.transaction_outputs[0]['amount']) + ',  ' + str(t.transaction_outputs[1]['amount']))}
    return "Creating transaction", 200    
    
    
@app.route('/block/add', methods=['POST'])
def add_block():
    jsonData = request.json['block']
    block = jsonpickle.decode(jsonData)
    if (current_node.validate_block(block,current_node.chain.blockchain)):
        flag = False
        for block2 in current_node.chain.blockchain:
            if (block2.index == block.index):
                flag= True
                block2 == block
        if (not flag): 
            current_node.chain.add_block(block)
    #elif len(current_node.chain.blockchain)!=0:
        #if (current_node.chain.blockchain[-1].current_hash!=block.previous_hash):
    else:
        current_node.resolve_conflicts()
        
    return "Block added", 200
    

    
    
@app.route('/transaction/validate', methods=['POST'])
def validate_transaction():
    jsonData = request.json['transaction']
    transaction = jsonpickle.decode(jsonData)
    is_valid = current_node.validate_transaction(transaction)
    if (is_valid):
        print("Transaction validated by node "+ str(current_node.id))
        current_node.add_transaction_to_block(transaction)
        return "Transaction OK" , 200
    else:
        return "Transaction is Not Valid", 400
        
 
@app.route('/node/sendChain', methods=['GET'])
def Chain():
    return {'chain': jsonpickle.encode(current_node.chain.blockchain)}

    
@app.route('/chain/print', methods=['GET'])
def print_blockchain():    
    current_node.chain.print_chain()
    return jsonify({}),200
        
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port' ,type=int, help='port to listen on')
    parser.add_argument('-ip', '--ipaddress' ,type=str, help='port to listen on')
    parser.add_argument('-cap', '--capacity' ,type=int, help='the capacity of the block')
    parser.add_argument('-diff', '--difficulty' ,type=int, help='the block difficulty, number of "0" the hash starts with')
    args = parser.parse_args()
    port = args.port
    ip = args.ipaddress
    block_capacity = args.capacity
    block_difficulty = args.difficulty
    current_node = node.Node(ip,port,5000,'127.0.0.1',block_capacity, block_difficulty)
    app.run(host = '127.0.0.1', port = port)