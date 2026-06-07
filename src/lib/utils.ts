export const formatDate = (value: string) =>
  new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));

export const createId = (prefix: string) => `${prefix}-${Math.random().toString(36).slice(2, 9)}`;

export const clamp = (value: number, min = 0, max = 100) => Math.min(max, Math.max(min, value));
