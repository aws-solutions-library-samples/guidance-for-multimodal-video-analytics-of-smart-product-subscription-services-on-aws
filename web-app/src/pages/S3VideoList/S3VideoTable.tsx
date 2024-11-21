import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Box,
  Button,
  Header,
  Pagination,
  Table,
  TextFilter,
} from "@cloudscape-design/components";
import moment from "moment";
import { useCallback, useContext, useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { CustomContext } from "../../common/helpers/context";
import { UserState } from "../../common/helpers/store";
import { Link } from "react-router-dom";

type IS3Data = {
  Key: string; //"public/door-bell.mp4";
  LastModified: string; //"2024-08-13 06:12:39+00:00";
  ETag: string; //'"654109431d5010dfe70998dedc0cde8b-2"';
  Size: number; //9851118;
  StorageClass: string; //"STANDARD";
};

const ACTION = "list_s3_videos";

const useDistributions = () => {
  const [distributions, setDistributions] = useState<IS3Data[]>([]);
  const [loading, setLoading] = useState(true);

  const { message, sendMessage, isConnected } = useContext(CustomContext);
  const userId = useSelector((state: UserState) => state.userInfo.userId);

  const getDistributions = useCallback(() => {
    if (!isConnected || !sendMessage || !userId) return;
    setLoading(true);
    setDistributions([]);
    console.log("send WS message to fetch [public] data");
    sendMessage({ action: ACTION, user_id: "public" });
    setTimeout(() => {
      console.log("send WS message to fetch [user] data");
      sendMessage({ action: ACTION, user_id: userId });
    }, 800);
  }, [isConnected, userId, sendMessage]);

  useEffect(() => {
    getDistributions();
    return () => {
      setDistributions([]);
    };
  }, [getDistributions]);

  useEffect(() => {
    if (!message?.data) return;
    try {
      const data = JSON.parse(message.data);
      if (data?.statusCode === 200 && data?.action === ACTION) {
        const list = JSON.parse(data.body)?.s3_videos;
        if (list?.length) {
          if (list[0].Key.indexOf("public/") !== -1) {
            // [public] data e.g. "public/door-bell.mp4"
            const publicS3VideoList = list.filter(
              (item: any) => item.Key.split("/")[1] !== ""
            );
            console.info({ publicS3VideoList });
            setDistributions((prev) => prev.concat(publicS3VideoList));
          } else {
            // [user] data
            const s3VideoList = list.filter(
              (item: any) => item.Key.split("/")[1] !== ""
            );
            console.info({ s3VideoList });
            setDistributions((prev) => prev.concat(s3VideoList));
          }
        }
      }
    } catch (error) {
      console.error(error);
      setDistributions([]);
    } finally {
      setLoading(false);
    }
  }, [message]);

  return {
    getDistributions,
    distributions,
    setDistributions,
    loading,
    setLoading,
  };
};
const S3VideoTable = () => {
  const { distributions, loading, getDistributions } = useDistributions();

  const {
    items,
    actions,
    collectionProps,
    filterProps,
    paginationProps,
    filteredItemsCount,
  } = useCollection(distributions, {
    pagination: { pageSize: 10 },
    sorting: {},
    filtering: {
      noMatch: (
        <Box textAlign="center" color="inherit">
          <b>No matches</b>
          <Box color="inherit" margin={{ top: "xxs", bottom: "s" }}>
            No results match your query
          </Box>
          <Button onClick={() => actions.setFiltering("")}>Clear filter</Button>
        </Box>
      ),
    },
  });

  return (
    <Table<IS3Data>
      {...collectionProps}
      items={items}
      loading={loading}
      loadingText="Loading resources"
      pagination={<Pagination {...paginationProps} />}
      header={
        <Header
          variant="h2"
          counter={`(${distributions.length} item${
            distributions.length > 1 ? "s" : ""
          })`}
          actions={<Button iconName="refresh" onClick={getDistributions} />}
        >
          S3 Video Stream List
        </Header>
      }
      filter={
        <TextFilter
          {...filterProps}
          countText={`${filteredItemsCount} ${
            filteredItemsCount === 1 ? "match" : "matches"
          }`}
          filteringPlaceholder="Search Video"
        />
      }
      columnDefinitions={[
        {
          id: "name",
          cell: (item) => (
            <Link to={`/s3/video-play-analytics?type=s3&name=${item.Key}`}>
              {item.Key.split("/")[1]}
            </Link>
          ),
          header: "Name",
          minWidth: "100px",
          sortingField: "key",
        },
        {
          id: "type",
          cell: (item) => item.Key.split(".")[1],
          header: "Type",
          minWidth: "80px",
        },
        {
          id: "last modified",
          cell: (item) =>
            moment(new Date(item.LastModified)).format("YYYY-MM-DD HH:mm:ss"),
          header: "Last modified",
          minWidth: "100px",
          sortingField: "lastModified",
        },
        {
          id: "size",
          cell: (item) => formatBytes(item.Size),
          header: "Size",
          minWidth: "80px",
          sortingField: "size",
        },
      ]}
    />
  );
};

function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024,
    dm = decimals < 0 ? 0 : decimals,
    sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
    i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

export default S3VideoTable;
