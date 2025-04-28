import type { Meta, StoryObj } from "@storybook/react";
import { StyledButton } from "./StyledButton";
import type { JSX } from "react";

const meta = {
	title: "Components/StyledButton",
	component: StyledButton,
	parameters: {
		layout: "centered",
	},
	tags: ["autodocs"],
} satisfies Meta<typeof StyledButton>;

export default meta;
type Story = StoryObj<typeof meta>;

// Icon components for the examples
const DownloadIcon = (): JSX.Element => (
	<svg
		className="mr-2 h-4 w-4"
		fill="none"
		stroke="currentColor"
		viewBox="0 0 24 24"
	>
		<path
			d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
			strokeLinecap="round"
			strokeLinejoin="round"
			strokeWidth="2"
		/>
	</svg>
);

const CopyIcon = (): JSX.Element => (
	<svg
		className="mr-2 h-4 w-4"
		fill="none"
		stroke="currentColor"
		viewBox="0 0 24 24"
	>
		<path
			d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
			strokeLinecap="round"
			strokeLinejoin="round"
			strokeWidth="2"
		/>
	</svg>
);

export const Primary: Story = {
	args: {
		children: "Primary Button",
		variant: "primary",
	},
};

export const Secondary: Story = {
	args: {
		children: "Secondary Button",
		variant: "secondary",
	},
};

export const PrimaryWithIcon: Story = {
	args: {
		children: (
			<>
				<DownloadIcon />
				Download
			</>
		),
		variant: "primary",
	},
};

export const SecondaryWithIcon: Story = {
	args: {
		children: (
			<>
				<CopyIcon />
				Copy
			</>
		),
		variant: "secondary",
	},
};

export const AsLink: Story = {
	args: {
		children: "Visit Documentation",
		variant: "primary",
		href: "https://example.com",
	},
};

export const WithOnClick: Story = {
	args: {
		children: "Click Me",
		variant: "primary",
		onClick: () => {
			alert("Button clicked!");
		},
	},
};

export const CustomStyles: Story = {
	args: {
		children: "Custom Button",
		variant: "primary",
		className: "bg-blue-400 hover:bg-blue-500",
	},
};
