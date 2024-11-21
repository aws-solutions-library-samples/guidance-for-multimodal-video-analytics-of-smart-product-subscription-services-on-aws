import { Button, Container, SpaceBetween } from "@cloudscape-design/components";
import {
  Dispatch,
  SetStateAction,
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
} from "react";
import TextareaAutosize from "react-textarea-autosize";
import { ChatBotHistoryItem, ChatBotMessageType } from "./types";
import { useSelector } from "react-redux";
import styles from "./chat.module.scss";
import { CustomContext } from "../../../common/helpers/context";
import { UserState } from "../../../common/helpers/store";
import { Global } from "../../../common/constant/global";

export interface ChatInputPanelProps {
  setToolsHide: Dispatch<SetStateAction<boolean>> | undefined;
  setLoading: Dispatch<SetStateAction<boolean>>;
  messageHistory: ChatBotHistoryItem[];
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}

export abstract class ChatScrollState {
  static userHasScrolled = false;
  static skipNextScrollEvent = false;
  static skipNextHistoryUpdate = false;
}

export default function ChatInputPanel(props: ChatInputPanelProps) {
  const [text, setTextValue] = useState<string>("");
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const llmConfig = useSelector((state: UserState) => state.llmConfig);
  const context = useContext(CustomContext);

  const handleSendMessage = () => {
    if (context?.sendMessage) {
      props.setMessageHistory((history: ChatBotHistoryItem[]) => {
        return [
          ...history,
          {
            type: ChatBotMessageType.Human,
            content: text,
          },
        ];
      });
      props.setLoading(true);
      context.sendMessage({
        action: "vqa_chatbot",
        user_id: userInfo.userId,
        task_id: Global.taskId,
        vqa_prompt: text,
        model: llmConfig.modelId,
      });
    }
    setTextValue("");
  };

  const handleSetting = () => {
    if (props.setToolsHide) {
      props.setToolsHide(false);
    }
  };

  const handleClear = () => {
    props.setMessageHistory([]);
  };

  useEffect(() => {
    const onWindowScroll = () => {
      if (ChatScrollState.skipNextScrollEvent) {
        ChatScrollState.skipNextScrollEvent = false;
        return;
      }

      const isScrollToTheEnd =
        Math.abs(
          window.innerHeight +
            window.scrollY -
            document.documentElement.scrollHeight
        ) <= 10;

      ChatScrollState.userHasScrolled = !isScrollToTheEnd;
    };

    window.addEventListener("scroll", onWindowScroll);

    return () => {
      window.removeEventListener("scroll", onWindowScroll);
    };
  }, []);

  useLayoutEffect(() => {
    if (ChatScrollState.skipNextHistoryUpdate) {
      ChatScrollState.skipNextHistoryUpdate = false;
      return;
    }

    if (!ChatScrollState.userHasScrolled && props.messageHistory.length > 0) {
      ChatScrollState.skipNextScrollEvent = true;
      window.scrollTo({
        top: document.documentElement.scrollHeight + 1000,
        behavior: "smooth",
      });
    }
  }, [props.messageHistory]);

  return (
    <Container className={styles.input_area_container}>
      <SpaceBetween size={"s"}>
        <div className={styles.input_textarea_container}>
          <TextareaAutosize
            className={styles.input_textarea}
            maxRows={6}
            minRows={1}
            spellCheck={true}
            autoFocus
            onChange={(e) => setTextValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key == "Enter" && !e.shiftKey) {
                if (!e.nativeEvent.isComposing && e.locale !== "zh-CN") {
                  e.preventDefault();
                  handleSendMessage();
                }
              }
            }}
            value={text}
            placeholder={
              "Send a message... (⇧ + Enter to start a new line, and ENTER to generate a response)"
            }
          />
          <div className={styles.input_buttons}>
            <Button
              disabled={text.length === 0}
              onClick={handleSendMessage}
              variant="primary"
            >
              Send
            </Button>
            <Button
              iconName="remove"
              variant="icon"
              onClick={handleClear}
            ></Button>
            {props.setToolsHide && (
              <Button
                iconName="settings"
                variant="icon"
                onClick={handleSetting}
              ></Button>
            )}
          </div>
        </div>
      </SpaceBetween>
    </Container>
  );
}
