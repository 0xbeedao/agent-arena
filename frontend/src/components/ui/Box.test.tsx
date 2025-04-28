import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Box } from './Box';

describe('Box', () => {
  it('renders children correctly', () => {
    render(
      <Box>
        <div>Test Content</div>
      </Box>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('applies row variant styles by default', () => {
    const { container } = render(
      <Box>
        <div>Content</div>
      </Box>
    );
    expect(container.firstChild).toHaveClass('flex', 'flex-row');
  });

  it('applies column variant styles correctly', () => {
    const { container } = render(
      <Box variant="column">
        <div>Content</div>
      </Box>
    );
    expect(container.firstChild).toHaveClass('flex', 'flex-col');
  });

  it('applies centered variant styles correctly', () => {
    const { container } = render(
      <Box variant="centered">
        <div>Content</div>
      </Box>
    );
    expect(container.firstChild).toHaveClass('flex', 'flex-col', 'items-center');
  });

  it('applies grid variant styles correctly', () => {
    const { container } = render(
      <Box variant="grid">
        <div>Content</div>
      </Box>
    );
    expect(container.firstChild).toHaveClass('grid', 'grid-cols-1', 'gap-4');
  });

  it('merges custom className with variant styles', () => {
    const { container } = render(
      <Box className="bg-blue-500 p-4" variant="row">
        <div>Content</div>
      </Box>
    );
    expect(container.firstChild).toHaveClass('flex', 'flex-row', 'bg-blue-500', 'p-4');
  });
}); 