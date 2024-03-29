import socket
import sys
import thread
import time
import ssl
import Queue

def main(handlerPort,proxyPort,certificate,privateKey):
    thread.start_new_thread(server, (handlerPort,proxyPort,certificate,privateKey))
    while True:
       time.sleep(60)

def handlerServer(q,handlerPort,certificate,privateKey):
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.load_cert_chain(certificate,privateKey)
    try:
        dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        dock_socket.bind(('', int(handlerPort)))
        dock_socket.listen(5)
        print("Handler listening on: " + handlerPort)
        while True:
            try:
                clear_socket, address = dock_socket.accept()
                client_socket = context.wrap_socket(clear_socket, server_side=True)
                print("Reverse Socks Connection Received: {}:{}".format(address[0],address[1]))
                try:
                    q.get(False)
                except:
                    pass
                q.put(client_socket)
            except Exception as e:
                print(e)
                pass
    except Exception as e:
        print(e)
    finally:
        dock_socket.close()

def getActiveConnection(q):
    try:
        client_socket = q.get(block=True, timeout=10)
    except:
        print('No Reverse Socks connection found')
        return None
    try:
        client_socket.send("HELLO")
    except:
        return getActiveConnection(q)
    return client_socket

def server(handlerPort,proxyPort,certificate,privateKey):
    q = Queue.Queue()
    thread.start_new_thread(handlerServer, (q,handlerPort,certificate,privateKey))
    try:
        dock_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        dock_socket2.bind(('', int(proxyPort)))
        dock_socket2.listen(5)
        print("Socks Server listening on: " + proxyPort)
        while True:
            try:
                client_socket2, address = dock_socket2.accept()
                print("Socks Connection Received: {}:{}".format(address[0],address[1]))
                client_socket = getActiveConnection(q)
                if client_socket == None:
                    client_socket2.close()
                thread.start_new_thread(forward, (client_socket, client_socket2))
                thread.start_new_thread(forward, (client_socket2, client_socket))
            except Exception as e:
                print(e)
                pass
    except Exception as e:
        print(e)
    finally:
        dock_socket2.close()

def forward(source, destination):
    try:
        string = ' '
        while string:
            string = source.recv(1024)
            if string:
                destination.sendall(string)
            else:
                source.shutdown(socket.SHUT_RD)
                destination.shutdown(socket.SHUT_WR)
    except:
        try:
            source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)
        except:
            pass
        pass

if __name__ == '__main__':
    if len(sys.argv) < 5:
	    print("Usage:{} <handlerPort> <proxyPort> <certificate> <privateKey>".format(sys.argv[0]))
    else:
	    main(sys.argv[1], sys.argv[2],sys.argv[3],sys.argv[4])