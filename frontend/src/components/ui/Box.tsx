import { cn } from 'cn-func';
import type { BoxVariant, BoxProps } from './types';

const variantStyles: Record<BoxVariant, string> = {
  row: 'flex flex-row',
  column: 'flex flex-col',
  centered: 'flex flex-col items-center',
  grid: 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3',
};

export const Box = ({ 
  children, 
  variant = 'row',
  className = '',
}: BoxProps): React.ReactElement => {
  const baseStyles = variantStyles[variant];
  const mergedStyles = cn(baseStyles, className);

  return (
    <div className={mergedStyles}>
      {children}
    </div>
  );
};
