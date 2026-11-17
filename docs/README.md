# Concurrent File Sharing System Using SDN

## 1. Project Overview

The Concurrent File Sharing System is a client-server application developed using Python TCP sockets and Software Defined Networking (SDN).

The project allows multiple clients to upload, list, and download files through a centralized server.

Mininet is used to create the virtual network, Open vSwitch acts as the software-based switch, and the Ryu SDN Controller manages packet forwarding using OpenFlow 1.3.

The system also provides user authentication, secure password hashing, concurrent file transfers, SHA-256 file integrity verification, and dynamic SDN traffic monitoring.

## 2. Objectives

- Develop a centralized file-sharing application.
- Support multiple clients communicating with a server.
- Implement concurrent file uploads and downloads.
- Integrate SDN using Mininet, Open vSwitch, and Ryu.
- Implement user authentication.
- Verify file integrity using SHA-256.
- Implement dynamic traffic monitoring and automatic flow blocking.
- Analyze network communication using Wireshark.
- Evaluate network performance using iperf.

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
| iperf | Network throughput measurement |

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

- Network: `10.0.0.0/24`
- OpenFlow controller port: `6653`
- File server TCP port: `5000`
- OpenFlow version: `1.3`

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
- Dynamic OpenFlow flow entry installation.
- Periodic traffic statistics monitoring.
- Automatic client traffic blocking when the configured threshold is exceeded.
- Automatic recovery after the blocking period.

## 6. Dynamic SDN Traffic Monitoring and Automatic Blocking

The project implements dynamic traffic monitoring using the Ryu SDN controller and OpenFlow 1.3.

### Configuration

| Parameter | Value |
|---|---:|
| Monitoring interval | 5 seconds |
| Traffic threshold | 5 Mbps |
| Blocking duration | 15 seconds |
| Blocking rule priority | 100 |

### Working

1. Ryu periodically requests flow statistics from Open vSwitch.
2. The controller calculates traffic rates using byte-counter differences.
3. When a monitored client exceeds the configured traffic threshold, the controller installs a high-priority blocking rule.
4. The switch drops matching packets using an OpenFlow drop action.
5. After the blocking period, the temporary rule expires and normal communication can resume.
6. The controller continues monitoring traffic.

### Demonstrated Results

- Traffic statistics were successfully collected.
- Traffic exceeding the 5 Mbps threshold was detected.
- A priority-100 blocking rule was installed.
- The flow table confirmed the `actions=drop` rule.
- The blocking rule was removed after the configured period.
- h2 maintained connectivity with h3 while h1 was blocked.
- Connectivity was restored after recovery.

For implementation details, refer to [Dynamic SDN Documentation](docs/DYNAMIC_SDN.md).

## 7. Project Structure

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
│   ├── CONFIGURATION.md
│   ├── DYNAMIC_SDN.md
│   ├── PERFORMANCE_EVALUATION.md
│   └── README.md
│
├── demo_files/
├── client.py
├── test_upload.py
├── requirements.txt
└── README.md
```

## 8. Requirements

- Linux environment (Ubuntu recommended).
- Python 3.
- Mininet.
- Open vSwitch.
- Ryu SDN Controller.
- Wireshark (for packet analysis).
- iperf (for throughput testing).

## 9. Installation

Clone the repository:

```bash
git clone https://github.com/Yash13032007/concurrent-file-sharing-system.git
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

## 10. Running the Project

The following commands assume the repository is located at:

`~/Documents/concurrent-file-sharing`

Adjust the project path if your installation is different.

### Terminal 1: Start Ryu Controller

```bash
source ~/ryu-venv/bin/activate
cd ~/Documents/concurrent-file-sharing/sdn
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

## 11. Testing

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

## 12. Network Testing

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

Test TCP bandwidth:

```bash
iperf h1 h3
```

## 13. Wireshark Analysis

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

## 14. Performance Evaluation

Network throughput was measured using iperf in Mininet.

The baseline test was conducted with a high traffic threshold to prevent normal test traffic from triggering automatic blocking.

The dynamic SDN configuration was tested with a 5 Mbps threshold.

The observed throughput varied between test runs. These measurements are preliminary virtual-network observations and should not be interpreted as a controlled benchmark or proof of throughput improvement.

For the test results and methodology, refer to [Performance Evaluation](docs/PERFORMANCE_EVALUATION.md).

## 15. Security and Reliability

- Passwords are hashed using Argon2.
- File operations require authentication.
- Invalid filenames are rejected.
- File size is checked during transfers.
- SHA-256 is used for file integrity verification.
- Incomplete upload files are cleaned up.
- Concurrent client connections are handled using threads.

## 16. Documentation

- [Network Topology](docs/NETWORK_TOPOLOGY.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Dynamic SDN Documentation](docs/DYNAMIC_SDN.md)
- [Performance Evaluation](docs/PERFORMANCE_EVALUATION.md)

## 17. Future Enhancements

- Graphical user interface.
- File access permissions.
- Improved SDN traffic management.
- Transfer progress monitoring.
- Extended network performance analysis.

## 18. Author

Developed as an academic Computer Networks project.

## 19. License

This project is intended for educational and academic purposes.
