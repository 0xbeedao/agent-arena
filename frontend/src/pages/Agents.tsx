import type { FunctionComponent } from "../common/types";
import { Navbar } from "../components/layout/Navbar";
import { Box } from "../components/ui/Box";
import { StyledBox } from "../components/ui/StyledBox";

export const Agents = (): FunctionComponent => {
  return (
    <div className="flex h-screen w-full flex-col">
      <Navbar />
      <Box className="w-9/12 mx-auto" variant="column">
        <StyledBox position="outer" variant="column">
          <h1 className="text-4xl font-semibold mb-4 font-heading">Agents Management</h1>
          <div className="space-y-6">
            buttons here
          </div>
        </StyledBox>
      </Box>
    </div>
  );
};
