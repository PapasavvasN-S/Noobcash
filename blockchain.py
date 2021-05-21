# -*- coding: utf-8 -*-
import json
import copy
import block

class Blockchain:
    
    def __init__(self):
        self.blockchain = []
    
    def add_block(self, block):
        self.blockchain.append(block)

    def print_chain(self):
        for block in self.blockchain:
            block.print_block()