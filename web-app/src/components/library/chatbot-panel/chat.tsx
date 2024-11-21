import { Dispatch, SetStateAction, useContext, useEffect } from "react";
import { ChatBotHistoryItem, ChatBotMessageType } from "./types";
import ChatInputPanel from "./chat-input-panel";
import { Box, SpaceBetween, Spinner } from "@cloudscape-design/components";
import ChatMessage from "./chat-message";
import styles from "./chat.module.scss";
import { CHATBOT_NAME } from "../../../common/constant/constants";
import { CustomContext } from "../../../common/helpers/context";

export default function Chat(
  props: {
    setToolsHide: Dispatch<SetStateAction<boolean>> | undefined,
    messageHistory: ChatBotHistoryItem[],
    setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>,
    loading: boolean,
    setLoading: Dispatch<SetStateAction<boolean>>
  }) {

  const context = useContext(CustomContext);

  useEffect(() => {
    if (context?.message) {
      const data = JSON.parse(context.message.data);
      if (data.statusCode === 200) {
        const vqaResult = JSON.parse(data.body)['vqa_result'];
        if (vqaResult) {
          props.setLoading(false);
          if (props.messageHistory.length > 0) {
            if (props.messageHistory[props.messageHistory.length-1].content !== vqaResult) {
              props.setMessageHistory((history: ChatBotHistoryItem[]) => {
                return [...history, {
                  type: ChatBotMessageType.AI,
                  content: vqaResult
                }];
              });
            }
          }
        }
      }
    }
  }, [context?.message]);

  return (
    <div className={styles.chat_container}>
      <SpaceBetween size={'m'}>
        {props.messageHistory.map((message, idx) => {
            return (
              <div key={idx}>
                <ChatMessage
                  key={idx}
                  message={message}
                  setLoading={props.setLoading}
                  setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => props.setMessageHistory(history)}
                />
              </div>
            );
          }
        )}
        {props.loading && (
          <div>
            <Box float="left">
              <Spinner/>
            </Box>
          </div>
        )}
      </SpaceBetween>
      <div className={styles.welcome_text}>
        {props.messageHistory.length === 0 && !props.loading && (
          <center>{CHATBOT_NAME}</center>
        )}
      </div>
      <div className={styles.input_container}>
        <ChatInputPanel
          setToolsHide={props.setToolsHide}
          setLoading={props.setLoading}
          messageHistory={props.messageHistory}
          setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => props.setMessageHistory(history)}
        />
      </div>
    </div>
  );
}
