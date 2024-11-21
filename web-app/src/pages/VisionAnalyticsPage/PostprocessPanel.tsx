import {
  Box,
  Button,
  ExpandableSection,
  SpaceBetween,
  Spinner,
  Textarea,
} from "@cloudscape-design/components";
import { useContext, useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { Global } from "../../common/constant/global";
import { CustomContext } from "../../common/helpers/context";
import { UserState } from "../../common/helpers/store";

const ACTION = "configure_agent";

export default function PostprocessPanel() {
  const [result, setResult] = useState("");

  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const placeholder =
    "If suspicious individuals appear at the entrance, send me an email or 如果门口出现鬼鬼祟祟的人，请给门铃设备发送告警指令";
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const llmConfig = useSelector((state: UserState) => state.llmConfig);
  const { message, sendMessage } = useContext(CustomContext);

  useEffect(() => {
    if (!message?.data) return;
    try {
      const data = JSON.parse(message.data);
      if (data.statusCode === 200 && data.action === ACTION) {
        const vqaResult = JSON.parse(data.body)?.agent_result;
        setResult(vqaResult || "Nothing returned from backend");
      }
    } catch (error) {
      console.error(`Parsing error on action ${ACTION}: `, error);
      setResult("");
    } finally {
      setIsLoading(false);
    }
  }, [message, setResult]);

  return (
    <Box margin={{ left: "m", right: "m" }}>
      <SpaceBetween size="s">
        <ExpandableSection defaultExpanded variant="footer" headerText="Prompt">
          <Box margin={{ left: "l" }}>
            <SpaceBetween size="xs">
              <Textarea
                disabled={isLoading}
                value={prompt}
                onChange={({ detail }) => setPrompt(detail.value)}
                onFocus={() => {
                  if (prompt === "") {
                    setPrompt(placeholder.split("or")[1]);
                  }
                }}
                placeholder={placeholder}
                rows={3}
              />
              <div className="btn-container">
                <Button
                  variant="primary"
                  loading={isLoading}
                  disabled={prompt === "" || isLoading}
                  onClick={() => {
                    setIsLoading(true);
                    if (sendMessage) {
                      sendMessage({
                        action: ACTION,
                        user_id: userInfo.userId,
                        task_id: Global.taskId,
                        agent_prompt: prompt,
                        model: llmConfig.modelId,
                        execute_times: "once",
                      });
                    }
                  }}
                >
                  Run Postprocess
                </Button>
              </div>
            </SpaceBetween>
          </Box>
        </ExpandableSection>

        <hr style={{ border: "0.5px solid #e2e2e2" }} />

        <ExpandableSection
          defaultExpanded
          variant="footer"
          headerText="Results display"
        >
          <Box variant="p" margin={{ left: "l" }}>
            {isLoading ? (
              <>
                <Spinner /> Loading...
              </>
            ) : (
              result ||
              "When messages postprocessing has been finished, the results will be shown here."
            )}
          </Box>

          {/* <Textarea
            value={result}
            onChange={({ detail }) => console.log(detail.value)}
            placeholder="When messages postprocessing has been finished, the results will be shown here."
            disabled
            rows={12}
          /> */}
        </ExpandableSection>
      </SpaceBetween>
    </Box>
  );
}
