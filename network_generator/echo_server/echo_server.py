
import socket
import threading
import sys
from multiprocessing.pool import ThreadPool
import json

TIMEOUT=0.1
MAXMSG=2048

def server_loop(addr_port):
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.settimeout(TIMEOUT)
        try:
            sock.bind(addr_port)
        except:
            print(f'Failed to bind to address {repr(addr_port)}')
            sys.stdout.flush()
            sys.exit()

        while True:
            try:
                data, rec_addr_port = sock.recvfrom(MAXMSG)
                deserialized=json.loads(data.decode())
                host=deserialized['from']
                request=deserialized['message']
                print(f'Request received from {host}: {request}')
                sys.stdout.flush()

                deserialized['from']=socket.gethostname()
                data=json.dumps(deserialized).encode()
                sock.sendto(data, rec_addr_port)
            except:
                pass



def send_and_receive(message,addr_port):
    message_raw=message.encode()
    data=b''
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.settimeout(TIMEOUT)
            sock.connect(addr_port)
            sock.sendall(message_raw)
            data, _ = sock.recvfrom(MAXMSG)
        
    except:
        pass
    return data.decode()



def client_loop(addr_ports):
    with ThreadPool(processes=len(addr_ports)) as pool:
        while True:
            tasks=[]
            try:
                message=sys.stdin.readline()[:-1]
                
                if message=='quit':
                    break
                
                print(f'You entered: {message}')
                deserialized={'from':socket.gethostname(),'message':message}
                serialized=json.dumps(deserialized)
                for addr_port in addr_ports:
                    tasks.append( pool.apply_async(send_and_receive,
                                                    args=(serialized,addr_port)) )
            except:
                break
            else:
                replies={}
                for t in tasks:
                    serialized=t.get()
                    if not serialized: continue
                    deserialized=json.loads(serialized)
                    replies.update({deserialized['from']:deserialized['message']})
                
                for host in sorted(replies.keys()):
                    reply=replies[host]
                    print(f'Reply received from {host}: {reply}')
                sys.stdout.flush()


def read_json(filename='knownhosts.json'):
    try:
        with open(filename,'r') as fp:
            deserialized=json.load(fp)
    except:
        print('Could not open json file!')
        sys.stdout.flush()
        sys.exit()
    
    self_addrport=()
    addrports=[]

    my_name=socket.gethostname()
    hosts_info=deserialized['hosts']
    for host,info in hosts_info.items():
        if host==my_name:
            self_addrport=(info['ip_address'], info['udp_start_port'])
        else:
            addrports.append((info['ip_address'], info['udp_start_port']))
    
    return self_addrport, addrports

    

def main():
    self_addrport,addrports=read_json()

    sever_thread=threading.Thread(target=server_loop, args=(self_addrport,),daemon=True)

    sever_thread.start()

    client_loop(addrports)



if __name__=='__main__':
    main()