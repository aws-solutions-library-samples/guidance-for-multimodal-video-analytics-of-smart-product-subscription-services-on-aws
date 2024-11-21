import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Box,
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  Pagination,
  Select,
  SelectProps,
  SpaceBetween,
  Table,
  Textarea,
  TextFilter,
} from "@cloudscape-design/components";
import React, { useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useSelector } from "react-redux";
import useRequest from "../api/hooks/useRequest";
import { INDUSTRY_KEYS } from "../common/constant/constants";
import { CustomContext } from "../common/helpers/context";
import { UserState } from "../common/helpers/store";

const PATH_LIST = "/prompt-list";
const PATH = "/prompt";
const OPTIONS = INDUSTRY_KEYS.map((v) => ({ label: v, value: v }));

type IRequestTypeDeletePrompt = { prompt_id: string; user_id: string };
export type IRequestTypeCreatePrompt = IPromptDatum & { user_id: string };
export type IPromptDatum = {
  prompt_id?: string;
  industry_type: (typeof OPTIONS)[number]["value"];
  topic_name: string;
  system_prompt: string;
  user_prompt: string;
  is_public?: boolean;
};
const initPromptCreate: Omit<IPromptDatum, "industry_type"> & {
  industryOption: SelectProps.Option;
} = {
  industryOption: OPTIONS[0],
  topic_name: "",
  system_prompt: "",
  user_prompt: "",
};

// eslint-disable-next-line react-refresh/only-export-components
export const usePromptList = (initGet = false) => {
  const user_id = useSelector((state: UserState) => state.userInfo.userId);
  const {
    loading: loadingListData,
    data: listData,
    run: getListData,
  } = useRequest<IPromptDatum[], { user_id: string }>(
    PATH_LIST,
    {
      method: "GET",
      params: { user_id },
      onError(error) {
        console.error(error);
      },
    },
    []
  );

  useEffect(() => {
    if (initGet && user_id) getListData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initGet, user_id]);
  return { user_id, loadingListData, listData, getListData };
};

const PromptList: React.FC = () => {
  const [promptData, setPromptData] = useState(initPromptCreate);
  const { user_id, loadingListData, listData, getListData } =
    usePromptList(true);

  const { loading: creatingPrompt, run: createPrompt } = useRequest<
    any,
    IRequestTypeCreatePrompt
  >(PATH, { method: "POST" });

  const { loading: deletingPrompt, run: delPrompt } = useRequest<
    any,
    IRequestTypeDeletePrompt
  >(PATH, { method: "DELETE" });

  const {
    items,
    actions,
    collectionProps,
    paginationProps,
    filteredItemsCount,
    filterProps,
  } = useCollection(listData || [], {
    pagination: { pageSize: 5 },
    sorting: {
      defaultState: { sortingColumn: { sortingField: "industry_type" } },
    },
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

  const { setSideNavOpen } = useContext(CustomContext);
  useEffect(() => {
    setSideNavOpen({ collapsed: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return !user_id ? (
    "Loading..."
  ) : (
    <SpaceBetween size="m">
      <Container header={<Header>Create a new prompt</Header>}>
        <form onSubmit={(e) => e.preventDefault()}>
          <Form
            actions={
              <Button
                variant="primary"
                iconName="status-positive"
                loading={creatingPrompt}
                onClick={async () => {
                  const {
                    industryOption: { value: industry_type },
                    topic_name,
                    system_prompt,
                    user_prompt,
                  } = promptData;
                  if (!topic_name)
                    return toast("Topic name is required", {
                      icon: "⚠️",
                    });
                  if (!system_prompt)
                    return toast("System Prompt is required", {
                      icon: "⚠️",
                    });
                  if (!user_prompt)
                    return toast("User Prompt is required", {
                      icon: "⚠️",
                    });

                  const { message } = await createPrompt({
                    industry_type:
                      industry_type as IPromptDatum["industry_type"],
                    topic_name,
                    system_prompt,
                    user_prompt,
                    user_id,
                  });
                  if (message) toast.success(message);
                  getListData();
                  setPromptData(initPromptCreate);
                }}
              >
                Create
              </Button>
            }
          >
            <SpaceBetween size="l">
              <FormField label="Industry" stretch>
                <Select
                  selectedOption={promptData.industryOption}
                  onChange={({ detail: { selectedOption: industryOption } }) =>
                    setPromptData((prev) => ({ ...prev, industryOption }))
                  }
                  options={OPTIONS}
                  placeholder="Please select an industry"
                />
              </FormField>
              <FormField label="Prompt Name" stretch>
                <Input
                  placeholder="Please enter a prompt topic"
                  onChange={({ detail: { value: topic_name } }) =>
                    setPromptData((prev) => ({ ...prev, topic_name }))
                  }
                  value={promptData.topic_name}
                />
              </FormField>
              <FormField label="System Prompt" stretch>
                <Textarea
                  placeholder="Please enter a system prompt"
                  value={promptData.system_prompt}
                  onChange={({ detail: { value: system_prompt } }) =>
                    setPromptData((prev) => ({ ...prev, system_prompt }))
                  }
                />
              </FormField>
              <FormField label="User Prompt" stretch>
                <Textarea
                  placeholder="Please enter a user prompt"
                  value={promptData.user_prompt}
                  onChange={({ detail: { value: user_prompt } }) =>
                    setPromptData((prev) => ({ ...prev, user_prompt }))
                  }
                />
              </FormField>
            </SpaceBetween>
          </Form>
        </form>
      </Container>
      <Container
        header={
          <Header
            actions={
              <Button
                loading={loadingListData}
                iconName="refresh"
                onClick={() => getListData()}
              />
            }
          >
            Prompt List
          </Header>
        }
      >
        <Table<IPromptDatum>
          {...collectionProps}
          stickyColumns={{ first: 0, last: 1 }}
          stripedRows
          wrapLines
          pagination={<Pagination {...paginationProps} />}
          variant="full-page"
          loading={loadingListData}
          items={items}
          loadingText="Loading prompt list"
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
              id: "industry_type",
              header: "Industry",
              sortingField: "industry_type",
              width: 80,
              cell: (item) => item.industry_type || "n/a",
            },
            {
              id: "topic_name",
              header: "Name",
              sortingField: "topic_name",
              width: 100,
              cell: (item) => item.topic_name || "n/a",
            },
            {
              id: "system_prompt",
              header: "System Prompt",
              cell: (item) => item.system_prompt || "n/a",
            },
            {
              id: "user_prompt",
              header: "User Prompt",
              cell: (item) => item.user_prompt || "n/a",
            },
            {
              id: "actions",
              header: "Action",
              cell: ({ prompt_id, topic_name, is_public }) => (
                <Button
                  variant="primary"
                  iconName="remove"
                  disabled={!!is_public}
                  loading={deletingPrompt}
                  onClick={async () => {
                    if (!prompt_id)
                      return toast.error(
                        `No prompt_id in this record: ${topic_name}`
                      );
                    const bool = confirm(
                      `Are you sure to delete this prompt: ${topic_name}?`
                    );
                    if (bool) {
                      const result = await delPrompt({
                        prompt_id,
                        user_id,
                      });
                      if (result?.message) toast.success(result.message);
                      getListData();
                    }
                  }}
                />
              ),
            },
          ]}
        />
      </Container>
    </SpaceBetween>
  );
};

export default PromptList;
