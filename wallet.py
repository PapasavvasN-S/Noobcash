import binascii

from Crypto.PublicKey import RSA


class Wallet:

    def __init__(self):
        temp_key = RSA.generate(2048)
        self.private_key = binascii.hexlify(temp_key.exportKey()).decode()
        self.public_key = binascii.hexlify(temp_key.publickey().exportKey()).decode()

    def balance(self, UTXOs):
        balance = 0
        for transaction in UTXOs:
            balance += transaction['amount']
        return balance