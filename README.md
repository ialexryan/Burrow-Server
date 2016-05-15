# Burrow Server

## Transmission layer
Here's how you send data to the server with multiple DNS requests:

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
The indices are required because DNS lookups are sometimes duplicated, and to allow all lookups to be done in parallel.

**3) End the transmission**
```
dig -t txt 3.2a591c8b.end.burrow.tech
```
The length is there for error detection - if it doesn't match the number of continue's received, the transmission will fail.

Right now, the server just sends you back the data you sent to it, concatenated and reversed.

In the future, it will concatenate the data into an IP packet or HTTP request and act on it.


## Session layer

### Message Types

The following messages are used to set up, utilize, and tear down a Burrow tunnel.

| Message        | Client Format                          | Server Format            |
|----------------|----------------------------------------|--------------------------|
| Begin Session  | `b`                                    | `s-[session identifier]` |
| Forward Packet | `f-[session identifier]-[packet data]` | `s`                      |
| Request Packet | `r-[session identifier]`               | `s-[packet data]`        |
| End Session    | `e-[session identifier]`               | `s`                      |
| Test (reverse) | `test-helloworld`                      | `dlrowolleh-tset`        |

As shown above, messages are formatted as a dash-separated list. In both cases, packet data is base64-encoded.

The first component of the client message identifies the message type so that the server knows how to
interpret the arguments and execute the message. The following components of the client message act
as the arguments of the message.

### Server Error Response

The server message is structured a little bit differently. Since it is sent in response to a client message,
the client does not need to be informed of the message type. Instead, the server message uses the first
component to indicate success or failure. If the first component is `s`, this identifier a successful response,
and the rest of the arguments are to be treated as the proper arguments to a response of this message type.
If the first component is `f` however, the response indicates a failure.

| Result  | Server Format                               |
|---------|---------------------------------------------|
| Success | `s-[arguments...]`                          |
| Failure | `f-[error code]-[reason]-[associated data]` |

The error code describes the basic type of error that occured. It might be used by the client to recover
from a given error, perhaps by retrying. A separate error code need not exist for every possible reason.
Error codes simply describe the general problem that occured, and the reason provides description. The
associated data may be used to send back other info if necessary, otherwise it may be omitted such that the
message simply ends with a separator.

#### Error Codes

The following error codes exist. Note that new error codes should be added to the end of the list as to not
break compatibility. If error codes must be added earlier in the list, both the client and server must be
updated.

| Error Code | Error Type      |
|------------|-----------------|
| 0          | Unknown Failure |
