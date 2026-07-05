import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none active:scale-[0.97]',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-white hover:bg-primary-hover shadow-button hover:shadow-button-hover hover:-translate-y-0.5',
        destructive:
          'bg-error text-white hover:bg-red-600 shadow-lg shadow-red-500/20 hover:-translate-y-0.5',
        outline:
          'border border-border/60 bg-transparent hover:bg-white/50 dark:hover:bg-white/5 text-text-primary hover:border-border',
        secondary:
          'bg-surface-light text-text-primary hover:bg-border/50 border border-border/40',
        ghost:
          'text-text-secondary hover:text-text-primary hover:bg-white/50 dark:hover:bg-white/5',
        link: 'text-primary underline-offset-4 hover:underline',
        gradient:
          'bg-gradient-to-r from-[#007aff] to-[#005bbf] text-white hover:from-[#0a84ff] hover:to-[#0066d6] shadow-button hover:shadow-button-hover hover:-translate-y-0.5',
      },
      size: {
        default: 'h-11 px-7 py-2.5',
        sm: 'h-9 rounded-full px-5 text-xs',
        lg: 'h-13 rounded-full px-9 text-base',
        xl: 'h-15 rounded-full px-11 text-lg',
        icon: 'h-11 w-11',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }
