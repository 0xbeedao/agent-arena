import type { PropsWithChildren } from "react";

export type BoxVariant = "row" | "column" | "centered" | "grid";

export type ButtonVariant = "primary" | "secondary";

export type PositionVariant = "outer" | "inner" | "outer-alt" | "inner-alt";

export interface BoxProps extends PropsWithChildren {
	variant?: BoxVariant;
	className?: string;
}

export interface StyledBoxProps extends BoxProps {
	className?: string;
	position?: PositionVariant;
	wrapperClassName?: string;
	variant?: BoxVariant;
}

export interface ShadowBoxProps extends BoxProps {
	className?: string;
	position?: PositionVariant;
}

export interface StyledButtonProps extends PropsWithChildren {
	className?: string;
	href?: string;
	onClick?: () => void;
	variant?: ButtonVariant;
}
