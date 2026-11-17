# Dynamic SDN Traffic Monitoring and Automatic Blocking

## 1. Overview

The Concurrent File Sharing System uses Software Defined Networking (SDN) to monitor network traffic and dynamically control traffic forwarding.

The Ryu SDN controller communicates with the Open vSwitch using OpenFlow 1.3. It periodically collects flow statistics and calculates traffic rates.

When a client's traffic exceeds the configured threshold, the controller installs a high-priority blocking rule. After the blocking period, the rule is removed automatically, allowing the client to communicate again.

## 2. Configuration

The following parameters are configured in `sdn/controller.py`:

| Parameter | Value | Description |
|---|---:|---|
| MONITOR_INTERVAL | 5 seconds | Flow statistics monitoring interval |
| TRAFFIC_THRESHOLD_MBPS | 5 Mbps | Maximum permitted traffic rate |
| BLOCK_DURATION | 15 seconds | Duration of temporary blocking |
| BLOCK_PRIORITY | 100 | Priority of the blocking rule |

## 3. Working Architecture

1. Mininet creates three hosts: h1, h2 and h3.
2. Open vSwitch (s1) connects all three hosts.
3. Ryu acts as the SDN controller.
4. OpenFlow 1.3 enables communication between Ryu and the switch.
5. Ryu requests flow statistics every five seconds.
6. The controller calculates traffic rates using flow byte counters.
7. If traffic exceeds 5 Mbps, the controller installs a priority 100 blocking rule.
8. The blocking rule expires or is removed after 15 seconds.
9. Normal communication is restored.

## 4. Traffic Monitoring

The controller monitors:

- Source MAC address
- Destination MAC address
- Packet count
- Byte count
- Traffic rate in Mbps

## 5. Dynamic Blocking and Recovery

When a monitored client's traffic exceeds the configured threshold of 5 Mbps, the controller installs a high-priority OpenFlow rule.

The blocking rule:
- Matches the source MAC address of the offending client.
- Uses priority 100.
- Applies the `drop` action to matching packets.
- Has a hard timeout of 15 seconds.

The high-priority rule takes precedence over normal forwarding rules.

After the blocking period, the temporary rule expires automatically, allowing normal forwarding to resume.

The OpenFlow flow table can be inspected using:

```bash
sh ovs-ofctl -O OpenFlow13 dump-flows s1
```

The blocking rule is identified by `priority=100` and `actions=drop`.

## 6. Testing

The following tests were performed:

| Test | Expected result | Observed result |
|---|---|---|
| Network connectivity | All hosts communicate | Passed |
| Flow statistics | Statistics received every 5 seconds | Passed |
| High traffic generation | Traffic exceeds 5 Mbps | Passed |
| Automatic blocking | Priority 100 rule installed | Passed |
| Blocking expiration | Priority 100 rule removed | Passed |
| h2 connectivity | h2 communicates with h3 | Passed |
| h1 recovery | h1 communicates with h3 again | Passed |

## 7. Conclusion

Dynamic SDN traffic monitoring and automatic blocking provide temporary traffic control based on network usage.

The implementation demonstrates how an SDN controller can monitor network statistics, dynamically modify flow rules, temporarily restrict excessive traffic and restore connectivity after the blocking period.
