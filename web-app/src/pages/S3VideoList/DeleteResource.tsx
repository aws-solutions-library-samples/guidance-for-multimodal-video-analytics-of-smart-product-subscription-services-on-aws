import {
  Button,
  Container,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";
import React, { useCallback, useContext, useEffect, useState } from "react";
import { CustomContext } from "../../common/helpers/context";
import { useSelector } from "react-redux";
import { UserState } from "../../common/helpers/store";
import toast from "react-hot-toast";

const ACTION = "delete_resource";
const DeleteResource: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { message, sendMessage, setMessage } = useContext(CustomContext);
  const userId = useSelector((state: UserState) => state.userInfo.userId);
  const del = useCallback(
    (period: number) => {
      if (!sendMessage) return;
      if (period < 0)
        return console.error('"period" can NOT be a negative number');
      setLoading(true);
      sendMessage({ action: ACTION, user_id: userId, period });
    },
    [sendMessage, userId]
  );

  useEffect(() => {
    if (!message?.data) return;
    try {
      const data = JSON.parse(message.data);
      if (data?.statusCode === 200 && data?.action === ACTION) {
        const msg = JSON.parse(data.body);
        toast.success(msg || "The resource has been successfully deleted!");
        setMessage(undefined);
      }
    } catch (error) {
      console.error(error);
      toast.error("Failed to delete the resource...");
    } finally {
      setLoading(false);
    }
  }, [message, setMessage]);

  return (
    <Container header={<Header>Delete Resources</Header>}>
      <SpaceBetween size="m" direction="horizontal">
        <Button
          disabled={loading}
          loading={loading}
          variant="primary"
          onClick={() => del(0)}
        >
          Delete All
        </Button>
        <Button disabled={loading} loading={loading} onClick={() => del(1)}>
          Delete 1 Day Before
        </Button>
        <Button disabled={loading} loading={loading} onClick={() => del(3)}>
          Delete 3 Days Before
        </Button>
      </SpaceBetween>
    </Container>
  );
};

export default DeleteResource;
