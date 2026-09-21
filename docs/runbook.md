# Runbook: diagnosing a network with the device-command tools

For an LLM agent (paste it into the system prompt) or an engineer following the
same steps by hand. It covers three symptoms: a lost OSPF adjacency, a lost
IS-IS adjacency, and a broken BGP/MPLS service.

## Rules

1. **Read-only.** The tools inspect state. They cannot change anything, and you
   must never suggest that a tool call changed the network.
2. **Ask about the devices the question names.** Start with the two ends of the
   affected link or session. Widen only when the evidence points elsewhere.
3. **Check every result before using it.** For each device look at `status`.
   If it is `error`, report `error.code` and stop reasoning about that device.
4. **Say where data came from.** `data_source: "fixture"` is a replayed capture,
   not the current state of a device. Never present it as live.
5. **`null` is not zero.** A field listed in `unsupported_fields` is `null`
   because the vendor cannot report it. Do not read it as "none".
6. **State what you could not check.** These tools return neither configuration
   nor logs nor interface counters. A conclusion that needs them is a
   hypothesis, and must be worded that way.

## Reading a result

| You see | It means | Do |
|---|---|---|
| `device_unreachable` | SSH to the device failed | Report it. Do not infer protocol state |
| `authentication_failed` | Credentials rejected | Report it; it is a proxy setup issue |
| `unsupported_operation` | This platform lacks the tool | Use the platform's own equivalent from the table below |
| `device_not_found` | Name is not in the inventory | Ask the user for the exact inventory name |
| `deadline_exceeded` | Device too slow (30 s limit) | Retry once, then report |
| `command_failed` | Device answered with an error | Report; the feature may be absent on this release |
| `fixture_not_found` | Demo device has no capture for this tool | Pick another tool or device |

Tool choice by protocol:

| Protocol | FRR / Junos | IOS XR |
|---|---|---|
| OSPF | `get_ospf_*`, `get_interface_status`, `get_route` | not available |
| IS-IS | not available | `get_isis_neighbors`, `get_isis_interface`, `get_isis_database` |
| BGP | not available | `get_bgp_summary`, `get_bgp_neighbor_detail` |
| MPLS | not available | `get_ldp_neighbors`, `get_mpls_forwarding`, `get_rsvp_lsps`, `get_vrf_detail` |

## Playbook 1: OSPF adjacency is missing or not Full (FRR, Junos)

Call the tools for **both** routers of the link.

1. `get_ospf_neighbors` on each router. Find the peer's `router_id` and read
   `adjacency_state` (`full` is healthy).
   - Peer absent on one side, present on the other: one-way hellos, go to step 2.
   - Stuck in `init`, `two_way`, `exstart`, `exchange`, `loading`: go to step 3.
   - `two_way` between two non-DR routers on a broadcast segment is normal.
2. `get_ospf_interface` with the link's `interface` on each router. Compare the
   two sides:
   - `enabled` or `up` false: OSPF is not running on the interface.
   - `area` differs: area mismatch.
   - `network_type` differs (one `broadcast_network`, one
     `point_to_point_network`): type mismatch.
   - `hello_interval_ms` or `dead_interval_sec` differ: timer mismatch.
3. `get_interface_status` with the same `interface` on each router. `admin_up`
   false means the port is shut. `oper_up` false means no link. `mtu` differing
   between the two ends is the classic cause of a session stuck in `exstart` or
   `exchange`.
4. `get_ospf_neighbor_detail`. A high or fast-growing `state_changes` on a
   `full` neighbor means the adjacency is flapping. Report the number and the
   `dead_time_ms` remaining.
5. `get_route` for the prefix behind the failed link, on the router that lost
   it. `found: false` confirms the loss of reachability; a route with another
   `next_hops[].interface` shows the traffic has rerouted.

Stop and report when one of the checks in steps 2 or 3 identifies a mismatch.
If the two sides agree on everything above, say so and list what remains
unchecked (authentication, ACLs on the link, device logs).

## Playbook 2: IS-IS adjacency is missing (IOS XR)

1. `get_isis_neighbors` on both routers. Look for the peer's `system_id`, with
   `state: "up"`. `circuit_type` (`l1`, `l2`, `l1l2`) is the level the adjacency
   runs on.
