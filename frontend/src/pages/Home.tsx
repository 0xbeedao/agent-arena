import type { FunctionComponent } from "../common/types";
import { Navbar } from "../components/layout/Navbar";
import { Box } from "../components/ui/Box";
import { StyledBox } from "../components/ui/StyledBox";
import { Link } from '@tanstack/react-router';

export const Home = (): FunctionComponent => {
	return (
		<div className="flex h-screen w-full flex-col">
			<Navbar />
			<Box className="w-9/12 mx-auto" variant="grid">
				<div className="col-span-1 mx-auto my-auto">
					<p className="text-4xl text-blue-800 font-heading">Mister Agent Arena</p>
				</div>
				<StyledBox position="outer" variant="centered">
					<h4 className="text-3xl font-semibold font-heading text-left mb-4">
						Quick Links
					</h4>
					<p className="xl:text-lg font-body">
						<ul>
							<li><Link to="/agents">Agent Management</Link></li>
						</ul>
					</p>
				</StyledBox>
			</Box>
		</div>
	);
};
