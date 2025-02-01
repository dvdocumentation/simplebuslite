from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

from pelicandb import Pelican

import json

import os
import pathlib

import time

import os.path

from werkzeug.security import generate_password_hash, check_password_hash
import socket


connected = []

WSPORT=7000

PING = 0x9
PONG = 0xA

NO_AUTHORIZATION = 'NO AUTHORIZATION'

UID_REQUIRED=False
CHECK_USER=False

clients = []
clients_socket_id = {}
clients_id_socket = {}
tokens = {}

APP_PATH=str(pathlib.Path(__file__).parent.absolute())

maindb = Pelican("SimpleBusDB", path =APP_PATH)

tempfiles = os.listdir( maindb._basepath)

for item in tempfiles:
    if item.endswith(".lock"):
        os.remove( os.path.join( maindb._basepath, item ) )

instant_confirm = []
  
maindb['users'].insert({"_id":"admin","password": generate_password_hash("12345")},upsert=True)    
maindb['users'].insert({"_id":"user1","password": generate_password_hash("12345")},upsert=True)    
#maindb['users'].insert({"_id":"user1c","password": generate_password_hash("12345")},upsert=True)    


def ping_sockets():
   while True:
      for client in clients:
         client.sendMessage(json.dumps({"type":"ping"}))
      time.sleep(1)   


class SimpleChat(WebSocket):

    def handleMessage(self):

       global clients_socket_id
       global clients_id_socket
       
       global instant_confirm

       try:
         message = json.loads(self.data)

         if UID_REQUIRED:
            if not "uid" in message:
               self.sendMessage(json.dumps({"type":"ERROR","data":message}))

         if message.get("type") == "connect_token" and "token" in message:
            if not message.get("token") in tokens:
               tokens[message.get("token")]={}

            if CHECK_USER:
                     id = message.get("data")
                     password = message.get("password")
                     user = maindb["users"].get(id)
            
                     if user==None:
                           self.close(1002,NO_AUTHORIZATION)
                     else:
                        if not check_password_hash(user['password'], password):
                           print(self.address, 'closed')
                           self.close(1002,NO_AUTHORIZATION)
                        else:   
                           tokens[message.get("token")][message.get("from")] = self  
            else:                
               tokens[message.get("token")][message.get("from")] = self  
         
         elif message.get("type") == "onlinews":
            if message.get("token") in tokens:
               if "to" in message:

                  if message.get("to") in tokens[message.get("token")]:
            
                     try:
                           tokens[message.get("token")][message.get("to")].sendMessage(json.dumps(message,ensure_ascii=False))
                     except:   
                        print("Not delivered")
            else:
               if "to" in message: 
                     
                     if message.get("to") in clients_id_socket:
                        clients_id_socket[message.get("to")].sendMessage(json.dumps(message))

           

         elif message.get("type") == "connect":
            if "token" in message:
               if  message.get("token") in tokens:
                  if CHECK_USER:
                     id = message.get("data")
                     password = message.get("password")
                     user = maindb["users"].get(id)
            
                     if user==None:
                           self.close(1002,NO_AUTHORIZATION)
                     else:
                        if not check_password_hash(user['password'], password):
                           print(self.address, 'closed')
                           self.close(1002,NO_AUTHORIZATION)
                        else:   
                           tokens[message.get("token")][message.get("from")] = self
                  else:         
                     tokens[message.get("token")][message.get("from")] = self  
               else:
                  self.close(1002,NO_AUTHORIZATION)   
            else:   
               id = message.get("data")
               password = message.get("password")
               user = maindb["users"].get(id)
      
               if user==None:
                     self.close(1002,NO_AUTHORIZATION)
               else:
                  if not check_password_hash(user['password'], password):
                     print(self.address, 'closed')
                     self.close(1002,NO_AUTHORIZATION)
                  else:   

                     clients_socket_id[self] = id
                     clients_id_socket[id] = self

         

       except Exception  as e:
         print(e)    

    def handleConnected(self):
       global clients

       print(self.address, 'connected')
       

       clients.append(self)
       
       
       

    def handleClose(self):
       global clients

       global clients_socket_id
       global clients_id_socket
       
       id = clients_socket_id[self]

       del clients_socket_id[self]  
       del clients_id_socket[id]  

       clients.remove(self)
       print(self.address, 'closed')
       
    
if __name__ == "__main__":
   #Включить для периодического пинга.
   #t2 = threading.Thread(target=ping_sockets)
   #t2.daemon = True
   #t2.start()
   
   hostname = socket.getfqdn()
   if len(socket.gethostbyname_ex(hostname)[2])==1:
      print("WebSocket URL:","ws://"+str(socket.gethostbyname_ex(hostname)[2][0])+":"+str(WSPORT))
   else:   
      print("WebSocket URL:","ws://"+str(socket.gethostbyname_ex(hostname)[2][1])+":"+str(WSPORT))
   
   
   server = SimpleWebSocketServer('0.0.0.0', WSPORT, SimpleChat)
   server.serveforever() 
