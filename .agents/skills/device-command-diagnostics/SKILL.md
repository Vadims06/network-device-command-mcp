---
name: device-command-diagnostics
description: "Required before answering any question about a router's current state with the device-command MCP tools (get_bgp_summary, get_isis_neighbors, get_mpls_forwarding, get_ospf_neighbors, get_route, get_ldp_neighbors, get_rsvp_lsps, get_interface_status, get_evpn_vnis ...): BGP/IS-IS/OSPF neighbors, MPLS forwarding, LDP/RSVP sessions, EVPN VNIs and VTEPs on a device, a route on a device, interface state, or checking on the device what a Topolograph snapshot shows. Defines how to read per-device status and errors, fixture vs live data, and which tool fits which platform. Read-only; not for configuration changes."
---

# Live device diagnostics

Every answer comes from the device-command tools, which run fixed read-only operations on inventoried devices. Never answer from model knowledge, never suggest the user run the command if a tool covers it, and never claim a command was run that no tool ran.

## Rules
- Read-only. There is no tool to configure a device; do not ask for or attempt one.
- `devices` takes inventory names (1-20). If you do not know the names, take the router ids from the Topolograph graph as the first guess and say so; on `device_not_found` ask the user for the inventory name. Do not invent device names.
- Pick the tool by protocol and platform: FRR and Junos have OSPF, interface and route tools; FRR alone has `get_evpn_vnis` (L2/L3 VNI, tenant VRF, local VTEP, remote VTEPs and MAC count of an L2 VNI; both are null for an L3 VNI); IOS XR has BGP, IS-IS, RSVP-TE, MPLS, LDP and VRF tools. A tool that does not support the device's platform returns a per-device error - report it, do not retry with another tool to hide it.
- Results are per device. A device with `status: "error"` failed on its own; report it next to the devices that answered, with its error code, and do not treat the partial result as complete.
- Check `data_source` on every result: `live` is the device's state now; `fixture` is a replayed capture, so say it is not live state and never describe it as current.
- Live state is a point in time. Quote the device name and what the tool returned; do not generalize one device to the domain.

## Workflows
- **Neighbor or adjacency down**: `get_ospf_neighbors` / `get_isis_neighbors` on both ends, then the link: `get_interface_status` and `get_ospf_interfaces` (cost, timers, network type) for OSPF on FRR/Junos, `get_isis_interface` for IS-IS on IOS XR. Mismatched timers or network type are observed facts; a cause beyond that is inference.
- **Route check**: `get_route(prefix)` on the device; compare next hops with the path Topolograph computed for the same snapshot, and state that one is live and the other is a snapshot.
- **EVPN VNIs**: `get_evpn_vnis` on each leaf you compare. An empty VNI list on a device is a valid answer (it carries none); a per-device `unsupported_operation` is not, report it as unsupported; a request-level `unsupported_operation` ("operation is not allowed") means the proxy lacks the operation, say so. Remote VTEPs are what that device reports; to compare two leaves, query both.
- **BGP/VPN/MPLS**: `get_bgp_summary` first, then `get_bgp_neighbor_detail` for a failing neighbor; `get_vrf_detail`, `get_mpls_forwarding`, `get_ldp_neighbors`, `get_rsvp_lsps` as the question needs.
- **With the Topolograph skill**: the snapshot says what the topology looked like at `graph_time`; these tools say what the device reports now. Give the snapshot's `graph_time`, say the device read is current at call time only when `data_source` is `live` (a `fixture` is a replayed capture; the tools return no device timestamp), and never merge them into one claim.
