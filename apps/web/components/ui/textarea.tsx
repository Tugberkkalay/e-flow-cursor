import * as React from "react";

import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.ComponentProps<"textarea">
>(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[84px] w-full rounded-xl border border-[#DEE3EA] bg-white px-3 py-2 text-sm placeholder:text-[#8A93A3] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E2A38]/20 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

export { Textarea };
