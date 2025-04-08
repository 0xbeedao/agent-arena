import {
  JudgeResponseSchema,
  PlayerActionSchema,
  ParticipantSchema,
} from "./schemas";
import { z } from "zod";

export type Grid = {
  features: Map<string, string>;
  height: number;
  players: Map<string, Point>;
  width: number;
};

export type Participant = z.infer<typeof ParticipantSchema>;

export type JudgeResponse = z.infer<typeof JudgeResponseSchema>;

export type PlayerAction = z.infer<typeof PlayerActionSchema>;

export type Point = {
  x: number;
  y: number;
};

export type ArenaPosition = {
  x: number;
  y: number;
  description: string;
};

export type ArenaFeature = {
  name: string;
  position: Point;
  end_position?: Point;
};
