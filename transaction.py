from collections import OrderedDict

import binascii
import copy
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import requests
#from flask import Flask, jsonify, request, render_template

import hashlib
import json

class Transaction:

    def __init__(self, sender_address, sender_private_key, recipient_address, value, inputs, sender_id, receiver_id):
        self.sender_address = sender_address 
        self.receiver_address = recipient_address  
        self.amount = value 
        self.transaction_inputs = inputs  
        self.transaction_id = hashlib.sha256((str(self.sender_address) + str(self.receiver_address) + str(self.amount) + json.dumps(self.transaction_inputs)).encode('utf-8')).hexdigest()
        self.transaction_outputs = []
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        
        if(str(sender_address) == str('0')):
            trans_out = {
            'transaction_id': self.transaction_id,
            'receiver_id': receiver_id,
            'amount': self.amount
            }
            trans_out = json.dumps(trans_out)
            trans_out = json.loads(trans_out)
            self.transaction_outputs.append(trans_out)
        else:
            total_nbc = 0
            for transaction in self.transaction_inputs:
                total_nbc += transaction['amount']
            changes = total_nbc - self.amount
            self.transaction_outputs = []
            trans_out1 = {
            'transaction_id': self.transaction_id,
            'receiver_id': receiver_id,
            'amount': self.amount
            }
            trans_out1 = json.dumps(trans_out1)
            trans_out1 = json.loads(trans_out1)
            self.transaction_outputs.append(trans_out1)
            if (changes > 0):
                trans_out2 = {
                'transaction_id': self.transaction_id,
                'receiver_id': sender_id,
                'amount': changes
                }
                trans_out2 = json.dumps(trans_out2)
                trans_out2 = json.loads(trans_out2)
                self.transaction_outputs.append(trans_out2)
            
            self.signature = self.sign_transaction(sender_private_key)

    def sign_transaction(self, sender_private_key):
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(sender_private_key)))
        h = SHA.new((str(self.sender_address) + str(self.receiver_address) + str(self.amount) + json.dumps(self.transaction_inputs)).encode('utf-8'))
        signature = signer.sign(h)
        return signature
    
       
    def verify_transaction(self):
         h = SHA.new((str(self.sender_address) + str(self.receiver_address) + str(self.amount) + json.dumps(self.transaction_inputs)).encode('utf-8'))
         verifier = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.sender_address)))
         return verifier.verify(h, self.signature)
