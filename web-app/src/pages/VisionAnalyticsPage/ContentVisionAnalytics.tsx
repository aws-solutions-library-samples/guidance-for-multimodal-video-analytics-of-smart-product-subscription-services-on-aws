import {
  Button,
  Container,
  ExpandableSection,
  Form,
  FormField,
  Grid,
  Header,
  Select,
  SpaceBetween,
  Tabs,
  Textarea,
} from "@cloudscape-design/components";
import { useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useSelector } from "react-redux";
import useRequest from "../../api/hooks/useRequest";
import {
  defaultSystemPrompt,
  defaultUserPrompt,
  INDUSTRY_KEYS,
} from "../../common/constant/constants";
import { Global } from "../../common/constant/global";
import { CustomContext } from "../../common/helpers/context";
import { UserState } from "../../common/helpers/store";
import { ChatBotHistoryItem } from "../../components/library/chatbot-panel/types";
import { HLSPlayer } from "../../components/library/player-panel/player-kvs";
import { S3Player } from "../../components/library/player-panel/player-s3";
import {
  IPromptDatum,
  IRequestTypeCreatePrompt,
  usePromptList,
} from "../PromptList";
import AnalyticsResponse from "./AnalyticsResponse";
import Configuration from "./Configuration";
import FrameRetrieve from "./FrameRetrieve";
import PostprocessPanel from "./PostprocessPanel";
import VQAPanel from "./VQAPanel";
import { useNavigate } from "react-router-dom";

// const ACTION_LIST_PROMPT = "list_prompt";
const ACTION_WEBSOCKET_NOTIFY = "websocket_notify";

type IRequestTypeUpdatePrompt = Required<
  Pick<
    IRequestTypeCreatePrompt,
    "user_id" | "prompt_id" | "system_prompt" | "user_prompt"
  >
>;
type IPromptOption = {
  label: string;
  value: Required<IPromptDatum["prompt_id"]>;
};
type IPromptOptions = { label: string; options: IPromptOption[] }[];

