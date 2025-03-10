import { z } from "zod";

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
)})

export const PlayerActionSchema = z.object({
  playerId: z.string(),
  action: z.string(),
  narration: z.string(),
});

const contestWorkflowSetupSchema = z.object({
  arena: ParticipantSchema,
  judge: ParticipantSchema,
  players: z.array(ParticipantSchema)
})

const contestWorkflowSchema = contestWorkflowSetupSchema.extend({
  arenaDescription: z.string(),
  round: z.number().default(0),
  roundHistory: z.array(z.object({
      round: z.number(),
      actions: z.array(z.object({
          playerId: z.string(),
          action: z.string(),
          narration: z.string()
      }))
  }))
})
