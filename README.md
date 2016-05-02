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
The indices are required because DNS lookups are sometimes duplicated, and to allow all lookups to be done in parallel.

**3) End the transmission**
```
dig -t txt 3.2a591c8b.end.burrow.tech
```
The length is there for error detection - if it doesn't match the number of continue's received, the transmission will fail.

Right now, the server just sends you back the data you sent to it, concatenated and reversed.

In the future, it will concatenate the data into an IP packet or HTTP request and act on it.
