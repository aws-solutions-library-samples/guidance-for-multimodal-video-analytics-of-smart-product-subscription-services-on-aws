import {
  Button,
  Container,
  FileUpload,
  FormField,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useContext, useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { awsConfig } from "../../aws-config";
import { CustomContext } from "../../common/helpers/context";
import { UserState } from "../../common/helpers/store";

const ACTION = "get_s3_presigned_url";
const S3VideoUploader = () => {
  const [value, setValue] = useState<File[]>([]);

  const { message, sendMessage } = useContext(CustomContext);
  const userId = useSelector((state: UserState) => state.userInfo.userId);
  const navigate = useNavigate();

  useEffect(() => {
    if (message?.data) {
      const data = JSON.parse(message.data);
      try {
        if (data.statusCode === 200 && data.action === ACTION) {
          const preSignedUrl = JSON.parse(data.body)?.s3_presigned_url;
          if (preSignedUrl && value.length > 0) {
            fetch(preSignedUrl, {
              headers: { "Content-Type": "video/mp4" },
              method: "PUT",
              body: value[0],
            })
              .then(() => {
                setValue([]);
                const link = `/s3/video-play-analytics?type=s3&name=${userId}/${value[0].name}`;
                navigate(link);
              })
              .catch((error) => {
                console.error(error);
              });
          }
        }
      } catch (error) {
        console.error(
          `Error in receiving action ${ACTION}: `,
          JSON.stringify(error)
        );
      }
    }
  }, [message, navigate, userId, value]);

  return (
    <Container
      header={<Header variant="h2">Drag video here or Choose file</Header>}
    >
      <FormField>
        <SpaceBetween size={"m"} direction="vertical">
          <FileUpload
            onChange={({ detail }) => {
              setValue(detail.value);
              // upload file to s3
              if (detail.value) {
                const file = detail.value[0];
                if (!file || file.size === 0) {
                  return;
                }
                sendMessage?.({
                  action: ACTION,
                  from_path: file.name,
                  to_path: userId,
                  bucket: awsConfig.Storage.bucket1.bucket,
                });
              }
            }}
            value={value}
            accept={"video/mp4"}
            i18nStrings={{
              uploadButtonText: (e) => (e ? "Choose files" : "Choose file"),
              dropzoneText: (e) =>
                e ? "Drop files to upload" : "Drop file to upload",
              removeFileAriaLabel: (e) => `Remove file ${e + 1}`,
              limitShowFewer: "Show fewer files",
              limitShowMore: "Show more files",
              errorIconAriaLabel: "Error",
            }}
            showFileLastModified
            showFileSize
            showFileThumbnail
            tokenLimit={3}
            constraintText="The file must be .MP4 (Max file size: 1 GB)"
          />
          {value.length > 0 ? (
            <Button disabled loading variant="link">
              File uploading
            </Button>
          ) : null}
        </SpaceBetween>
      </FormField>
    </Container>
  );
};

export default S3VideoUploader;
