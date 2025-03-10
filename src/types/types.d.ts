import { JudgeResponseSchema, PlayerActionSchema, ParticipantSchema } from "./schemas";
import { z } from "zod";

export type Participant = z.infer<typeof ParticipantSchema>;

export type JudgeResponse = z.infer<typeof JudgeResponseSchema>;

export type PlayerAction = z.infer<typeof PlayerActionSchema>;

