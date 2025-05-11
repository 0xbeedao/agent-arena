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

## State machine - ending complete

Ends complete after caller requests three times, the first time the polling loop hasn't piced it up yet

```mermaid
sequenceDiagram
    participant C as Caller
    participant T as Controller
    participant Q as Queue
    participant J as Job Svc
    participant P as Poller
    participant R as Request Svc
    
    C->>+T: POST
    T->>+Q: add job
    Q->>+J: create
    J->>+Q: job
    Q->>+T: job
    T->>-C: return PENDING / ID
    
    C->>+T: GET ID
    T->>+J: get job
    J->>+T: job
    T->>-C: return PENDING / ID
    
    P->>+Q: get next
    Q->>+J: get job
    J->>+Q: job
    Q->>+P: job
    P->>+R: process request
    R->>+P: return COMPLETE / payload
    P->>+Q: update
    Q->>+J: update

    C->>+T: GET ID
    T->>+J: get job
    J->>+T: job
    T->>-C: return COMPLETE / payload
```

## Sequence of a batch with 2 request jobs

```mermaid
sequenceDiagram

    participant C as Controller
    participant Q as Queue
    participant P as Poller
    participant R as Request Svc

    C->>+Q: Add Batch, Requests
    Q->>+Q: Add Batch Job
    Q->>+Q: Add Request Jobs
    P->>+Q: Poll and Process
    Q->>+Q: Get Request Job
    Q->>+R: perform Request
    R->>+Q: Update state to COMPLETE
    Q->>+Q: Revalidate Batch - REQUEST

    P->>+Q: Poll and Process
    Q->>+Q: Get Request Job
    Q->>+R: perform Request
    R->>+Q: Update state to COMPLETE
    Q->>+Q: Revalidate Batch - COMPLETE
```
