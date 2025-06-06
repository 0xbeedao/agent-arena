# Message usage in Agent Arena

## Message Channel/Subject Naming Patterns

| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `arena.request.job`                                  | Sending jobs to the scheduler (MessageBroker.send_job)                        | Used for all job requests to the scheduler                                                    |
| `arena.contest.{contest_id}.role_call`               | Role call for contest participants (ContestMachine)                           | Subscribed to for role call state, children use `{channel}.{p.id}`                            |
| `arena.contest.{contest_id}.role_call.{participant}` | Role call for a specific participant (ContestMachine)                         | Used for child jobs in role call                                                              |
| `arena.contest.{contest_id}.setup.description`       | Requesting arena description from announcer agent (SetupMachine)               | Used for announcer to describe the arena                                                      |
| `arena.contest.{contest_id}.setup.features`          | Requesting random features from arena agent (SetupMachine)                     | Used for feature generation                                                                   |
| `arena.contest.{contest_id}.contestflow.{from}.{to}` | State transitions in contest flow (ContestMachine.after_transition)            | E.g., `arena.contest.123.contestflow.starting.role_call`                                      |
| `arena.contest.{contest_id}.contestflow.{state}`     | Announcing contest state (ContestController.start_contest)                     | E.g., `arena.contest.123.contestflow.starting`                                                |
| `{custom}`                                           | Direct message channels for jobs (CommandJob/UrlJobRequest)                    | E.g., `test.command`, `test.arena.job` in tests                                               |
| `channel` field in jobs                              | Used as the subject for job/response messages                                 | Can be set arbitrarily, but often follows above patterns                                      |
| `completion_channel`                                 | Used for setup completion notifications (ContestMachine/SetupMachine)          | Typically matches one of the above patterns, e.g., `arena.contest.{id}.setup.complete`        |
| `msg.reply`                                          | Used for response channels (MessageBroker.publish_response)                    | If present, used as the reply subject                                                         |

## Observations & Logical Inconsistencies

- **Pattern Consistency:** Most channels follow the pattern `arena.contest.{contest_id}.[...]` for contest-related flows, and `arena.request.job` for scheduler jobs.
- **Role Call/Child Jobs:** The use of `{channel}.{p.id}` for child jobs is consistent in role call and setup flows.
- **Completion Channels:** The `completion_channel` is passed around but its naming is not always explicit; it should be documented to follow the same contest-based pattern.
- **Direct/Custom Channels:** Some jobs/tests use arbitrary channels like `test.command`, which could clash if not namespaced.
- **Empty Channels:** In some controller responses, `channel=""` is set, which could lead to issues if a response is attempted to be published without a valid channel.
- **Reply Subjects:** The use of `msg.reply` for responses is correct, but fallback to `response.channel` can be risky if the channel is not set.

### Potential Clashes/Issues

- **Arbitrary/Empty Channels:** Jobs or responses with `channel=""` or non-namespaced values (e.g., `test.command`) could cause message routing issues or accidental cross-talk between tests and production.
- **Lack of Namespace Enforcement:** There is no enforced namespace for custom/test channels, which could lead to accidental overlap.
- **Completion Channel Ambiguity:** The `completion_channel` is passed as a parameter but its naming convention is not always enforced or checked.

## Suggested Improvements

- **Enforce Namespacing:** All channels should be prefixed with a context (e.g., `arena.`, `arena.contest.`, etc.) to avoid clashes.
- **Validate Non-Empty Channels:** Ensure that no message is published to an empty channel.
- **Document Completion Channel Pattern:** Standardize and document the expected pattern for `completion_channel`.
