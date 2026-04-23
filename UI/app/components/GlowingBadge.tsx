import { Badge } from "./ui/badge";
import { ReactNode } from "react";

interface GlowingBadgeProps {
  children: ReactNode;
  color?: "green" | "blue" | "purple" | "amber" | "red";
  className?: string;
}

export function GlowingBadge({ children, color = "blue", className = "" }: GlowingBadgeProps) {
  const colorClasses = {
    green: "bg-gradient-to-r from-green-500 to-emerald-600 shadow-lg shadow-green-300/50",
    blue: "bg-gradient-to-r from-blue-500 to-indigo-600 shadow-lg shadow-blue-300/50",
    purple: "bg-gradient-to-r from-purple-500 to-pink-600 shadow-lg shadow-purple-300/50",
    amber: "bg-gradient-to-r from-amber-500 to-yellow-600 shadow-lg shadow-amber-300/50",
    red: "bg-gradient-to-r from-red-500 to-rose-600 shadow-lg shadow-red-300/50",
  };

  return (
    <Badge className={`${colorClasses[color]} text-white font-semibold ${className} animate-pulse-glow`}>
      {children}
    </Badge>
  );
}
