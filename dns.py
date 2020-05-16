import sys
import socket
import dnslib
import threading
import time
import random
import pickle


LISTENING_ADDRESS = ('localhost', 53)
DNS_SERVERS = [('8.8.8.8', 53), ]
CACHE = {}


def listen(listening_socket):
    data = None
    try:
        data, addr = listening_socket.recvfrom(1024)
        print('Request from {}:{}'.format(addr[0], addr[1]))
    except OSError:        
        raise ConnectionError()
    return data


def hit(question):
    return question.qname in CACHE and question.qtype in CACHE[question.qname]


def get_time_in_sec():
    return int(time.time())


def filter_questions(record):
    hits = []
    for question in record.questions:
        if hit(question):
            _, end_time = CACHE[question.qname][question.qtype]
            print('Record:{} type:{} endtime:{} contains in cache'.format(question.qname, question.qtype, time.ctime(end_time)))
            hits.append(question)
        else:
            print('Record:{} type:{} not contains in cache'.format(question.qname, question.qtype))
    for question in hits:
        record.questions.remove(question)
    if record.questions:
        return record
    return None


def fill_cache(record):
    for question in record.rr:
        if question.rname in CACHE:
            CACHE[question.rname][question.rtype] = (question, get_time_in_sec() + question.ttl)
        else:
            CACHE[question.rname] = { question.rtype: (question, get_time_in_sec() + question.ttl) }


def handle_request(listening_socket, working_socket):
    try:
        data = listen(listening_socket)
        if data:
            record = filter_questions(dnslib.DNSRecord.parse(data))
            if record:
                try:
                    server = random.choice(DNS_SERVERS)
                    working_socket.sendto(record.pack(), server)                
                    print('Request to {}:{}'.format(server[0], server[1]))                    
                except OSError:
                    pass                
    except OSError:
        pass
        

def handle_reply(working_socket):
    try:
        data, addr = working_socket.recvfrom(1024)
        print('Reply from {}:{}'.format(addr[0], addr[1]))
        record = dnslib.DNSRecord.parse(data)
        fill_cache(record)        
    except OSError:
        pass


def on_exit(*args):
    print('Saving cache...')
    with open('saved_cache.pickle', 'wb') as f:
            pickle.dump(CACHE, f)
    print('Closing...')
    time.sleep(1)
    sys.exit(0)


def check_cache():
    removed = []
    for rname in CACHE:
        for rtype in CACHE[rname]:
            _, end_time = CACHE[rname][rtype]
            if end_time < get_time_in_sec():
                removed.append((rname, rtype))
    for rname, rtype in removed:
        del CACHE[rname][rtype]


if __name__ == '__main__':
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    working_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listening_socket.bind(LISTENING_ADDRESS)
    listening_socket.settimeout(0)    
    working_socket.settimeout(0)
    timer = time.time()

    try:
        print('Starting server...')
        print('Searching cache...')
        try:
            with open('saved_cache.pickle', 'rb') as f:
                CACHE = pickle.load(f)
                print("Cache was found")
                check_cache()
                print("Cache was updated")
        except IOError:
            print("Cache wasn't found")
        while True:
            handle_request(listening_socket, working_socket)
            handle_reply(working_socket)
            if time.time() - timer > 60:
                check_cache()
                timer = time.time()
            time.sleep(0.1)
    except:
        pass 
    finally:
        print('Stopping server...')
        listening_socket.close()        
        working_socket.close()
        on_exit()