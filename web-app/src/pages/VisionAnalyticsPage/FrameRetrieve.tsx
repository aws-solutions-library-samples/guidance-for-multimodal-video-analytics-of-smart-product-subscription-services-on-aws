import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Box,
  Button,
  Form,
  FormField,
  Header,
  Pagination,
  SpaceBetween,
  Table,
  Textarea,
} from "@cloudscape-design/components";
import React, { useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useSelector } from "react-redux";
import { CustomContext } from "../../common/helpers/context";
import { UserState } from "../../common/helpers/store";

type IPropsFrameRetrieve = any;
type IOSRetrieveDatum = {
  image_url: string;
  description: string;
  timestamp: string;
  video_resource: string;
  score: string;
};

export type IMessageData<T = any> = {
  action: string;
  statusCode: number;
  body: T;
};

const ACTION = "opensearch_retrieve";

const FrameRetrieve: React.FC<IPropsFrameRetrieve> = () => {
  const { message, sendMessage, isConnected } = useContext(CustomContext);
  const userId = useSelector((state: UserState) => state?.userInfo?.userId);
  const [keyword, setKeyWord] = useState("");
  const [retrieving, setRetrieving] = useState(false);
  const [dataSource, setDataSource] = useState<IOSRetrieveDatum[]>([]);
  const { items, paginationProps } = useCollection(dataSource, {
    pagination: { pageSize: 5 },
  });

  useEffect(() => {
    if (!message?.data) return;
    try {
      const data: IMessageData<IOSRetrieveDatum[]> = JSON.parse(message.data);
      if (data.action === ACTION && data.statusCode === 200 && data.body) {
        setDataSource(data.body);
        toast.success("Result retrieved!");
      }
    } catch (error) {
      setDataSource([]);
      toast.error(JSON.stringify(error));
      console.error(`Error on processing action: ${ACTION}: `, error);
      toast.error(
        "Retrieve failed... please checkout the browser console for more info..."
      );
    } finally {
      setRetrieving(false);
    }
  }, [message]);

  return (
    <Box margin={{ left: "m", right: "m" }}>
      <SpaceBetween size="l">
        <Form
          header={<Header>Keyword</Header>}
          actions={
            <Button
              loading={retrieving}
              disabled={!isConnected || !keyword || retrieving}
              onClick={() => {
                if (!userId) return toast.error("No User ID");
                if (!keyword) return toast.error("No Keyword");
                if (!sendMessage) return toast.error("No sendMessage instance");
                setRetrieving(true);
                sendMessage({
                  action: ACTION,
                  user_id: userId,
                  keyword,
                });
              }}
            >
              Retrieve
            </Button>
          }
        >
          <FormField stretch>
            <Textarea
              value={keyword}
              onChange={({ detail }) => setKeyWord(detail.value)}
              placeholder="Please enter your keyword here"
              rows={1}
            />
          </FormField>
        </Form>
        <hr style={{ border: "0.5px solid #e2e2e2" }} />
        <Table<IOSRetrieveDatum>
          variant="embedded"
          wrapLines={true}
          items={items}
          pagination={<Pagination {...paginationProps} />}
          loadingText="Retrieving resources"
          loading={retrieving}
          header={
            <Header counter={`(${items.length} items)`}>
              Result Retrieved
            </Header>
          }
          empty={
            <Box margin={{ vertical: "xs" }} textAlign="center" color="inherit">
              <SpaceBetween size="m">
                <b>No resources</b>
              </SpaceBetween>
            </Box>
          }
          columnDefinitions={[
            {
              id: "image_url",
              cell: (item) => (
                <img
                  src={item.image_url}
                  alt={item.description}
                  style={{ width: "300px", height: "auto" }}
                />
              ),
              header: "Image",
              // width: 80,
            },
            {
              id: "description",
              cell: (item) => <div>{item.description}</div>,
              header: "Description",
            },
            {
              id: "timestamp",
              cell: (item) => item.timestamp,
              header: "Time",
            },
            {
              id: "video_resource",
              cell: (item) => item.video_resource,
              header: "Video Resource",
            },
            {
              id: "score",
              cell: (item) => item.score,
              header: "Score",
            },
          ]}
        />
      </SpaceBetween>
    </Box>
  );
};

export default FrameRetrieve;
