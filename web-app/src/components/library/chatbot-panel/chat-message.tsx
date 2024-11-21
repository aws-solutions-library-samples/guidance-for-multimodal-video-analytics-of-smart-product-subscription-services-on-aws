import { Container, Icon } from "@cloudscape-design/components";
import { ChatBotHistoryItem, ChatBotMessageType } from "./types";
import { Dispatch, SetStateAction } from "react";
import styles from "./chat.module.scss";

export interface ChatMessageProps {
  message: ChatBotHistoryItem;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}

export default function ChatMessage(props: ChatMessageProps) {

  return (
    <div>
      {props.message.type === ChatBotMessageType.Human && (
        <div className={styles.question}>
          <Icon name="user-profile"/> {props.message.content.toString()}
        </div>
      )}
      {props.message.type === ChatBotMessageType.AI && (
        <Container className={styles.answer_area_container}>
          <p>{props.message.content}</p>
        </Container>
      )}
    </div>
  );
}