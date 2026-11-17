# Concurrent File Sharing System Using SDN

## 1. Project Overview

The Concurrent File Sharing System is a client-server application developed using Python TCP sockets and Software Defined Networking (SDN).

The project allows multiple clients to upload, list, and download files through a centralized server.

Mininet is used to create the virtual network, Open vSwitch acts as the software-based switch, and the Ryu SDN Controller manages packet forwarding using OpenFlow 1.3.

The system also provides user authentication, secure password hashing, concurrent file transfers, and SHA-256 file integrity verification.

## 2. Objectives

- Develop a centralized file-sharing application.
- Support multiple clients communicating with a server.
- Implement concurrent file uploads and downloads.
- Integrate SDN using Mininet, Open vSwitch, and Ryu.
- Implement user authentication.
- Verify file integrity using SHA-256.
- Analyze network communication using Wireshark.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| TCP Sockets | Client-server communication |
| Mininet | Virtual network emulation |
| Open vSwitch | Software-based network switching |
| Ryu | SDN controller |
| OpenFlow 1.3 | SDN communication protocol |
| SQLite | User and file metadata storage |
| Argon2 | Password hashing |
| SHA-256 | File integrity verification |
| Wireshark | Network traffic analysis |

## 4. System Architecture

The network consists of three hosts connected to one Open vSwitch.

```text
             Ryu Controller
              127.0.0.1
               Port 6653
                   |
              OpenFlow 1.3
                   |
                +-----+
                | s1  |
                | OVS |
                +-----+
                /  |  \
               /   |   \
            +----+ +----+ +----+
            | h1 | | h2 | | h3 |
            +----+ +----+ +----+
            Client Client  Server
              1      2
```

### IP Addressing

| Device | IP Address | Role |
|---|---|---|
| h1 | 10.0.0.1 | Client 1 |
| h2 | 10.0.0.2 | Client 2 |
| h3 | 10.0.0.3 | File Server |
| s1 | Open vSwitch | Network Switch |

- Network: 10.0.0.0/24
- OpenFlow controller port: 6653
- File server TCP port: 5000
- OpenFlow version: 1.3

For detailed network information, refer to [Network Topology](docs/NETWORK_TOPOLOGY.md).

## 5. Features

### User Authentication
- User registration.
- User login and logout.
- Password hashing using Argon2.
- Authentication required for file operations.

### File Management
- Upload files to the centralized server.
- List available files.
- Download files using their file IDs.
- Store file metadata in SQLite.

### Concurrent File Transfer
- Multiple clients can upload files simultaneously.
- Multiple clients can download files simultaneously.
- Client connections are handled using separate threads.

### File Integrity
- SHA-256 hash calculation.
- File size verification.
- Integrity verification after file transfer.
- Cleanup of incomplete uploads.

### SDN Integration
- Mininet virtual network.
- Open vSwitch with OpenFlow 1.3.
- Ryu-based MAC learning and packet forwarding.
- Dynamic flow entry installation.

## 6. Project Structure

```text
concurrent-file-sharing/
│
├── app/
│   ├── server.py
│   ├── protocol.py
│   ├── auth.py
│   └── storage.py
│
├── sdn/
│   ├── topology.py
│   └── controller.py
│
├── tests/
│   ├── test_protocol.py
│   ├── test_file_transfer.py
│   ├── test_server.py
│   ├── test_interrupted_upload.py
│   ├── test_concurrent.py
│   ├── test_simultaneous_downloads.py
│   ├── test_invalid_filename.py
│   ├── test_invalid_requests.py
│   └── test_malformed_request.py
│
├── docs/
│   ├── NETWORK_TOPOLOGY.md
│   └── CONFIGURATION.md
│
├── demo_files/
├── client.py
├── test_upload.py
├── requirements.txt
└── README.md
```

## 7. Requirements

- Linux environment (Ubuntu recommended).
- Python 3.
- Mininet.
- Open vSwitch.
- Ryu SDN Controller.
- Wireshark (for packet analysis).

## 8. Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/concurrent-file-sharing-system.git
cd concurrent-file-sharing-system
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

The Ryu controller should be installed in a separate Python environment with its required dependencies.

Mininet and Open vSwitch must also be installed and configured on the system.

## 9. Running the Project

### Terminal 1: Start Ryu Controller

```bash
source ~/ryu-venv/bin/activate
cd sdn
ryu-manager --ofp-tcp-listen-port 6653 controller.py
```

### Terminal 2: Start Mininet

```bash
sudo mn -c
cd ~/Documents/concurrent-file-sharing/sdn

sudo mn --custom topology.py --topo filesharing --controller remote,ip=127.0.0.1,port=6653 --switch ovs,protocols=OpenFlow13
```

### Start File Server on h3

From the Mininet CLI:

```bash
h3 bash -c 'cd /home/yash/Documents/concurrent-file-sharing && .venv/bin/python -m app.server > /tmp/fileshare-server.log 2>&1 &'
```

Replace `/home/yash/Documents/concurrent-file-sharing` with the actual project path on your system if different.

### Verify Server

```bash
h3 pgrep -af app.server
h3 ss -ltnp | grep 5000
```

### Start Client Applications

From the Mininet CLI:

```bash
xterm h1 h2
```

In both client terminals:

```bash
cd /home/yash/Documents/concurrent-file-sharing

FILESHARE_SERVER=10.0.0.3 FILESHARE_PORT=5000 .venv/bin/python client.py
```

Register or log in and use the client menu to upload, list, download, and log out.

## 10. Testing

Run the tests from the project root with the application virtual environment activated.

```bash
python -m tests.test_protocol
python -m tests.test_file_transfer
python -m tests.test_server
python -m tests.test_interrupted_upload
python -m tests.test_concurrent
python -m tests.test_simultaneous_downloads
python -m tests.test_invalid_filename
python -m tests.test_invalid_requests
python -m tests.test_malformed_request
```

The server must be running for integration tests that connect to TCP port 5000.

For interactive file upload testing:

```bash
python test_upload.py
```

## 11. Network Testing

From the Mininet CLI:

```bash
net
pingall
h1 ping -c 3 h2
h1 ping -c 3 h3
h2 ping -c 3 h3
```

Inspect OpenFlow rules:

```bash
sh ovs-ofctl -O OpenFlow13 dump-flows s1
```

## 12. Wireshark Analysis

Wireshark is used to capture and analyze network traffic.

The following activities are demonstrated:

- TCP three-way handshake.
- Client-to-server file upload traffic.
- Concurrent uploads from multiple clients.
- Server-to-client file download traffic.

Useful display filter:

```text
tcp.port == 5000
```

Detailed configuration instructions are available in [Configuration](docs/CONFIGURATION.md).

## 13. Security and Reliability

- Passwords are hashed using Argon2.
- File operations require authentication.
- Invalid filenames are rejected.
- File size is checked during transfers.
- SHA-256 is used for file integrity verification.
- Incomplete upload files are cleaned up.
- Concurrent client connections are handled using threads.

## 14. Documentation

- [Network Topology](docs/NETWORK_TOPOLOGY.md)
- [Configuration Guide](docs/CONFIGURATION.md)

## 15. Future Enhancements

- Graphical user interface.
- File access permissions.
- Improved SDN traffic management.
- Transfer progress monitoring.
- Extended network performance analysis.

## 16. Author

Developed as an academic Computer Networks project.

## 17. License

This project is intended for educational and academic purposes.
