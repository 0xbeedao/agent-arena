import { z } from "zod";

export const AgentSchema = z.custom<Agent>((val) => {
  if (val instanceof Agent) {
    return val;
  }
  throw new Error("Invalid agent");
});

export const PointSchema = z.object({
  x: z.number(),
  y: z.number(),
});

export const ArenaFeatureSchema = z.object({
  name: z.string(),
  position: PointSchema,
  endPosition: PointSchema.optional(),
});

export const GridFeatureSchema = z.object({
  name: z.string(),
  position: PointSchema,
  endPosition: PointSchema.optional(),
});

export const GridFeatureListSchema = z.array(GridFeatureSchema);

export const PlayerSchema = z.object({
  id: z.string(),
  name: z.string(),
  model: z.string(),
  personality: z.string(),
  instructions: z.string().optional(),
});

export const PlayerActionSchema = z.object({
  action: z.string(),
  target: PointSchema.optional(),
  narration: z.string(),
});

export const PlayerStatusSchema = z.object({
  status: z.string(),
  health: z.number(),
  inventory: z.array(z.string()),
});

// [{playerId: <playerId>, status: <PlayerStatus>, result: <result>, reason: <reason>}]
export const JudgeResultSchema = z.object({
  playerId: z.string(),
  result: z.string(),
  reason: z.string(),
});

export const JudgeResultListSchema = z.array(JudgeResultSchema);

export const PlayerResultSchema = z.object({
  status: PlayerStatusSchema,
  result: z.string(),
  reason: z.string(),
  playerId: z.string(),
});

export const RoundResultSchema = z.object({
  arenaDescription: z.string(),
  results: z.array(PlayerResultSchema),
});

export const ContestRoundSchema = z.object({
  actions: z.record(z.string(), PlayerActionSchema),  // player actions
  arenaDescription: z.string(),                       // changes to arena description
  narrative: z.string().default(""),                  // narrative summary of round
  positions: z.record(z.string(), PointSchema)  ,     // positions of players and features. Players have a "player:" prefix
                                                      // and features have an "feature:"
  results: z.record(z.string(), PlayerResultSchema),  // judge results by player
  status: z.record(z.string(), PlayerStatusSchema),   // player status
});

// ---- Workflow Schemas ----

export const contestWorkflowSetupSchema = z.object({
  arena: z.string().default("arena"), // agent id, default: arena
  judge: z.string().default("judge"), // agent id, default: judge
  players: z.array(z.string()).default(["player1", "player2"]),
  arenaDescription: z.string().default("A square arena"),
  arenaHeight: z.number().positive(),
  arenaWidth: z.number().positive(),
  maxFeatures: z.number().positive(),
  requiredFeatures: GridFeatureListSchema.optional(),
  rules: z.string(),
});

export const contestWorkflowRoundSchema = z.object({
  roundHistory: z.array(ContestRoundSchema),
  roundNumber: z.number(),
});
