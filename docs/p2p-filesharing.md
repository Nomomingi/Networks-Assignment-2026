# **P2P File Sharing (p2p.py)**

FIle sharing in our app is done over a P2P connection. The sender assumes the role of the server and the receiver takes the role of the client. The main reason for this design decision is to reduce strain on the main TCP server.

### **How the file sharing works**

Before we proceed with the file-sharing workflow, below are some important points:

* In the P2P server, the sender shares files over a LAN. Devices on the same Wi-Fi network can communicate with the sender with no issue. This led to issues where devices not on the same network could not send files to each other because they were protected by a firewall or NAT.
* A fix we came up with was to use **ngrok** to create a public URL so that clients on the internet can communicate with the sender’s local IP.

**Workflow:**

* The sender generates a temporary public URL that maps to the local IP using ngrok.
* The sender relays the file-sharing metadata to the main TCP server, i.e., sender name, filename, ngrok URL, ngrok port, and receiver name/group id.
* The server receives this metadata and relays it to the receiver(s).
* The receivers receive this metadata and create a P2P connection with the sender, who now assumes the role of the server. The sender sends the blobs in chunks, and the receiver receives the chunks and reassembles them upon receipt.
* After all packets are received, the TCP connection and ngrok tunnel are terminated.

**Note:** The main TCP server does not receive any bytes from the sender. It only receives metadata and relays it to receivers.

### **Reasons for using TCP over UDP for file transfer**

TCP guarantees that every packet will be received by the receiver, hence we chose it over UDP. UDP, while faster, does not guarantee that every packet will be received. In cases of blob transfer, if any byte is lost due to unreliable protocols, the file might become corrupt and unusable. Additionally, UDP does not keep track of the order in which packets are sent or received. This means the blobs could be reassembled incorrectly at their destination, resulting in file corruption.

