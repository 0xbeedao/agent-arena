import {
  ContestRoundSchema,
  JudgeResponseSchema,
  PlayerActionSchema,
  ParticipantSchema,
} from "./schemas";
import { z } from "zod";

export type ContestRound = z.infer<typeof ContestRoundSchema>;

export type Grid = z.infer<typeof GridSchema>;

export type Participant = z.infer<typeof ParticipantSchema>;

export type JudgeResponse = z.infer<typeof JudgeResponseSchema>;

export type PlayerAction = z.infer<typeof PlayerActionSchema>;

export type Point = z.infer<typeof PointSchema>;

export type PlayerStatus = z.infer<typeof PlayerStatusSchema>;

export type ArenaFeature = {
  name: string;
  position: Point;
  endPosition?: Point;
};
