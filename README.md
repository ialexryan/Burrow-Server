# Burrow Server

Burrow operates using two layers. The Transmission layer handles communicating
arbitrary amounts of data between the server and the client. The Session layer, which is built
atop the Transmission layer, handles forwarding packets from the client and returning response packets to the client.

## Transmission layer
Here's how we would send the message "thisissomesampledataforustouse" to the server, across 3 separate DNS lookups.

**1) Begin the transmission**
```
dig -t txt <garbage>.begin.burrow.tech
```
(the garbage is required to defeat caching of the naked begin endpoint)

The server will return a transmission ID like `2a591c8b`.

**2) Continue the transmission**
```
dig -t txt thisissome.0.2a591c8b.continue.burrow.tech
dig -t txt sampledata.1.2a591c8b.continue.burrow.tech
dig -t txt forustouse.2.2a591c8b.continue.burrow.tech
```
The indices (0, 1, 2) are required because DNS lookups are sometimes duplicated, and to allow all lookups to be done in parallel.

Note that any data sent through the transmission layer must be domain-safe.

**3) End the transmission**
```
dig -t txt 3.2a591c8b.end.burrow.tech
```
The length (3) is there for error detection - if it doesn't match the number of `continue` lookups received, the transmission will fail.

Of course, we would never send the message "thisissomesampledataforustouse" to the server. Instead, the messages we send to the server have the following special format.


## Session layer

### Message Types

The following messages are used to set up, utilize, and tear down a Burrow tunnel.

| Message         | Client Message Format                      | Server Response Format   |
|-----------------|--------------------------------------------|--------------------------|
| Begin Session   | `b`                                        | `s-[session identifier]` |
| Forward Packets | `f-[session identifier]-[packet data]-...` | `s`                      |
| Request Packets | `r-[session identifier]`                   | `s-[packet data]-...`    |
| End Session     | `e-[session identifier]`                   | `s`                      |
| Test (reverse)  | `test-helloworld`                          | `dlrowolleh-tset`        |

In both cases, packet data is Base64-encoded.

The first dash-separated component of the client message identifies the message type, and the following components
are the arguments of the message.

The server response doesn't contain a message type since it is sent in response to a client message. 
Instead, the server response uses the first component to indicate success or failure.
If the first component is `s`, the operation was successful and the rest of the components
contain the information returned in response to this message type.
If the first component is `f` however, the response indicates a failure.

| Result  | Server Format                               |
|---------|---------------------------------------------|
| Success | `s-[information...]`                        |
| Failure | `f-[error code]-[reason]-[associated data]` |


#### Error Codes

The following error codes exist. Note that new error codes should be added to the end of the list in order to maintain
compatibility. If error codes must be added earlier in the list, both the client and server must be
updated.

| Error Code | Error Type                 |
|------------|----------------------------|
| 0          | Unknown Failure            |
| 1          | Unknown Message Type       |
| 2          | Unknown Session Identifier |

