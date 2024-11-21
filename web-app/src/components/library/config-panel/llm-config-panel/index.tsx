import {
  ExpandableSection,
  FormField,
  Input,
  Select,
  Slider,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useDispatch } from "react-redux";
import CONFIG_JSON from "../../../../../../deployment/cdk/model_config.json";
import { ActionType } from "../../../../common/helpers/store";
import "./style.scss";
import { LLMConfigState } from "./types";

export const LLMConfiguration = () => {
  const dispatch = useDispatch();

  const [modelId, setModelId] = useState({
    value: CONFIG_JSON?.analytics_model[0],
  });
  const [temperature, setTemperature] = useState(0.1);
  const [topP] = useState(1);
  const [topK, setTopK] = useState(250);
  const [maximumLength, setMaximumLength] = useState(2048);

  useEffect(() => {
    const llmConfigInfo: LLMConfigState = {
      modelId: modelId.value,
      temperature,
      topP,
      topK,
      maxLength: maximumLength,
    };
    dispatch({ type: ActionType.UpdateLLMConfig, state: llmConfigInfo });
  }, [modelId, temperature, topP, topK, maximumLength, dispatch]);

  if (!CONFIG_JSON?.analytics_model?.length) {
    toast.error(
      "Config.json file is empty. Please at least configure analytics_model..."
    );
    return null;
  }
  return (
    <ExpandableSection
      defaultExpanded
      variant="footer"
      headerText="Claude3 Configuration"
    >
      <SpaceBetween size="l">
        <FormField label="Model" description="Select a model for analytics">
          <Select
            selectedOption={modelId}
            onChange={({ detail }) =>
              // eslint-disable-next-line @typescript-eslint/ban-ts-comment
              // @ts-expect-error
              setModelId(detail.selectedOption)
            }
            options={CONFIG_JSON.analytics_model.map((v) => ({ value: v }))}
          />
        </FormField>

        <FormField label="Temperature">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="decimal"
              value={temperature.toString()}
              onChange={({ detail }) => {
                if (Number(detail.value) > 1 || Number(detail.value) < 0) {
                  return;
                }
                setTemperature(Number(detail.value));
              }}
              controlId="temperature-input"
              step={0.1}
            />
          </div>
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                onChange={({ detail }) => setTemperature(detail.value)}
                value={temperature}
                max={1}
                min={0}
                step={0.1}
                valueFormatter={(e) => e.toFixed(2)}
              />
            </div>
          </div>
        </FormField>

        {/* <FormField label="Top P">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="numeric"
              value={topP.toString()}
              onChange={({ detail }) => {
                if (Number(detail.value) > 1 || Number(detail.value) < 0) {
                  return;
                }
                setTopP(Number(detail.value));
              }}
              controlId="topp-input"
              step={0.001}
            />
          </div>
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                onChange={({ detail }) => setTopP(detail.value)}
                value={topP}
                max={1}
                min={0}
                step={0.001}
                valueFormatter={(e) => e.toFixed(3)}
              />
            </div>
          </div>
        </FormField> */}

        <FormField label="Top K">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="numeric"
              value={topK.toString()}
              onChange={({ detail }) => {
                if (Number(detail.value) > 500 || Number(detail.value) < 0) {
                  return;
                }
                setTopK(Number(detail.value));
              }}
              controlId="topk-input"
              step={1}
            />
          </div>
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                onChange={({ detail }) => setTopK(detail.value)}
                value={topK}
                max={500}
                min={0}
                step={1}
              />
            </div>
          </div>
        </FormField>

        <FormField label="Maximum Length">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="numeric"
              value={maximumLength.toString()}
              onChange={({ detail }) => {
                if (Number(detail.value) >= 0 && Number(detail.value) <= 4096) {
                  setMaximumLength(Number(detail.value));
                }
              }}
              controlId="maximum-length-input"
              step={1}
            />
          </div>
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                onChange={({ detail }) => setMaximumLength(detail.value)}
                value={maximumLength}
                min={0}
                max={4096}
                step={1}
              />
            </div>
          </div>
        </FormField>
      </SpaceBetween>
    </ExpandableSection>
  );
};
