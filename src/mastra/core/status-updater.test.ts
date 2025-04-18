import { describe, it, expect } from "vitest";
import { updateStatusesFromJudgeResults } from "./status-updater";
import type { PlayerStatus, JudgeResult } from "../../types/types.d";

const mockStatusPlayer1: PlayerStatus = {
  status: "ok",
  health: 100,
  inventory: [],
};
const mockStatusPlayer2: PlayerStatus = {
  status: "ok",
  health: 90,
  inventory: ["stick"],
};

describe("Status Updater Tests", () => {
  it("should iterate through judge results but not modify statuses (current behavior)", () => {
    const initialStatuses: Record<string, PlayerStatus> = {
      player1: { ...mockStatusPlayer1 },
      player2: { ...mockStatusPlayer2 },
      player3: { status: "ok", health: 50, inventory: ["potion"] },
    };
    const localJudgeResults: JudgeResult[] = [
      {
        playerId: "player1",
        result: "success",
        reason: "Did something",
      },
      {
        playerId: "player2",
        result: "failure",
        reason: "Tripped",
      },
    ];

    const updatedStatuses = updateStatusesFromJudgeResults(localJudgeResults, initialStatuses);

    expect(updatedStatuses["player1"]).toEqual(mockStatusPlayer1);
    expect(updatedStatuses["player2"]).toEqual(mockStatusPlayer2);
    expect(updatedStatuses["player3"]).toEqual({
      status: "ok",
      health: 50,
      inventory: ["potion"],
    });
  });

  it("should handle empty judge results array", () => {
    const initialStatuses: Record<string, PlayerStatus> = {
      player1: { ...mockStatusPlayer1 }
    };
    const emptyJudgeResults: JudgeResult[] = [];

    const updatedStatuses = updateStatusesFromJudgeResults(emptyJudgeResults, initialStatuses);

    expect(updatedStatuses).toEqual(initialStatuses);
  });

  it("should handle statuses object with players not in judge results", () => {
    const initialStatuses: Record<string, PlayerStatus> = {
      player1: { ...mockStatusPlayer1 },
      player3: { status: "ok", health: 50, inventory: ["potion"] }
    };
    const localJudgeResults: JudgeResult[] = [
        { playerId: "player1", result: "success", reason: "Did something" }
    ];

    const updatedStatuses = updateStatusesFromJudgeResults(localJudgeResults, initialStatuses);

    expect(updatedStatuses["player1"]).toEqual(mockStatusPlayer1);
    expect(updatedStatuses["player3"]).toEqual(initialStatuses.player3);
  });
});