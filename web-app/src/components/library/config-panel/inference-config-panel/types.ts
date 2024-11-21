export type InferenceConfigState = {
  frequency: number;
  list_length: number;
  interval: number;
  selectedResolution: string;
  durationTime: number;
  platform: "lambda" | "ecs";
};

export const DEFAULT_INFERENCE_CONFIG = {
  frequency: 10,
  list_length: 1,
  interval: 1,
  selectedResolution: "raw",
  durationTime: 60,
  platform: "lambda",
} as const;
