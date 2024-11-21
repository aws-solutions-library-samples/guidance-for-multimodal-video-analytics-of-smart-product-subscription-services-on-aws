import Hls from "hls.js";
import { useContext, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import "./style.scss";
import { DEFAULT_STREAM_NAME } from "../../../../aws-config";
import { CustomContext } from "../../../../common/helpers/context";

const ACTION = "get_kvs_streaming_url";

export function HLSPlayer() {
  const { search } = useLocation();
  const params = new URLSearchParams(search);
  const name = params.get("name");
  const { message, sendMessage } = useContext(CustomContext);

  const videoRef = useRef(null);
  const [videoURL, setVideoURL] = useState("");
  let hls;

  useEffect(() => {
    if (!sendMessage) return;
    sendMessage({
      action: ACTION,
      stream_name: name || DEFAULT_STREAM_NAME,
    });
  }, [sendMessage, name]);

  useEffect(() => {
    if (!message?.data) return;
    try {
      const data = JSON.parse(message.data);
      if (data.action === ACTION && data.statusCode === 200) {
        const streamingUrl = JSON.parse(data.body)?.streaming_url;
        if (streamingUrl) setVideoURL(streamingUrl);
      }
    } catch (error) {
      console.error({ error });
    }
  }, [message]);

  useEffect(() => {
    if (videoRef.current) {
      if (!hls) {
        hls = new Hls();
      }
      hls.loadSource(videoURL);
      hls.attachMedia(videoRef.current);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        console.log("Starting playback");
        videoRef.current.stop();
        videoRef.current.play();
      });
    }

    return () => {
      if (hls) {
        hls.destroy();
      }
    };
  }, [videoRef, videoURL]);

  return <video className="video" ref={videoRef} controls />;
}
