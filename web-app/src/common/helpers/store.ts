import { createStore } from "redux";
import { UserAction } from "../../components/library/config-panel/chat-config-panel/types";
import { DEFAULT_QUERY_CONFIG, LOCALSTORAGE_KEY } from "../constant/constants";
import { DEFAULT_LLM_CONFIG, LLMConfigState } from "../../components/library/config-panel/llm-config-panel/types";
import {
  DEFAULT_INFERENCE_CONFIG,
  InferenceConfigState
} from "../../components/library/config-panel/inference-config-panel/types";

export enum ActionType {
  Delete = "Delete",
  UpdateUserInfo = "UpdateUserInfo",
  UpdateConfig = "UpdateConfig",
  UpdateLLMConfig = "UpdateLLMConfig",
  UpdateInferConfig = "UpdateInferConfig",
}

export type UserState = {
  userInfo: UserInfo,
  llmConfig: LLMConfigState;
  inferenceConfig: InferenceConfigState;
  queryConfig: any;
};

export type UserInfo = {
  userId: string;
  displayName: string;
  loginExpiration: number;
  isLogin: boolean;
};

export const DEFAULT_USER_INFO = {
  userId: "",
  displayName: "",
  loginExpiration: +new Date() + 6000,
  isLogin: false
};

const defaultUserState: UserState = {
  userInfo: DEFAULT_USER_INFO,
  llmConfig: DEFAULT_LLM_CONFIG,
  inferenceConfig: DEFAULT_INFERENCE_CONFIG,
  queryConfig: DEFAULT_QUERY_CONFIG
};

const localStorageData = localStorage.getItem(LOCALSTORAGE_KEY)
  ? JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "{}")
  : null;

const initialState = localStorageData || defaultUserState;

const userReducer = (state = initialState, action: UserAction) => {
  switch (action.type) {
    case ActionType.Delete:
      localStorage.setItem(LOCALSTORAGE_KEY, "");
      return null;
    case ActionType.UpdateConfig:
      if (localStorage.getItem(LOCALSTORAGE_KEY)) {
        const userInfo = JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "");
        userInfo.queryConfig = action.state.queryConfig;
        localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...userInfo }));
      }
      return { ...action.state };
    case ActionType.UpdateUserInfo:
      if (localStorage.getItem(LOCALSTORAGE_KEY)) {
        const userInfo = JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "");
        userInfo.userInfo = action.state;
        localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...userInfo }));
      }
      return { ...state, userInfo: action.state };
    case ActionType.UpdateLLMConfig:
      if (localStorage.getItem(LOCALSTORAGE_KEY)) {
        const userInfo = JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "");
        userInfo.llmConfig = action.state;
        localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...userInfo }));
      }
      return { ...state, llmConfig: action.state };
    case ActionType.UpdateInferConfig:
      if (localStorage.getItem(LOCALSTORAGE_KEY)) {
        const userInfo = JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "");
        userInfo.inferenceConfig = action.state;
        localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...userInfo }));
      }
      return { ...state, inferenceConfig: action.state };
    default:
      return { ...state };
  }
};

const store = createStore(userReducer as any);

export default store;
