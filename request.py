import socket
import dnslib
import pickle

SERVER_ADDRESS = ('localhost', 53)

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
data = dnslib.DNSRecord.question("ya.ru", 'MX')
data.add_question(dnslib.DNSQuestion("mail.ru"))
socket.sendto(data.pack(), SERVER_ADDRESS)
socket.close()