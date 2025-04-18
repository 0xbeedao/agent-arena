import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  generateJudgement,
  generatePositionUpdates,
  generatePlayerStatus,
  generatePlayerStatusUpdates,
  generateNarrativeForJudgement,
} from "./judge-system";
import type {
  ContestRound,
  JudgeResult,
  JudgeResultList,
  PlayerResult,
  PlayerStatus,
} from "../../types/types.d";
import {
  PlayerStatusSchema,
  JudgeResultListSchema,
} from "../../types/schemas.d";
import { testLogger } from "../../logging";
import { Agent } from "@mastra/core";

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

const mockRound: ContestRound = {
  actions: {
    player1: {
      action: "move",
      target: { x: 2, y: 1 },
      narration: "Moving right",
    },
    player2: { action: "wait", narration: "Waiting" },
  },
  arenaDescription: "A basic arena",
  status: {
    player1: mockStatusPlayer1,
    player2: mockStatusPlayer2,
  },
  results: {},
  positions: {
    "feature:a rock": { x: 4, y: 5 },
  },
};

const mockJudgeResults: JudgeResult[] = [
  {
    playerId: "player1",
    result: "success",
    reason: "Moved successfully",
  },
  {
    playerId: "player2",
    result: "no effect",
    reason: "Waited",
  },
];

describe("Judge System Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("generateJudgement", () => {
    it("should generate initial judge results based on player actions and grid state", async () => {
      const mockJudgeResponseObject = [
        {
          playerId: "player1",
          result: "success",
          reason: "Moved right and found a key",
        },
        {
          playerId: "player2",
          result: "success with consequences",
          reason: "Moved right but triggered a trap",
        },
      ];
      const localMockJudge = {
        generate: vi.fn().mockResolvedValueOnce({
          object: mockJudgeResponseObject,
        }),
      } as unknown as any;

      const localRound: ContestRound = { ...mockRound };

      const judgeResults: JudgeResultList = await generateJudgement({
        judgeAgent: localMockJudge,
        arenaDescription: "A dangerous arena",
        extraInstructions: "Beware of hidden traps",
        round: localRound,
      });

      expect(judgeResults).toEqual(mockJudgeResponseObject);

      expect(localMockJudge.generate).toHaveBeenCalledTimes(1);
      expect(localMockJudge.generate).toHaveBeenCalledWith(
        expect.stringContaining("A dangerous arena"),
        { output: JudgeResultListSchema }
      );

      const generateCall = (localMockJudge.generate as ReturnType<typeof vi.fn>)
        .mock.calls[0][0] as string;
      expect(generateCall).toContain("Beware of hidden traps");
      expect(generateCall).toContain(JSON.stringify(localRound.actions));
    });
  });

  describe("generatePositionUpdates", () => {
    it("should call the agent to generate position updates and update the grid", async () => {
      const mockPositionUpdates: Record<string, { x: number; y: number }> = {
        player1: { x: 2, y: 1 },
        player2: { x: 5, y: 5 },
      };
      const localMockJudge = {
        generate: vi.fn().mockResolvedValueOnce({
          object: mockPositionUpdates,
        }),
      } as unknown as any;

      const localRound: ContestRound = JSON.parse(JSON.stringify(mockRound));

      const props = {
        judgeAgent: localMockJudge,
        arenaDescription: "Updating positions",
        judgeResults: mockJudgeResults,
        round: localRound,
      };

      const response = await generatePositionUpdates(props);

      expect(localMockJudge.generate).toHaveBeenCalledTimes(1);
      const jsonCall = JSON.stringify((localMockJudge.generate as any).mock.calls[0]);
      expect(jsonCall).toContain("Updating positions");
      const generateCall = (localMockJudge.generate as ReturnType<typeof vi.fn>)
        .mock.calls[0][0] as string;
      expect(generateCall).toContain(JSON.stringify(mockJudgeResults));

      expect(response["player1"]).toEqual({ x: 2, y: 1 });
      expect(response["player2"]).toEqual({ x: 5, y: 5 });
    });
  });

  describe("generatePlayerStatus", () => {
    it("should generate player status based on judge result", async () => {
      const mockUpdatedStatus: PlayerStatus = {
        status: "injured",
        health: 80,
        inventory: [],
      };
      const localMockAgent = {
        generate: vi.fn().mockResolvedValue({
          object: mockUpdatedStatus,
        }),
      } as unknown as any;

      const mockResult = {
        playerId: "player2",
        result: "success with consequences",
        reason: "Moved right but triggered a trap",
      };

      const playerResult = await generatePlayerStatus({
        agent: localMockAgent,
        result: mockResult,
        playerStatus: {
          status: "ok",
          health: 100,
          inventory: [],
        },
      });

      expect(playerResult.status).toEqual(mockUpdatedStatus);
      expect(playerResult.playerId).toBe("player2");
      expect(playerResult.result).toBe("success with consequences");
      expect(playerResult.reason).toBe("Moved right but triggered a trap");

      expect(localMockAgent.generate).toHaveBeenCalledTimes(1);
      const generateCall = (localMockAgent.generate as ReturnType<typeof vi.fn>)
        .mock.calls[0];
      const prompt = generateCall[0] as string;
      const options = generateCall[1];

      expect(prompt).toContain(JSON.stringify(mockResult));
      expect(JSON.stringify(options.output)).toEqual(JSON.stringify(PlayerStatusSchema));
    });
  });

  describe("generatePlayerStatusUpdates", () => {
    it("should call generatePlayerStatus for each result and update round statuses", async () => {
        const status1: PlayerStatus = {
            health: 100,
            status: "ok",
            inventory: []
        };
        const status2: PlayerStatus = {
            health: 80,
            status: "sick",
            inventory: []
        };
        
      const localMockAgent = {
        generate: vi.fn()
          .mockResolvedValueOnce({object: status1})
          .mockResolvedValueOnce({object: status2}),
      } as unknown as Agent;
      
      const localRound: ContestRound = JSON.parse(JSON.stringify(mockRound));

      const props = {
        judgeAgent: localMockAgent,
        arenaDescription: "Updating statuses",
        judgeResults: mockJudgeResults,
        round: localRound,
      };

      const response = await generatePlayerStatusUpdates(props);

      testLogger.info("Response: " + JSON.stringify(response));
      expect(localMockAgent.generate).toHaveBeenCalledTimes(2);
      expect(Object.keys(response)).toEqual(["player1", "player2"]);
      expect(response["player1"]).toEqual(status1);
      expect(response.player2).toEqual(status2);
    });
  });

  describe("generateNarrativeForJudgement", () => {
    it("should call generateNarrativeFromResults and return JudgeResponse structure", async () => {
      const mockNarrative = "The crowd goes wild!";
      const localMockAgent = {
        generate: vi.fn().mockResolvedValue({
          object: mockNarrative,
        }),
      } as unknown as any;

      const localRound: ContestRound = { ...mockRound };

      const props = {
        arenaAgent: localMockAgent,
        arenaDescription: "Narrating the round",
        extraInstructions: "Be dramatic!",
        judgeResults: mockJudgeResults,
        round: localRound,
      };

      const response = await generateNarrativeForJudgement(props);

      expect(localMockAgent.generate).toHaveBeenCalledTimes(1);
      expect(response).toEqual(mockNarrative);
    });
  });
});