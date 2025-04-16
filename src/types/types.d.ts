import {
  ContestRoundSchema,
  ContestWorkflowSetupSchema,
  JudgeResponseSchema,
  PlayerActionSchema,
  PlayerSchema,
} from "./schemas";
import { z } from "zod";

export type ContestRound = z.infer<typeof ContestRoundSchema>;

export type ContestWorkflowSetup = z.infer<typeof ContestWorkflowSetupSchema>;

export type ContestWorkflowRound = z.infer<typeof ContestWorkflowRoundSchema>;

export type Grid = z.infer<typeof GridSchema>;

export type Participant = z.infer<typeof PlayerSchema>;

export type JudgeResult = z.infer<typeof JudgeResultSchema>;
export type JudgeResponse = z.infer<typeof JudgeResponseSchema>;

export type PlayerAction = z.infer<typeof PlayerActionSchema>;

export type Point = z.infer<typeof PointSchema>;

export type PlayerStatus = z.infer<typeof PlayerStatusSchema>;

export type ArenaFeature = {
  name: string;
  position: Point;
  endPosition?: Point;
};
