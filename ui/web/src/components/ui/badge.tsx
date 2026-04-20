import * as React from "react";
import { cn } from "@/lib/cn";

type Variant =
  | "default"
  | "success"
  | "warning"
  | "destructive"
  | "info"
  | "muted";

const VARIANTS: Record<Variant, string> = {
  default: "bg-muted text-foreground border-border",
  success: "bg-accent/15 text-accent border-accent/30",
  warning: "bg-warning/15 text-warning border-warning/30",
  destructive: "bg-destructive/15 text-destructive border-destructive/30",
  info: "bg-info/15 text-info border-info/30",
  muted: "bg-muted text-foreground-muted border-border",
};

export function Badge({
  variant = "default",
  className,
  children,
  ...rest
}: {
  variant?: Variant;
} & React.HTMLAttributes<HTMLSpanElement>): React.ReactElement {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        VARIANTS[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