export default function ContentVisionAnalytics({
  type,
  name,
}: {
  type: string;
  name: string;
}) {
  // distributions: data source of Analytic Details Table
  const [distributions, setDistributions] = useState<any[]>([]);
  // summary: summary result of Analytics Tab
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingAnalyticDetails, setLoadingAnalyticDetails] = useState(false);
  const [tokens, setTokens] = useState<number | null>(null);
  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>(
    []
  );
  const { sendMessage, message } = useContext(CustomContext);
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const llmConfig = useSelector((state: UserState) => state.llmConfig);
  const inferenceConfig = useSelector(
    (state: UserState) => state.inferenceConfig
  );
  const [selectedOption, setSelectedOption] = useState<IPromptOption>();
  const [options, setOptions] = useState<IPromptOptions>([]);

  const [systemPrompt, setSystemPrompt] = useState(defaultSystemPrompt);
  const [userPrompt, setUserPrompt] = useState(defaultUserPrompt);
  const [isSelectedPublic, setIsSelectedPublic] = useState(false);

  useEffect(() => {
    if (!message?.data) return;
    try {
      const data = JSON.parse(message.data);

      switch (data.action) {
        case ACTION_WEBSOCKET_NOTIFY: {
          if (data.summary_result) {
            setSummary(data.summary_result);
            setIsLoading(false);
          } else {
            setDistributions((prev) =>
              [...prev, data].filter(
                (obj, index, self) =>
                  index === self.findIndex((o) => o.timestamp === obj.timestamp)
              )
            );
            setLoadingAnalyticDetails(false);
            if (data.tag === "end") Global.taskId = data.task_id;
          }
          break;
        }
        default: {
          break;
        }
      }
    } catch (error) {
      console.error("Content Parsing Error: ", error);
    }
  }, [message?.data]);

  useEffect(() => {
    if (inferenceConfig.selectedResolution !== "raw") {
      const { selectedResolution, durationTime, frequency, list_length } =
        inferenceConfig;
      const width = Number(selectedResolution.split("*")[0]);
      const height = Number(selectedResolution.split("*")[1]);
      setTokens(
        (Math.floor(durationTime / frequency) * list_length * width * height) /
          750
      );
    } else {
      setTokens(null);
    }
  }, [inferenceConfig, setTokens]);

  const { run: updatePrompt, loading: updatingPrompt } = useRequest<
    any,
    IRequestTypeUpdatePrompt
  >("/prompt", { method: "PUT" });
  const { user_id, loadingListData, listData, getListData } =
    usePromptList(true);

  useEffect(() => {
    if (!listData?.length) return;
    const newOptions = listData.reduce(
      (prev: IPromptOptions, curr: IPromptDatum) => {
        const { industry_type, prompt_id, topic_name } = curr;
        prev.forEach(
          (o) =>
            o.label.toLowerCase() === industry_type.toLowerCase() &&
            o.options.push({ label: topic_name, value: prompt_id })
        );
        return prev;
      },
      INDUSTRY_KEYS.map((v) => ({ label: v, options: [] })) as IPromptOptions
    );
    setOptions(newOptions);
  }, [listData]);
  const navigate = useNavigate();

  return (
    <SpaceBetween size="s">
      <hr style={{ border: "0.5px solid #e2e2e2" }} />
      <Grid disableGutters gridDefinition={[{ colspan: 9 }, { colspan: 3 }]}>
        <SpaceBetween direction="vertical" size="s">
          <Header variant="h3">
            Vision Analytics - Type: <u>{type}</u> , Name: <u>{name}</u>
          </Header>

          <hr style={{ border: "0.5px solid #e2e2e2" }} />

          <ExpandableSection
            defaultExpanded
            variant="footer"
            headerText="Player"
          >
            {type === "s3" ? <S3Player name={name} /> : <HLSPlayer />}
          </ExpandableSection>

          <Form>
            <SpaceBetween direction="vertical" size="l">
              <FormField label="Prompt" stretch>
                <Select
                  selectedOption={selectedOption || null}
                  onChange={({ detail: { selectedOption: op } }) => {
                    const { label, value } = op;
                    setSelectedOption({ label: label!, value });
                    const prompt = listData?.find(
                      (item) => item.prompt_id === value
                    );
                    if (prompt) {
                      setSystemPrompt(prompt.system_prompt);
                      setUserPrompt(prompt.user_prompt);
                      setIsSelectedPublic(!!prompt.is_public);
                    }
                  }}
                  loadingText="Loading prompts"
                  statusType={loadingListData ? "loading" : "finished"}
                  options={options}
                  ariaLabel="Autosuggest example with suggestions groups"
                  placeholder="Please choose a prompt from the list"
                  empty="No matches found"
                />
              </FormField>
              <FormField label="System Prompt" stretch>
                <Textarea
                  value={systemPrompt}
                  onChange={({ detail }) => setSystemPrompt(detail.value)}
                  placeholder="Write a system prompt here...(ENTER to start a new line)"
                  rows={6}
                />
              </FormField>
              <FormField label="User Prompt" stretch>
                <Textarea
                  value={userPrompt}
                  onChange={({ detail }) => setUserPrompt(detail.value)}
                  placeholder="Write a user prompt here...(ENTER to start a new line and Run to  generate a response)"
                  rows={6}
                />
              </FormField>

              <div
                style={{
                  width: "100%",
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <div style={{ display: "flex", gap: "12px" }}>
                  <Button
                    loading={updatingPrompt}
                    disabled={isSelectedPublic}
                    onClick={async () => {
                      if (!selectedOption?.value)
                        return toast.error("Please selecte a prompt first!");
                      const { message } = await updatePrompt({
                        system_prompt: systemPrompt,
                        user_prompt: userPrompt,
                        prompt_id: selectedOption.value,
                        user_id,
                      });
                      if (message) toast.success(message);
                      getListData();
                    }}
                  >
                    {isSelectedPublic ? "Public Prompt" : "Update Prompt"}
                  </Button>
                  <Button variant="link" onClick={() => navigate("/prompt")}>
                    <small>manage prompt</small>
                  </Button>
                </div>
                <div>
                  {tokens !== null && (
                    <Button iconName="suggestions" variant="inline-link">
                      Estimated number of used tokens: {tokens}
                    </Button>
                  )}
                  <Button
                    variant="primary"
                    disabled={!systemPrompt || !userPrompt || isLoading}
                    loading={isLoading}
                    onClick={() => {
                      if (!sendMessage)
                        return toast.error("No sendMessage instance");
                      sendMessage({
                        action: "configure_video_resource",
                        // video resource params
                        video_source_type: type,
                        video_source_content: name,
                        user_id: userInfo.userId,

                        // frame extraction params
                        frequency: inferenceConfig.frequency, // how often to perform inference once
                        list_length: inferenceConfig.list_length, // number of images per inference
                        interval: inferenceConfig.interval, // how often to catch an image
                        image_size: inferenceConfig.selectedResolution, // actual image size to perform inference
                        duration: inferenceConfig.durationTime, // whole inference duration time
                        platform: inferenceConfig.platform || "lambda", // lambda or ecs

                        // LLM params
                        system_prompt: systemPrompt,
                        user_prompt: userPrompt,
                        model_id: llmConfig.modelId,
                        temperature: llmConfig.temperature,
                        top_p: llmConfig.topP,
                        top_k: llmConfig.topK,
                        max_tokens: llmConfig.maxLength,
                      });
                      setIsLoading(true);
                      setLoadingAnalyticDetails(true);
                      setDistributions([]);
                      setSummary("");
                    }}
                  >
                    Run Analytics
                  </Button>
                </div>
              </div>
            </SpaceBetween>
          </Form>
        </SpaceBetween>

        <Configuration />
      </Grid>

      <Container>
        <Tabs
          fitHeight
          tabs={[
            {
              label: "Analytics",
              id: "first",
              content: (
                <AnalyticsResponse
                  isLoading={isLoading}
                  loadingAnalyticDetails={loadingAnalyticDetails}
                  distributions={distributions}
                  summary={summary}
                  setDistributions={setDistributions}
                  setIsLoading={setIsLoading}
                />
              ),
            },
            {
              label: "Postprocess",
              id: "second",
              content: <PostprocessPanel />,
              disabled: Global.taskId === "",
            },
            {
              label: "VQA",
              id: "third",
              content: (
                <VQAPanel
                  messageHistory={messageHistory}
                  setMessageHistory={setMessageHistory}
                  isLoading={isLoading}
                  setLoading={setIsLoading}
                />
              ),
              disabled: Global.taskId === "",
            },
            {
              label: "Frame Retrieve",
              id: "fourth",
              content: <FrameRetrieve />,
            },
          ]}
        />
      </Container>
    </SpaceBetween>
  );
}
