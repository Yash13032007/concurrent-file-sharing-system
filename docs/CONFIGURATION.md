# Project Configuration

## 1. Project Environment

The Concurrent File Sharing System uses the following technologies:

| Technology | Purpose |
|---|---|
| Python | File sharing application |
| TCP Sockets | Client-server communication |
| Mininet | Virtual network emulation |
| Open vSwitch | Software-based network switch |
| Ryu | SDN controller |
| OpenFlow 1.3 | Switch-controller communication |
| SQLite | User and file metadata storage |
| SHA-256 | File integrity verification |
| Argon2 | Password hashing |

## 2. Network Configuration

| Parameter | Value |
|---|---|
| Network | 10.0.0.0/24 |
| Client 1 | 10.0.0.1 |
| Client 2 | 10.0.0.2 |
| File Server | 10.0.0.3 |
| Switch | s1 |
| Controller | 127.0.0.1 |
| OpenFlow Version | OpenFlow 1.3 |
| Controller Port | 6653 |
| File Server Port | 5000 |

## 3. Python Environment

The project uses a Python virtual environment named `.venv`.

Activate it from the project directory:

```bash
source .venv/bin/activate
```

Install application dependencies:

```bash
pip install -r requirements.txt
```

The Ryu controller uses a separate virtual environment:

```bash
source ~/ryu-venv/bin/activate
```

## 4. Start the Ryu Controller

Open Terminal 1:

```bash
source ~/ryu-venv/bin/activate
cd ~/Documents/concurrent-file-sharing/sdn
ryu-manager --ofp-tcp-listen-port 6653 controller.py
```

## 5. Start the Mininet Network

Open Terminal 2:

```bash
sudo mn -c
cd ~/Documents/concurrent-file-sharing/sdn
sudo mn --custom topology.py --topo filesharing --controller remote,ip=127.0.0.1,port=6653 --switch ovs,protocols=OpenFlow13
```

## 6. Start the File Sharing Server

From the Mininet CLI:

```bash
h3 bash -c 'cd /home/yash/Documents/concurrent-file-sharing && .venv/bin/python -m app.server > /tmp/fileshare-server.log 2>&1 &'
```

Verify the server:

```bash
h3 pgrep -af app.server
h3 ss -ltnp | grep 5000
```

## 7. Start Client Applications

Open client terminals:

```bash
xterm h1 h2
```

In both client terminals, run:

```bash
cd /home/yash/Documents/concurrent-file-sharing
FILESHARE_SERVER=10.0.0.3 FILESHARE_PORT=5000 .venv/bin/python client.py
```

## 8. Network Verification

From the Mininet CLI:

```bash
net
pingall
h1 ping -c 3 h2
h1 ping -c 3 h3
h2 ping -c 3 h3
```

Check switch flow entries:

```bash
sh ovs-ofctl -O OpenFlow13 dump-flows s1
```

## 9. Server Communication

The application uses TCP socket communication.

| Operation | Description |
|---|---|
| Register | Create a user account |
| Login | Authenticate a user |
| Logout | End the authenticated session |
| Upload | Upload a file to the server |
| List | View available files |
| Download | Download a file using its ID |

The application uses length-prefixed JSON messages for control communication and an 8-byte file-size prefix for file transfers.

## 10. File Storage

| Location | Purpose |
|---|---|
| shared_files/ | Uploaded files stored by the server |
| downloads/ | Downloaded files |
| logs/ | Server logs |
| fileshare.db | SQLite database |
| demo_files/ | Prepared demonstration input files |

## 11. Shutdown Procedure

1. Log out from client applications.
2. Close client terminals.
3. Stop Wireshark if running.
4. Exit Mininet:

```bash
exit
```

5. Stop the Ryu controller using Ctrl+C.
6. Clean up Mininet:

```bash
sudo mn -c
```
