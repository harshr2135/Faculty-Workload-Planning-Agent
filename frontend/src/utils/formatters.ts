export function formatTime(value: string): string {
  return value.slice(0, 5);
}

export function formatWorkingDays(days: string[]): string {
  return days.map((d) => d.charAt(0).toUpperCase() + d.slice(1, 3)).join(", ");
}

export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
