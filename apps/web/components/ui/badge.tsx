import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-lg border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-[#D7DEEA] bg-[#EEF2FA] text-[#24354B]",
        success: "border-[#C5E7CF] bg-[#EAF7EE] text-[#1F6B35]",
        warning: "border-[#F2E2B0] bg-[#FFF8E6] text-[#8A6400]",
        destructive: "border-[#F0C4C4] bg-[#FDECEC] text-[#A33333]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"div"> & VariantProps<typeof badgeVariants>) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
