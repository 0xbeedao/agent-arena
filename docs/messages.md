# Message usage in Agent Arena

## Message Channel/Subject Naming Patterns

### Arena Contest Channels
| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `arena.contest.{contest_id}.role_call`               | Role call for contest participants (ContestMachine)                           | Subscribed to for role call state, children use `{channel}.{p.id}`                            |
| `arena.contest.{contest_id}.role_call.{participant}` | Role call for a specific participant (ContestMachine)                         | Used for participant-specific role call responses                                              |
| `arena.contest.{contest_id}.setup.description`       | Requesting arena description from announcer agent (SetupMachine)               | Used for announcer to describe the arena                                                      |
| `arena.contest.{contest_id}.contestflow.{from}.{to}` | State transitions in contest flow (ContestMachine.after_transition)            | E.g., `arena.contest.123.contestflow.starting.role_call`                                      |
| `arena.contest.{contest_id}.contestflow.{state}.{job_id}` | Contest state transitions with job tracking                                    | E.g., `arena.contest.123.contestflow.starting.abc123`                                         |
| `arena.contest.{contest_id}.setupmachine.complete`   | Setup machine completion notifications                                         | Used by SetupMachine to signal completion                                                     |
| `arena.contest.{contest_id}.contestmachine.complete` | Contest machine completion notifications                                       | Used by ContestMachine to signal completion                                                   |
| `arena.contest.{contest_id}.round.{round_no}.complete` | Round completion notifications                                                | Used by RoundMachine to signal round completion                                               |

### Actor Agent Channels
| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `actor.agent.*.request.>`                           | All agent requests (wildcard subscription)                                   | Used by AgentController to handle all agent requests                                          |
| `actor.agent.{participant_id}.response.health`      | Health check responses                                                        | Used for participant health check responses                                                    |
| `actor.agent.{participant_id}.response.health.{job_id}` | Job-specific health responses                                             | Used for tracking specific health check jobs                                                  |
| `actor.agent.{participant_id}.response.{prompt_type}.{job_id}` | Prompt response channels                                          | Used for various prompt types (player_action, judge_results, etc.)                            |

### Participant Request Channels
| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `{participant_endpoint}.request.health.{job_id}`     | Health check requests to participants                                         | Constructed from participant endpoint with job ID                                             |
| `{participant_endpoint}.{action}.{prompt_type}.{job_id}` | Prompt-based requests to participants                                      | E.g., `channel://actor.agent.123.request.player_action.abc456`                                |

### System Model Change Channels
| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `sys.arena.{model_class_name}.create`               | Arena model creation notifications                                            | E.g., `sys.arena.contest.create`                                                              |
| `sys.arena.{model_class_name}.update`               | Arena model update notifications                                              | E.g., `sys.arena.contest.update`                                                              |
| `sys.arena.{model_class_name}.delete`               | Arena model deletion notifications                                            | E.g., `sys.arena.contest.delete`                                                              |
| `sys.actor.{model_class_name}.create`               | Actor model creation notifications                                            | E.g., `sys.actor.participant.create`                                                          |
| `sys.actor.{model_class_name}.update`               | Actor model update notifications                                              | E.g., `sys.actor.participant.update`                                                          |
| `sys.actor.{model_class_name}.delete`               | Actor model deletion notifications                                            | E.g., `sys.actor.participant.delete`                                                          |

### LLM Service Channels
| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `actor.llm.{job_id}.{job_id}.request`               | LLM job started notifications                                                 | Used when LLM jobs are initiated                                                              |
| `actor.llm.{job_id}.{job_id}.complete`              | LLM job completion notifications                                              | Used when LLM jobs complete successfully                                                      |
| `actor.llm.{job_id}.{job_id}.fail`                  | LLM job failure notifications                                                 | Used when LLM jobs fail                                                                       |

### Control Panel Monitoring Channels
| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `arena.>`                                            | All arena messages (wildcard)                                                | Used by control panel for monitoring all arena activity                                       |
| `actor.>`                                            | All actor messages (wildcard)                                                | Used by control panel for monitoring all actor activity                                       |
| `actor.llm.{gen_id}.>`                              | All LLM messages for specific generation                                     | Used for monitoring specific LLM generation jobs                                              |

### Common Message Patterns
| Channel/Pattern                                      | Usage/Context                                                                 | Example/Notes                                                                                  |
|------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `msg.reply`                                          | Used for response channels (MessageBroker.publish_response)                    | If present, used as the reply subject                                                         |
| `completion_channel`                                 | Used for state machine completion notifications                                | Passed as parameter to state machines for completion signaling                                |

## Channel Architecture

### Primary Namespaces
- **`arena.contest.{contest_id}.*`** - All contest-related messaging
- **`actor.agent.{participant_id}.*`** - Agent-specific communication
- **`sys.arena.*`** - Arena system model notifications
- **`sys.actor.*`** - Actor system model notifications
- **`actor.llm.*`** - LLM service notifications

### Message Flow Patterns

#### Request-Response Flow
1. **Health Checks**: `{participant_endpoint}.request.health.{job_id}` → `actor.agent.{participant_id}.response.health.{job_id}`
2. **Prompt Requests**: `{participant_endpoint}.{action}.{prompt_type}.{job_id}` → `actor.agent.{participant_id}.response.{prompt_type}.{job_id}`

#### State Machine Flow
1. **Contest Flow**: `arena.contest.{contest_id}.contestflow.{from}.{to}` for state transitions
2. **Completion Flow**: `arena.contest.{contest_id}.{machine_type}.complete` for state machine completion
3. **Round Flow**: `arena.contest.{contest_id}.round.{round_no}.complete` for round completion

#### System Event Flow
1. **Model Changes**: `sys.{component}.{model_class_name}.{action}` for CRUD operations
2. **LLM Jobs**: `actor.llm.{job_id}.{job_id}.{state}` for LLM job lifecycle

### Wildcard Subscriptions
- **`actor.agent.*.request.>`** - All agent requests (used by AgentController)
- **`arena.contest.*.contestflow.*.*`** - All contest flow messages (used by ContestController)
- **`arena.>`** - All arena messages (used by control panel)
- **`actor.>`** - All actor messages (used by control panel)
- **`actor.llm.{gen_id}.>`** - All LLM messages for specific generation

### Channel Construction
- **Participant Endpoints**: Use `channel://actor.agent.$AGENT_ID$` pattern with `$AGENT_ID$` substitution
- **Job-Specific Channels**: Append `{job_id}` to track specific request/response pairs
- **Completion Channels**: Follow `{base_channel}.complete` pattern for state machine completion
- **System Channels**: Use `sys.{component}.{model}.{action}` for model lifecycle events

## Observations & Best Practices

- **Namespace Consistency:** All channels follow clear namespace patterns (`arena.contest.*`, `actor.agent.*`, `sys.*`)
- **Job Tracking:** Job IDs are consistently appended to channels for request/response correlation
- **Hierarchical Structure:** Channel names use dot notation for hierarchical organization
- **Wildcard Support:** Strategic use of wildcards (`*`, `>`) for monitoring and routing
- **Completion Signaling:** State machines use standardized completion channel patterns

### Potential Considerations

- **Channel Depth:** Some channels have deep hierarchies (e.g., `actor.llm.{job_id}.{job_id}.{state}`)
- **Duplicate Job IDs:** LLM channels use job_id twice, which may indicate room for simplification
- **Endpoint Substitution:** Participant endpoints use `$AGENT_ID$` token replacement

## Suggested Improvements

- **Validate Channel Patterns:** Ensure all channels follow the established namespace conventions
- **Monitor Channel Depth:** Consider simplifying deeply nested channel hierarchies
- **Standardize Completion Patterns:** Ensure all state machines use consistent completion channel naming
- **Document Wildcard Usage:** Clearly document which components use wildcard subscriptions and why
