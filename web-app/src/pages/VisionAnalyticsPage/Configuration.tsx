import { Box, Grid, Header, SpaceBetween } from "@cloudscape-design/components";
import { InferenceConfiguration } from "../../components/library/config-panel/inference-config-panel";
import { LLMConfiguration } from "../../components/library/config-panel/llm-config-panel";

const Configuration = () => {
  return (
    <Grid disableGutters gridDefinition={[{ colspan: 2 }, { colspan: 10 }]}>
      <div className="line"></div>
      <Box padding={{ left: "s", right: "s" }}>
        <SpaceBetween size="s">
          <Header variant="h2">Configuration</Header>
          <LLMConfiguration />
          <InferenceConfiguration />
        </SpaceBetween>
      </Box>
    </Grid>
  );
};
export default Configuration;
