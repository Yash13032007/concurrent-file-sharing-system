# Network Topology

## 1. Overview

The Concurrent File Sharing System uses Software Defined Networking (SDN)
with Mininet, Open vSwitch, and the Ryu SDN Controller.

The network consists of three hosts connected to one Open vSwitch.

- h1: Client 1
- h2: Client 2
- h3: File sharing server
- s1: Open vSwitch

The Ryu controller manages the forwarding behavior of the switch using
OpenFlow 1.3.

## 2. Network Architecture

```text
             Ryu SDN Controller
                (127.0.0.1)
                Port: 6653
                     |
                OpenFlow 1.3
                     |
                 +-------+
                 |  s1   |
                 | OVS   |
                 +-------+
                 /   |   \
                /    |    \
               /     |     \
            +----+ +----+ +----+
            | h1 | | h2 | | h3 |
            +----+ +----+ +----+
              |      |      |
           Client 1 Client 2 Server

         Network: 10.0.0.0/24
```

## 3. IP Addressing

| Device | IP Address | Role |
|--------|------------|------|
| h1 | 10.0.0.1/24 | Client 1 |
| h2 | 10.0.0.2/24 | Client 2 |
| h3 | 10.0.0.3/24 | File Server |
| s1 | Open vSwitch | Network Switch |

All three hosts belong to the same subnet: 10.0.0.0/24.

## 4. Network Components

### Mininet

Mininet creates the virtual network containing three hosts and one switch.

### Open vSwitch

The Open vSwitch named s1 connects all three hosts.

It uses OpenFlow 1.3 to communicate with the Ryu controller.

### Ryu SDN Controller

The Ryu controller implements MAC learning.

Its responsibilities include:

- Receiving packet-in events.
- Learning source MAC addresses and their switch ports.
- Flooding packets when the destination MAC is unknown.
- Forwarding packets to known destination ports.
- Installing flow entries in the switch.

### File Sharing Server

The Python TCP server runs on h3.

- Server IP: 10.0.0.3
- Server port: 5000

Clients h1 and h2 communicate with the server using TCP.

## 5. Communication Flow

1. The Ryu controller starts and listens for OpenFlow connections.
2. Mininet creates the network and connects s1 to the controller.
3. The controller installs a table-miss flow entry that sends unmatched packets to the controller.
4. Hosts communicate through the Open vSwitch.
5. The controller learns MAC addresses from incoming packets.
6. Unknown destinations are flooded.
7. Known destinations are forwarded using installed flow entries.
8. Clients connect to the file sharing server on h3 using TCP port 5000.
9. Multiple clients can upload and download files concurrently.

## 6. Protocols and Ports

| Protocol | Port | Purpose |
|----------|------|---------|
| OpenFlow | 6653 | Switch-controller communication |
| TCP | 5000 | File sharing communication |
| Ethernet | Layer 2 | Host-to-host frame delivery |

## 7. Topology File

The Mininet topology is implemented in:

`sdn/topology.py`

The Ryu controller is implemented in:

`sdn/controller.py`

The topology uses the name `filesharing`.

## 8. Verification Commands

From the Mininet CLI:

```bash
net
pingall
h1 ping -c 3 h2
h1 ping -c 3 h3
h2 ping -c 3 h3
sh ovs-ofctl -O OpenFlow13 dump-flows s1
```

These commands verify network connectivity and inspect the OpenFlow rules installed on the switch.

