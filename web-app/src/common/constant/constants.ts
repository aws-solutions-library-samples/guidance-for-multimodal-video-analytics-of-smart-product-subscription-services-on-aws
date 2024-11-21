export const CHATBOT_NAME = "Video Streams";

export const DEFAULT_QUERY_CONFIG = {
  selectedLLM: "anthropic.claude-3-sonnet-20240229-v1:0",
  selectedDataPro: "",
  intentChecked: true,
  complexChecked: true,
  answerInsightChecked: false,
  modelSuggestChecked: false,
  temperature: 0.01,
  topP: 1,
  topK: 250,
  maxLength: 2048,
};

export const defaultSystemPrompt = `You are a helpful AI assistant.
<task>
You task is to describe the images.
</task>

Assistant：`;

export const defaultUserPrompt = `You have perfect vision and pay great attention to detail which makes you an expert at video monitor.
Before answering the question in <answer> tags, please think about it step-by-step within <thinking></thinking> tags`;

export const LOCALSTORAGE_KEY = "__GEN_BI_STORE_INFO__";

export const INDUSTRY_KEYS = ["AUTO", "MFG"] as const;
