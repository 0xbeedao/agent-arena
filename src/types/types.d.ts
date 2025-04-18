import {
  ContestRoundSchema,
  ContestWorkflowSetupSchema,
  JudgeResponseSchema,
  JudgeResultSchema,
  JudgeResultListSchema,
  PlayerActionSchema,
  PlayerResultSchema,
  PlayerSchema,
  PlayerStatusSchema,
  PointSchema,
} from "./schemas";
import { z } from "zod";

export type ContestRound = z.infer<typeof ContestRoundSchema>;

export type ContestWorkflowSetup = z.infer<typeof ContestWorkflowSetupSchema>;

export type ContestWorkflowRound = z.infer<typeof ContestWorkflowRoundSchema>;

export type Participant = z.infer<typeof PlayerSchema>;

export type JudgeResult = z.infer<typeof JudgeResultSchema>;
export type JudgeResponse = z.infer<typeof JudgeResponseSchema>;
export type JudgeResultList = z.infer<typeof JudgeResultListSchema>;
export type PlayerAction = z.infer<typeof PlayerActionSchema>;

export type Point = z.infer<typeof PointSchema>;

export type PlayerStatus = z.infer<typeof PlayerStatusSchema>;

export type GridFeature = z.infer<typeof GridFeatureSchema>;

export type PlayerResult = z.infer<typeof PlayerResultSchema>;
