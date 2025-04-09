import { z } from "zod";
import { Point } from "./types";

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

export const GridSchema = z.object({
  features: z.map(z.string(), z.string()),
  height: z.number(),
  players: z.map(z.string(), PointSchema),
  width: z.number(),
});

export const GridFeatureSchema = z.object({
  name: z.string(),
  position: PointSchema,
  endPosition: PointSchema.optional(),
});

export const GridFeatureListSchema = z.array(GridFeatureSchema);

export const JudgeResponseSchema = z.object({
  results: z.array(
    z.object({
      playerId: z.string(),
      result: z.string(),
      narration: z.string(),
      reason: z.string(),
    })
  ),
});

export const ParticipantSchema = z.object({
  id: z.string(),
  name: z.string(),
  instructions: z.string(),
  model: z.string(),
  personality: z.string(),
});

export const PlayerActionSchema = z.object({
  playerId: z.string(),
  action: z.string(),
  narration: z.string(),
});

// ---- Workflow Schemas ----

export const contestWorkflowSetupSchema = z.object({
  arena: ParticipantSchema,
  judge: ParticipantSchema,
  players: z.array(ParticipantSchema),
  arenaDescription: z.string(),
  arenaHeight: z.number(),
  arenaWidth: z.number(),
  maxFeatures: z.number(),
  requiredFeatures: GridFeatureListSchema.optional(),
  rules: z.array(z.string()),
});

export const contestWorkflowSchema = contestWorkflowSetupSchema.extend({
  agentCache: z.record(z.string(), AgentSchema),
  roundHistory: z.array(
    z.object({
      actions: z.array(
        z.object({
          playerId: z.string(),
          action: z.string(),
          narration: z.string(),
        })
      ),
      arenaDescription: z.string(),
      grid: GridSchema,
      round: z.number(),
    })
  ),
});
