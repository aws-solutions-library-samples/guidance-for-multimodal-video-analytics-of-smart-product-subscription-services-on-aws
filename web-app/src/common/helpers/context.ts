import React, { createContext } from "react";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { NavigationPanelState } from "../types";

export interface ContextType {
  sendMessage: SendJsonMessage | undefined;
  message: MessageEvent<any> | undefined;
  isConnected: boolean;
  setMessage: React.Dispatch<
    React.SetStateAction<MessageEvent<any> | undefined>
  >;
  setSideNavOpen: (state: Partial<NavigationPanelState>) => void;
}
export const CustomContext = createContext<ContextType>({
  sendMessage: undefined,
  message: undefined,
  isConnected: false,
  setMessage: () => void 0,
  setSideNavOpen: () => void 0,
});
