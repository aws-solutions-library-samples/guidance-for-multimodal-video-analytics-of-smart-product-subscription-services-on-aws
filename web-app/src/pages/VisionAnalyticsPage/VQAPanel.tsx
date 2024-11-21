import { Dispatch, SetStateAction } from "react";
import Chat from "../../components/library/chatbot-panel/chat";
import { ChatBotHistoryItem } from "../../components/library/chatbot-panel/types";

export default function VQAPanel(props: {
  messageHistory: ChatBotHistoryItem[];
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  isLoading: boolean;
  setLoading: Dispatch<SetStateAction<boolean>>;
}) {
  return (
    <Chat
      setToolsHide={undefined}
      messageHistory={props.messageHistory}
      setMessageHistory={props.setMessageHistory}
      loading={props.isLoading}
      setLoading={props.setLoading}
    />
  );
}