2. `get_isis_interface`. For the link's interface read `state`,
   `adjacency_count_l1` and `adjacency_count_l2` separately: an `l1l2`
   interface can have an adjacency on one level and none on the other. `null`
   counts (for example on a TE tunnel) mean the value is not reported.
   Compare `circuit_type` of both ends; an L1-only end cannot form an L2
   adjacency with an L2-only end.
3. `get_isis_database`. Per level, find the peer's LSP (`lsp_id` starts with its
   hostname, `own_lsp` false) and check `holdtime_sec`. A missing LSP means the
   peer's advertisement is not reaching this router; a `holdtime_sec` close to 0
   means it is about to expire. The router's own LSP has `own_lsp: true`.
   `att_p_ol` is a `attached/partition/overload` triple: an overload bit of
   `1` means the router is signalling that it must not be used for transit.

Report per level. IS-IS is judged level by level, so avoid "IS-IS is up" without
naming the level.

## Playbook 3: BGP/MPLS service is broken (IOS XR)

1. `get_bgp_summary` on the PE. In each address family (`vpnv4 unicast`,
   `vpnv6 unicast`) find the remote PE. `state_or_prefixes_received` is a number
   when the session is Established and a state name (`Idle`, `Active`) when it
   is not.
2. `get_bgp_neighbor_detail`. Check `state`, `up_time` (a short one means a
   recent reset) and `hold_time_sec`. `remote_as` equal to `local_as` is iBGP.
3. `get_vrf_detail`. Find the customer VRF by `name` and read its
   `route_distinguisher` and per-family `import_route_targets` /
   `export_route_targets`. Routes leak between two PEs only when an export target
   on one is imported on the other; compare both PEs.
4. `get_ldp_neighbors`. A neighbor `state` other than `Oper` means the label
   transport to that peer is down.
5. `get_mpls_forwarding`. Confirm a label entry exists toward the remote PE's
   loopback (`prefix_or_id`) with an `outgoing_interface` and `next_hop`.
6. If the service uses RSVP-TE, `get_rsvp_lsps`. Each session lists `head_end`,
   `destination`, `tunnel_name`, the `out_label`, and, when the path is
   protected, `frr_out_label`. A tunnel whose `explicit_route` is missing or
   whose `out_label` is `No label` is not forwarding.

Order matters: BGP down explains everything after it, so stop at the first
failing layer and report it.

## Worked example on the demo devices

The proxy's fixture devices reproduce this without any hardware. Take the
question "Is IS-IS healthy on 123.123.200.200?".

1. `get_isis_neighbors(devices=["123.123.200.200"])` returns two adjacencies,
   `R1_xe` on `Gi0/0/0/0.115` and `R3_nx` on `Gi0/0/0/1.115`, both `state: "up"`,
   `circuit_type: "l1l2"`, `holdtime_sec` 24 and 25.
2. `get_isis_interface` returns the loopback, four Gigabit interfaces and a TE
   tunnel. `GigabitEthernet0/0/0/0` has `adjacency_count_l2: 1` and
   `adjacency_count_l1: 0`; `GigabitEthernet0/0/0/3` has one adjacency on each
   level. Every metric is 10.
3. `get_isis_database` returns 11 LSPs at Level-1 and 11 at Level-2, the device's
   own LSP being `R3.00-00` at both, with the shortest remaining lifetime 521 s
   (L1) and 426 s (L2).

A correct answer names what was seen, and its source: "Both listed adjacencies
are up on Level-1/Level-2, the LSDB holds 11 LSPs per level, no LSP is close to
expiry. The data is a `fixture` replay, not a live device."

The three captures in the demo devices were taken from different sessions, so
their numbers do not reconcile across commands (this device lists two neighbors
but four interfaces carrying adjacencies). On a real device they must agree, and
a disagreement is itself a finding worth reporting. Use the demo devices to
learn the output shape, not to judge a network.

## Not covered

These tools do not show configuration, logs, interface error counters, BGP
prefix tables, OSPF LSDB or Segment Routing state. When the answer depends on
them, say which check is missing and ask the engineer to run it.
