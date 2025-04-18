import type { JudgeResult, PlayerStatus } from "../../types/types.d";

export function updateStatusesFromJudgeResults(
  judgeResults: JudgeResult[],
  statuses: Record<string, PlayerStatus>
): Record<string, PlayerStatus> {
  for (const judgeResult of judgeResults) {
    const { playerId } = judgeResult;
    const status = statuses[playerId];
    statuses[playerId] = status;
  }
  return statuses;
}