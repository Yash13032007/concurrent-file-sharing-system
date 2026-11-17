# Performance Evaluation

## 1. Objective

The objective of performance evaluation is to study network throughput and observe the behavior of the Concurrent File Sharing System under different SDN traffic-control configurations.

## 2. Testing Environment

| Component | Configuration |
|---|---|
| Network Emulator | Mininet |
| SDN Controller | Ryu |
| Virtual Switch | Open vSwitch |
| Protocol | OpenFlow 1.3 |
| Hosts | h1, h2, h3 |
| Traffic Testing Tool | iperf |
| Traffic Threshold | 5 Mbps |
| Blocking Duration | 15 seconds |

## 3. Baseline Performance

The baseline test was performed with the traffic threshold configured to 10,000 Mbps, effectively preventing normal test traffic from triggering the blocking mechanism.

| Direction | Measured Throughput |
|---|---:|
| h1 to h3 | 2.91 Gbits/sec |
| h3 to h1 | 3.37 Gbits/sec |

## 4. Dynamic SDN Performance

With dynamic traffic monitoring enabled, the controller monitored OpenFlow statistics and detected traffic exceeding the configured 5 Mbps threshold.

Observed iperf results varied between test runs:

| Test | h1 to h3 | h3 to h1 |
|---|---:|---:|
| 1 | 13.0 Gbits/sec | 13.0 Gbits/sec |
| 2 | 7.12 Gbits/sec | 7.23 Gbits/sec |
| 3 | 6.86 Gbits/sec | 7.01 Gbits/sec |
| 4 | 17.7 Gbits/sec | 17.6 Gbits/sec |
| 5 | 19.2 Gbits/sec | 19.2 Gbits/sec |
| 6 | 21.9 Gbits/sec | 21.9 Gbits/sec |

These are observed virtual-network measurements, not controlled benchmark averages. Results can vary depending on host CPU scheduling, virtual networking, and whether traffic blocking is active.

## 5. Dynamic Traffic Control

The controller was configured with:

- Monitoring interval: 5 seconds
- Traffic threshold: 5 Mbps
- Blocking duration: 15 seconds
- Blocking rule priority: 100

When traffic exceeded the threshold, the controller installed a high-priority OpenFlow drop rule for the offending client.

The switch flow table confirmed the rule using `priority=100` and `actions=drop`.

After the blocking period, the rule was removed automatically and normal monitoring continued.

## 6. Client Isolation Test

During the blocking of h1, connectivity from h2 to h3 was tested.

Result:

- h1: Traffic blocking rule installed.
- h2: Successfully communicated with h3.
- Packet loss for h2 ping test: 0%.

This demonstrates that the traffic-control mechanism can isolate a client without interrupting another client's communication.

## 7. Conclusion

The performance tests demonstrated TCP communication between Mininet hosts and verified the operation of dynamic SDN traffic monitoring, threshold detection, automatic flow blocking, and recovery.

The experiment also demonstrated that the controller can isolate a high-traffic client while maintaining connectivity for another client.
