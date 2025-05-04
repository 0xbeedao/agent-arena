# Async request handling

Because we want to be able to track every step in the DB for reconstruction/replay, we want to abstract the calls to the endpoints somewhat.

The flow is as follows:

```mermaid
flowchart TD
    IDLE --> | get job | REQUEST
    REQUEST --> REQUESTING
    REQUESTING --> |sends http request | C{HTTP Code}
    C -->| error | FAIL
    C -->| OK | RESPONSE
    RESPONSE -->| malformed | FAIL
    RESPONSE -->| state complete | COMPLETE{{COMPLETE}}
    RESPONSE -->| state pending | WAITING
    RESPONSE -->| state failure | FAIL
    WAITING --> | get wakeup | REQUEST
```

Using a queue, the flow would then be

```mermaid
flowchart TD

C[[Calling Service]] --> | add job | Q[[Queue]]
Poll[Poller] --> | gets job | Q
Poll --> | sends job | R[[Request Service]]
R ---> S{State Machine}
S --> | COMPLETE | P[send payload]
P --> C
S --> | FAIL | F[send rejection]
F --> C
S --> | WAITING | J[reject job]
J --> Q

```

