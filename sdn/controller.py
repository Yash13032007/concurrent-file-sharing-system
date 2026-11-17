import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls
)
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub


# Traffic monitoring configuration
MONITOR_INTERVAL = 5
TRAFFIC_THRESHOLD_MBPS = 5
BLOCK_DURATION = 15
BLOCK_PRIORITY = 100


# Only client MAC addresses are monitored for blocking
# h1 and h2 are clients; h3 is the file server
CLIENT_MACS = {
    'c6:1d:b0:eb:51:3f',  # h1
    'a6:ad:55:cb:a3:46'   # h2
}


class FileSharingController(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):

        super(FileSharingController, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.datapaths = {}

        # Previous flow statistics
        self.previous_stats = {}

        # Currently blocked clients
        self.blocked_macs = {}

        self.logger.info("File Sharing SDN Controller Started")

        self.monitor_thread = hub.spawn(self._monitor)

    # Add a normal forwarding flow
    def add_flow(self, datapath, priority, match, actions):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions
        )

        datapath.send_msg(flow_mod)

    # Track connected switches
    @set_ev_cls(
        ofp_event.EventOFPStateChange,
        [MAIN_DISPATCHER, DEAD_DISPATCHER]
    )
    def state_change_handler(self, ev):

        datapath = ev.datapath

        if ev.state == MAIN_DISPATCHER:

            if datapath.id not in self.datapaths:

                self.datapaths[datapath.id] = datapath

                self.logger.info(
                    "Switch registered: %s",
                    datapath.id
                )

        elif ev.state == DEAD_DISPATCHER:

            if datapath.id in self.datapaths:

                del self.datapaths[datapath.id]

                self.logger.info(
                    "Switch disconnected: %s",
                    datapath.id
                )

    # Periodically request statistics and recover blocked clients
    def _monitor(self):

        last_request = {}

        while True:

            now = time.time()

            for dpid, datapath in list(self.datapaths.items()):

                # Request flow statistics every 5 seconds
                if now - last_request.get(dpid, 0) >= MONITOR_INTERVAL:

                    parser = datapath.ofproto_parser

                    request = parser.OFPFlowStatsRequest(datapath)

                    datapath.send_msg(request)

                    last_request[dpid] = now

                # Recover clients whose blocking period expired
                for key, details in list(self.blocked_macs.items()):

                    blocked_dpid, mac = key
                    expiry, cookie = details

                    if blocked_dpid == dpid and now >= expiry:

                        self.remove_block(datapath, cookie)

                        del self.blocked_macs[key]

                        self.logger.info(
                            "RECOVERY: Blocking removed for client %s",
                            mac
                        )

            hub.sleep(1)

    # Receive flow statistics from Open vSwitch
    @set_ev_cls(
        ofp_event.EventOFPFlowStatsReply,
        MAIN_DISPATCHER
    )
    def flow_stats_reply_handler(self, ev):

        datapath = ev.msg.datapath
        dpid = datapath.id

        now = time.time()

        for stat in ev.msg.body:

            # Process only normal learned forwarding flows
            if stat.priority != 1:
                continue

            src = stat.match.get('eth_src')
            dst = stat.match.get('eth_dst')
            in_port = stat.match.get('in_port')

            # Ignore server and unknown MAC addresses
            if not src or src not in CLIENT_MACS:
                continue

            flow_key = (dpid, src, dst, in_port)

            current_bytes = stat.byte_count

            previous = self.previous_stats.get(flow_key)

            self.previous_stats[flow_key] = (
                current_bytes,
                now
            )

            # First response establishes the baseline
            if previous is None:
                continue

            previous_bytes, previous_time = previous

            elapsed = now - previous_time
            byte_difference = current_bytes - previous_bytes

            if elapsed <= 0 or byte_difference < 0:
                continue

            # Calculate traffic rate in Mbps
            rate_mbps = (
                byte_difference * 8
            ) / (elapsed * 1000000)

            self.logger.info(
                "TRAFFIC STATS: source=%s destination=%s "
                "packets=%s bytes=%s rate=%.3f Mbps",
                src,
                dst,
                stat.packet_count,
                current_bytes,
                rate_mbps
            )

            # Check traffic threshold
            if rate_mbps > TRAFFIC_THRESHOLD_MBPS:

                self.block_client(datapath, src)

    # Dynamically block a client
    def block_client(self, datapath, src_mac):

        dpid = datapath.id
        key = (dpid, src_mac)

        # Only allow configured client MAC addresses
        if src_mac not in CLIENT_MACS:
            return

        # Avoid installing duplicate blocking rules
        if key in self.blocked_macs:
            return

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Unique cookie for this client's blocking rule
        cookie = (
            0xB10C000000000000 |
            int(src_mac.replace(':', ''), 16)
        )

        # Match all Ethernet traffic from this client
        match = parser.OFPMatch(
            eth_src=src_mac
        )

        # Empty instructions mean drop the matching packets
        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            cookie=cookie,
            table_id=0,
            command=ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=BLOCK_DURATION,
            priority=BLOCK_PRIORITY,
            match=match,
            instructions=[]
        )

        datapath.send_msg(flow_mod)

        expiry = time.time() + BLOCK_DURATION

        self.blocked_macs[key] = (
            expiry,
            cookie
        )

        self.logger.warning(
            "BLOCKING: Client %s exceeded traffic threshold "
            "of %s Mbps",
            src_mac,
            TRAFFIC_THRESHOLD_MBPS
        )

    # Remove a client's blocking rule
    def remove_block(self, datapath, cookie):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            cookie=cookie,
            cookie_mask=0xffffffffffffffff,
            table_id=ofproto.OFPTT_ALL,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=parser.OFPMatch()
        )

        datapath.send_msg(flow_mod)

    # Switch connection handler
    @set_ev_cls(
        ofp_event.EventOFPSwitchFeatures,
        CONFIG_DISPATCHER
    )
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(
            datapath,
            0,
            match,
            actions
        )

        self.logger.info(
            "Switch connected: datapath ID %s",
            datapath.id
        )

    # MAC learning and packet forwarding
    @set_ev_cls(
        ofp_event.EventOFPPacketIn,
        MAIN_DISPATCHER
    )
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        self.mac_to_port[dpid][src] = in_port

        self.logger.info(
            "Packet received: source=%s destination=%s port=%s",
            src,
            dst,
            in_port
        )

        if dst in self.mac_to_port[dpid]:

            out_port = self.mac_to_port[dpid][dst]

        else:

            out_port = ofproto.OFPP_FLOOD

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(
                in_port=in_port,
                eth_src=src,
                eth_dst=dst
            )

            self.add_flow(
                datapath,
                1,
                match,
                actions
            )

        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)
