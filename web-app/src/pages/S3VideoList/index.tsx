import { SpaceBetween } from "@cloudscape-design/components";
import DeleteResource from "./DeleteResource";
import S3VideoTable from "./S3VideoTable";
import S3VideoUploader from "./S3VideoUploader";
import { useContext, useEffect } from "react";
import { CustomContext } from "../../common/helpers/context";

export default function S3VideoList() {
  const { setSideNavOpen } = useContext(CustomContext);

  useEffect(() => {
    setSideNavOpen({ collapsed: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <SpaceBetween size="l">
      <S3VideoTable />
      <S3VideoUploader />
      <DeleteResource />
    </SpaceBetween>
  );
}
