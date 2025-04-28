import { cn } from "cn-func";
import type { StyledButtonProps } from "./types";
import { Button } from "@headlessui/react";
import { ShadowBox } from "./StyledBox";

const INNER_BUTTON_STYLES =
	"inline-flex items-center px-4 py-2 bg-[#ffc480] border-[3px] border-gray-900 text-gray-900 rounded group-hover:-translate-y-px group-hover:-translate-x-px transition-transform relative z-10";
const UNWRAPPED_BUTTON_STYLES =
	"px-4 py-1 bg-[#EBDBB7] hover:bg-[#FFC480] text-gray-900 rounded transition-colors duration-200 border-[3px] border-gray-900 relative hover:-translate-y-px hover:-translate-x-px";
    
/* example of Primary Button as Anchor Tag
 <div class="relative mt-4 inline-block group">
    <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
    <a href="/foo/" class="inline-flex items-center px-4 py-2 bg-[#ffc480] border-[3px] border-gray-900 text-gray-900 rounded group-hover:-translate-y-px group-hover:-translate-x-px transition-transform relative z-10">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
        </svg>
        Download
    </a>
</div> 

Example of Primary Button as Button Tag

<div class="relative mt-4 inline-block group ml-4">
    <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
    <button onclick="copyFullDigest()" class="inline-flex items-center px-4 py-2 bg-[#ffc480] border-[3px] border-gray-900 text-gray-900 rounded group-hover:-translate-y-px group-hover:-translate-x-px transition-transform relative z-10">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path>
        </svg>
        Copy all
    </button>
</div>

Example of Secondary Button

<button 
onclick="foo()" 
class="px-4 py-1 bg-[#EBDBB7] hover:bg-[#FFC480] text-gray-900 rounded transition-colors duration-200 border-[3px] border-gray-900 relative hover:-translate-y-px hover:-translate-x-px">
    Bar
</button>

*/

export const StyledButton = ({
	children,
	variant = "primary",
	className = "",
	href = "",
	onClick = (): void => {},
}: StyledButtonProps): React.ReactElement => {
	const baseStyles =
		variant === "primary" ? INNER_BUTTON_STYLES : UNWRAPPED_BUTTON_STYLES;
	const mergedStyles = cn(baseStyles, className);

	const inner = href ? (
		<a className={mergedStyles} href={href}>
			{children}
		</a>
	) : (
		<Button className={mergedStyles} onClick={onClick}>
			{children}
		</Button>
	);

	if (variant === "primary") {
		return (
			<div className="relative mt-4 inline-block group">
				<ShadowBox position="inner" />
				{inner}
			</div>
		);
	}

	return inner;
};
