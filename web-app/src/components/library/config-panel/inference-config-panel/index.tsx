import {
  ExpandableSection,
  FormField,
  Input,
  Select,
  Slider,
  SpaceBetween,
  Toggle,
} from "@cloudscape-design/components";
import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { ActionType } from "../../../../common/helpers/store";
import "./style.scss";
import { InferenceConfigState } from "./types";

export const InferenceConfiguration = () => {
  const dispatch = useDispatch();

  const [imageListLength, setImageListLength] = useState(1);
  const [listUpdateGap, setListUpdateGap] = useState(1);
  const [frameGap, setFrameGap] = useState(20);
  const [selectedResolution, setSelectedResolution] = useState({
    label: "raw",
    value: "raw",
  });
  const [durationTime, setDurationTime] = useState(60);
  const [isCheckedUseECS, setIsCheckedUseECS] = useState(false);

  useEffect(() => {
    const configInfo: InferenceConfigState = {
      frequency: frameGap,
      list_length: imageListLength,
      interval: listUpdateGap,
      selectedResolution: selectedResolution.value,
      durationTime: durationTime,
      platform: isCheckedUseECS ? "ecs" : "lambda",
    };
    dispatch({ type: ActionType.UpdateInferConfig, state: configInfo });
  }, [
    imageListLength,
    listUpdateGap,
    frameGap,
    selectedResolution.value,
    durationTime,
    dispatch,
    isCheckedUseECS,
  ]);
  const [durationTimeError, setDurationTimeError] = useState("");

  return (
    <ExpandableSection
      defaultExpanded
      variant="footer"
      headerText="Inference Configuration"
    >
      <SpaceBetween size="s">
        <FormField
          description="The number of images required as input for one inference cycle"
          label="Image count per cycle"
        >
          <Input
            type="number"
            inputMode="decimal"
            value={imageListLength.toString()}
            onChange={({ detail }) => {
              if (Number(detail.value) > 0 && Number(detail.value) <= 20) {
                setImageListLength(Number(detail.value));
                const temp = Math.ceil(Number(detail.value) * listUpdateGap);
                if (temp > frameGap) {
                  setFrameGap(temp);
                }
              }
            }}
          />
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                min={1}
                max={20}
                value={imageListLength}
                onChange={({ detail }) => {
                  setImageListLength(detail.value);
                  const temp = Math.ceil(detail.value * listUpdateGap);
                  if (temp > frameGap) {
                    setFrameGap(temp);
                  }
                }}
              />
            </div>
          </div>
        </FormField>

        <FormField
          description="The interval between each image in an inference cycle"
          label="Interval time (seconds)"
        >
          <Input
            onChange={({ detail }) => {
              if (Number(detail.value) >= 0.5 && Number(detail.value) <= 4) {
                setListUpdateGap(Number(detail.value));
                const temp = Math.ceil(Number(detail.value) * imageListLength);
                if (temp > frameGap) {
                  setFrameGap(temp);
                }
              }
            }}
            value={listUpdateGap.toString()}
            type="number"
            inputMode="numeric"
          />
          <Slider
            min={0.5}
            max={4}
            step={0.1}
            value={listUpdateGap}
            onChange={({ detail }) => {
              setListUpdateGap(detail.value);
              const temp = Math.ceil(detail.value * imageListLength);
              if (temp > frameGap) {
                setFrameGap(temp);
              }
            }}
          />
        </FormField>

        <FormField
          description="How often to perform an inference cycle"
          label="Frequency (seconds)"
        >
          <Input
            onChange={({ detail }) => {
              if (
                Number(detail.value) >= imageListLength * listUpdateGap &&
                Number(detail.value) <= 60
              ) {
                setFrameGap(Number(detail.value));
              }
            }}
            value={frameGap.toString()}
            type="number"
          />
          <Slider
            min={Math.ceil(imageListLength * listUpdateGap)}
            max={60}
            value={frameGap}
            onChange={({ detail }) => {
              setFrameGap(detail.value);
            }}
          />
        </FormField>

        <FormField
          description="The actual image size for performing inference"
          label="Image size"
        >
          <Select
            selectedOption={selectedResolution}
            onChange={({ detail }) =>
              // eslint-disable-next-line @typescript-eslint/ban-ts-comment
              // @ts-expect-error
              setSelectedResolution(detail.selectedOption)
            }
            options={[
              { label: "raw", value: "raw" },
              { label: "640 x 480", value: "640*480" },
              { label: "1280 x 720", value: "1280*720" },
              // { label: "1920 x 1080", value: "1920*1080" },
            ]}
          />
        </FormField>

        <FormField
          description="The duration of inference from the start of the video"
          label="Duration time (seconds)"
          errorText={durationTimeError}
        >
          <Input
            onBlur={() => {
              if (durationTime < 30) {
                setDurationTime(30);
              }
              if (durationTime > 600) {
                setDurationTime(600);
              }
              setDurationTimeError("");
            }}
            onChange={({ detail }) => {
              const n = Number(detail.value);
              setDurationTime(n);
              if (n >= 30 && n <= 600) {
                setDurationTimeError("");
              } else {
                setDurationTimeError("Must be a value between 30 and 600");
              }
            }}
            value={durationTime.toString()}
            type="number"
            inputMode="numeric"
          />
          <Slider
            onChange={({ detail }) => {
              setDurationTimeError("");
              setDurationTime(detail.value);
            }}
            value={durationTime}
            max={600}
            min={30}
          />
        </FormField>

        <FormField
          description="To launch advanced analysis in ECS"
          label="Platform"
        >
          <Toggle
            onChange={({ detail }) => setIsCheckedUseECS(detail.checked)}
            checked={isCheckedUseECS}
          >
            use ECS
          </Toggle>
        </FormField>
      </SpaceBetween>
    </ExpandableSection>
  );
};
