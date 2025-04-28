import { cn } from 'cn-func';
import { Box } from './Box';

import type { StyledBoxProps, PositionVariant } from './types';

const positionalStyles: Record<PositionVariant, string> = {
  outer: 'rounded-xl relative pl-8 sm:pl-10 pr-8 sm:pr-16 py-8 border-[3px] border-b-[9px] border-r-[9px] border-gray-900 bg-[#fff4da]',
  'outer-alt': 'bg-[#fafafa] rounded-xl border-[3px] border-b-[9px] border-r-[9px] border-gray-900 p-6 relative space-y-6',
  inner: 'w-full p-4 bg-[#fff4da] border-[3px] border-b-[9px] border-r-[9px] border-gray-900 rounded font-mono text-sm resize-none focus:outline-none relative z-10',
  'inner-alt': 'w-full p-4 bg-[#fafafa] border-[3px] border-b-[9px] border-r-[9px] border-gray-900 rounded font-mono text-sm resize-none focus:outline-none relative z-10',
}

export const StyledBox = ({ 
  children,
  variant = 'centered',
  position = 'outer',
  wrapperClassName = '',
  className = '',
}: StyledBoxProps): React.ReactElement => {
  const wrapperClasses = cn("relative", wrapperClassName);
  const baseStyles = positionalStyles[position];
  const mergedStyles = cn(baseStyles, className);

  const classes = cn("relative z-10", {
    "relative flex flex-col items-center justify-center": variant === "centered",
  })

  return (
    <div className={wrapperClasses}>
        <Box className={mergedStyles} variant={variant}>
          <div className={classes}>
            {children}
          </div>
        </Box>
    </div>
  );
};
