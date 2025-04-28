import type { Meta, StoryObj } from '@storybook/react';
import { StyledBox } from './StyledBox';

const meta = {
  title: 'Components/StyledBox',
  component: StyledBox,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof StyledBox>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: <div>Default StyledBox with row variant</div>,
    variant: 'row',
    position: 'outer',
  },
};

export const ColumnVariant: Story = {
  args: {
    children: (
      <>
        <div>First Item</div>
        <div>Second Item</div>
        <div>Third Item</div>
      </>
    ),
    variant: 'column',
    position: 'outer',
  },
};

export const CenteredVariant: Story = {
  args: {
    children: <div>Centered Content</div>,
    variant: 'centered',
    position: 'outer',
  },
};

export const GridVariant: Story = {
  args: {
    children: (
      <>
        <div className="p-4 bg-gray-100">Grid Item 1</div>
        <div className="p-4 bg-gray-100">Grid Item 2</div>
        <div className="p-4 bg-gray-100">Grid Item 3</div>
        <div className="p-4 bg-gray-100">Grid Item 4</div>
      </>
    ),
    variant: 'grid',
    position: 'outer',
  },
};

export const InnerPosition: Story = {
  args: {
    children: <div>Inner position with shadow effect</div>,
    variant: 'row',
    position: 'inner',
  },
};

export const InnerAltPosition: Story = {
  args: {
    children: <div>Inner alternative position with shadow</div>,
    variant: 'row',
    position: 'inner-alt',
  },
};

export const OuterAltPosition: Story = {
  args: {
    children: <div>Alternative outer style with shadow</div>,
    variant: 'row',
    position: 'outer-alt',
  },
};

export const NestedInnerInOuter: Story = {
  args: {
    children: (
      <StyledBox position="inner" variant="row">
        <div>Nested inner in outer</div>
      </StyledBox>
    ),
    variant: 'row',
    position: 'outer',
  },
};

export const NestedInnerAltInOuter: Story = {
  args: {
    children: (
      <StyledBox position="inner-alt" variant="row">
        <div>Nested inner in outer</div>
      </StyledBox>
    ),
    variant: 'row',
    position: 'outer',
  },
};

export const NestedInnerInOuterAlt: Story = {
  args: {
    children: (
      <StyledBox position="inner" variant="row">
        <div className="flex-1 bg-gray-100">Nested inner in outer</div>
        <div className="flex-1 bg-blue-100">Nested inner in outer 2</div>
      </StyledBox>
    ),
    variant: 'row',
    position: 'outer-alt',
  },
};

export const NestedInnerAltInOuterAlt: Story = {
  args: {
    children: (
      <StyledBox position="inner-alt" variant="row">
        <div>Nested inner in outer</div>
      </StyledBox>
    ),
    variant: 'row',
    position: 'outer-alt',
  },
};



export const CustomClassName: Story = {
  args: {
    children: <div>Custom styled box</div>,
    className: 'bg-blue-100 hover:bg-blue-200 transition-colors',
    position: 'outer',
    variant: 'centered',
  },
};

export const ComplexExample: Story = {
  args: {
    children: (
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Complex Layout Example</h2>
        <p>This example shows nested StyledBoxes with different variants and positions.</p>
        <StyledBox position="inner" variant="grid">
          <div className="p-4">
            <h3 className="font-bold">Section 1</h3>
            <p>Content for section 1</p>
          </div>
          <div className="p-4">
            <h3 className="font-bold">Section 2</h3>
            <p>Content for section 2</p>
          </div>
        </StyledBox>
      </div>
    ),
    position: 'outer',
    variant: 'column',
  },
}; 