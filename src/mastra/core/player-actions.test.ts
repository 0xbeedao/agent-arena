import { describe, it, expect, vi, beforeEach } from "vitest";
import { generatePlayerAction, describeRoundForPlayer } from "./player-actions";
import type { PlayerStatus, PlayerAction, ContestRound } from "../../types/types.d";

const mockPlayer1 = 'player1';
const mockStatusPlayer1: PlayerStatus = {
  status: "ok",
  health: 100,
  inventory: [],
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
    player2: {
      status: "ok",
      health: 90,
      inventory: ["stick"],
    },
  },
  narrative: '',
  results: {},
  positions: {
    "feature:a rock": { x: 4, y: 5 },
  },
};

describe("Player Actions Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("describeRoundForPlayer", () => {
    it("should generate a descriptive string for the player", async () => {
      const params = {
        agent: { generate: vi.fn() } as unknown as any,
        arenaDescription: "A fiery pit",
        extraInstructions: "Avoid the lava",
        player: mockPlayer1,
        playerStatus: mockStatusPlayer1,
        roundNumber: 3,
      };

      const description = await describeRoundForPlayer(params);

      expect(description).toContain("fiery pit");
      expect(description).toContain("Avoid the lava");
      expect(description).toContain("round is 3");
      expect(description).toContain(JSON.stringify(mockStatusPlayer1));
    });
  });

  describe("generatePlayerAction", () => {
    it("should get player agent, describe round, and generate action", async () => {
      const mockPlayerAction: PlayerAction = {
        action: "attack",
        target: { x: 5, y: 5 },
        narration: "Attacking player2!",
      };
      const arenaAgent = vi.fn() as unknown as any;

      const playerAgent = {
        generate: vi.fn().mockResolvedValue({
          object: mockPlayerAction,
        }),
      } as unknown as any;

      const localRound: ContestRound = { ...mockRound };

      const props = { 
        arenaAgent,
        playerAgent,
        arenaDescription: "Final Showdown",
        extraInstructions: "Only one survives",
        player: mockPlayer1,
        playerStatus: mockStatusPlayer1,
        round: localRound,
        roundNumber: 3,
      };
      
      const action = await generatePlayerAction(props);

      expect(playerAgent.generate).toHaveBeenCalledTimes(1);
      expect(action).toEqual(mockPlayerAction);
    });
  });
});