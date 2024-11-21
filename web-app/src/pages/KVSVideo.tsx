import {
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DEFAULT_STREAM_NAME } from "../aws-config";
import { CustomContext } from "../common/helpers/context";

export default function KVSVideo() {
  const [streamName, setStreamName] = useState(DEFAULT_STREAM_NAME);
  const selectedMode = "LIVE";
  const navigate = useNavigate();

  const { setSideNavOpen } = useContext(CustomContext);
  useEffect(() => {
    setSideNavOpen({ collapsed: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <Container>
      <form onSubmit={(e) => e.preventDefault()}>
        <Form
          header={<Header>KVS WebRTC Viewer</Header>}
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                variant="primary"
                onClick={() => {
                  navigate(
                    `/kvs/video-play-analytics?type=kvs&name=${streamName}&mode=${selectedMode}`
                  );
                }}
              >
                Start KVS
              </Button>
            </SpaceBetween>
          }
        >
          <SpaceBetween direction="vertical" size="l">
            <FormField label="Stream name" stretch>
              <Input
                placeholder="Please provide the KVS stream name"
                onChange={({ detail }) => setStreamName(detail.value)}
                value={streamName}
              />
            </FormField>
          </SpaceBetween>
        </Form>
      </form>
    </Container>
  );
}
