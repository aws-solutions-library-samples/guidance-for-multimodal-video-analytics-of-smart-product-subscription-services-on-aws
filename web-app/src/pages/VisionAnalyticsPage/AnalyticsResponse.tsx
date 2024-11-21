import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Box,
  Button,
  ContentLayout,
  Header,
  Pagination,
  SpaceBetween,
  Spinner,
  Table,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction } from "react";

const AnalyticsResponse = ({
  isLoading,
  loadingAnalyticDetails,
  summary,
  distributions,
}: {
  isLoading: boolean;
  loadingAnalyticDetails: boolean;
  distributions: any[];
  summary: string;
  setDistributions: Dispatch<SetStateAction<any[]>>;
  setIsLoading: Dispatch<SetStateAction<boolean>>;
}) => {
  const { items, actions, collectionProps, paginationProps } = useCollection(
    distributions,
    {
      pagination: { pageSize: 5 },
      sorting: {},
      filtering: {
        noMatch: (
          <Box textAlign="center" color="inherit">
            <b>No matches</b>
            <Box color="inherit" margin={{ top: "xxs", bottom: "s" }}>
              No results match your query
            </Box>
            <Button onClick={() => actions.setFiltering("")}>
              Clear filter
            </Button>
          </Box>
        ),
      },
    }
  );

  return (
    <Box margin={{ left: "m", right: "m" }}>
      <SpaceBetween size={"m"}>
        <ContentLayout header={<Header variant="h2">Summary result</Header>}>
          {isLoading ? (
            <>
              <Spinner /> Loading...
            </>
          ) : (
            <Box variant="p" padding={{ left: "m", right: "m" }}>
              {summary || "Please run the analytics to get the summary result"}
            </Box>
          )}
        </ContentLayout>
        <hr style={{ border: "0.5px solid #e2e2e2" }} />
        <Table
          {...collectionProps}
          loading={loadingAnalyticDetails}
          loadingText="Loading resources"
          variant="embedded"
          items={items}
          resizableColumns
          wrapLines={true}
          header={
            <Header variant="h2" counter={`(${distributions.length} items)`}>
              Analytic Details
            </Header>
          }
          empty={
            <Box margin={{ vertical: "xs" }} textAlign="center" color="inherit">
              <b>No response here</b>
            </Box>
          }
          pagination={<Pagination {...paginationProps} />}
          columnDefinitions={[
            {
              id: "timestamp",
              cell: (item) => item["timestamp"],
              header: "Time",
              sortingField: "timestamp",
              width: 80,
            },
            {
              id: "analytics",
              cell: (item) => <div>{item["analysis_result"]}</div>,
              header: "Analytics",
            },
            {
              id: "key frame",
              cell: (item) => (
                <img className="img" src={item["img_url"]} alt="Image" />
              ),
              header: "Key frame",
            },
          ]}
        />
      </SpaceBetween>
    </Box>
  );
};

export default AnalyticsResponse;
