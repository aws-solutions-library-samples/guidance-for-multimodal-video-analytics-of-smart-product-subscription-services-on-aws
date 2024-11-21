export type LLMConfigState = {
  modelId: string,
  temperature: number,
  topP: number,
  topK: number,
  maxLength: number
};

export const DEFAULT_LLM_CONFIG = {
  modelId: "anthropic.claude-3-sonnet-20240229-v1:0",
  temperature: 0.1,
  topP: 1,
  topK: 250,
  maxLength: 2048,
};