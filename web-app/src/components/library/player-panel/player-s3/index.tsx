import { useContext, useEffect, useRef, useState } from "react";
import "./style.scss";
import { CustomContext } from "../../../../common/helpers/context";
import toast from "react-hot-toast";

const ACTION = "get_s3_video_url";

export function S3Player({ name }: { name: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoURL, setVideoURL] = useState("");

  const { message, sendMessage } = useContext(CustomContext);

  useEffect(() => {
    if (!sendMessage) return;
    sendMessage({ action: ACTION, video_object_key: name });
  }, [sendMessage, name]);

  useEffect(() => {
    if (!message?.data) return;
    try {
      const data = JSON.parse(message.data);
      if (data.action === ACTION && data.statusCode === 200 && data.body) {
        const s3VideoUrl = JSON.parse(data.body.toString())?.s3_video_url;
        if (s3VideoUrl) setVideoURL(s3VideoUrl);
      }
    } catch (error) {
      toast.error(JSON.stringify(error));
      console.error(`Error on parsing data: `, error);
    }
  }, [message]);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
    }
  }, [videoURL]);

  return (
    <video className="video" ref={videoRef} controls autoPlay muted>
      <source src={videoURL} type="video/mp4" />
    </video>
  );
}
