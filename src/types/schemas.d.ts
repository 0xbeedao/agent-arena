import { z } from "zod";
import { Point } from "./types"; // Make sure we import Point type

export const GridFeatureResponseSchema = z.object({
  name: z.string(),
  position: z.array(z.number()),
  end_position: z.array(z.number()).optional(),
});

export const GridFeaturesResponseSchema = z.array(GridFeatureResponseSchema);

export const ParticipantSchema = z.object({
  id: z.string(),
  name: z.string(),
  instructions: z.string(),
  model: z.string(),
  personality: z.string(),
});

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

export const PlayerActionSchema = z.object({
  playerId: z.string(),
  action: z.string(),
  narration: z.string(),
});

const AgentSchema = z.custom<Agent>((val) => {
  if (val instanceof Agent) {
    return val;
  }
  throw new Error("Invalid agent");
});

// First, let's create a Point schema to match the Point type
const PointSchema = z.object({
  x: z.number(),
  y: z.number(),
});

// Create a Grid schema that matches the Grid type
const GridSchema = z.object({
  features: z.map(PointSchema, z.string()),
  height: z.number(),
  players: z.map(z.string(), PointSchema),
  width: z.number(),
});

export const contestWorkflowSetupSchema = z.object({
  arena: ParticipantSchema,
  judge: ParticipantSchema,
  players: z.array(ParticipantSchema),
  arenaDescription: z.string(),
  maxFeatures: z.number(),
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
      grid: GridSchema, // Updated to use the proper Grid schema
      round: z.number(),
    })
  ),
});
