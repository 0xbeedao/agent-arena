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

export const GridSchema = z.object({
  features: z.record(z.string(), z.string()),
  height: z.number(),
  playerPositions: z.record(z.string(), PointSchema),
  width: z.number(),
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

export const JudgeResponseSchema = z.object({
  arenaDescription: z.string(),
  grid: GridSchema,
  results: z.array(JudgeResultSchema),
});

export const PlayerResultSchema = z.object({
  status: PlayerStatusSchema,
  result: z.string(),
  reason: z.string(),
  playerId: z.string(),
});

export const RoundResultSchema = z.object({
  arenaDescription: z.string(),
  grid: GridSchema,
  results: z.array(PlayerResultSchema),
});

export const ContestRoundSchema = z.object({
  actions: z.record(z.string(), PlayerActionSchema),
  arenaDescription: z.string(),
  grid: GridSchema,
  status: z.record(z.string(), PlayerStatusSchema),
});

// ---- Workflow Schemas ----

export const contestWorkflowSetupSchema = z.object({
  arena: z.string().default("arena"), // agent id, default: arena
  judge: z.string().default("judge"), // agent id, default: judge
  players: z.array(PlayerSchema),
  arenaDescription: z.string().default("A square arena"),
  arenaHeight: z.number().positive(),
  arenaWidth: z.number().positive(),
  maxFeatures: z.number().positive(),
  requiredFeatures: GridFeatureListSchema.optional(),
  rules: z.array(z.string()),
});

export const contestWorkflowRoundSchema = z.object({
  agentCache: z.record(z.string(), AgentSchema),
  roundHistory: z.array(ContestRoundSchema),
  roundNumber: z.number(),
});
