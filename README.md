# Burrow Server

## Incoming transmissions
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
(the consecutive indices are required because sometimes DNS requests are duplicated)

**3) End the transmission**
```
dig -t txt 2a591c8b.end.burrow.tech
```
Right now, the server just sends you back the data you sent to it, concatenated and reversed.

In the future, it will concatenate the data into an IP packet or HTTP request and act on it.
