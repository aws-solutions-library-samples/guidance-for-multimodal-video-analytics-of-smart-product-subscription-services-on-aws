import React, { useEffect, useState } from "react";
import { CHATBOT_NAME } from "../common/constant/constants";
import { SideNavigation } from "@cloudscape-design/components";
import { useLocation, useNavigate } from "react-router-dom";

const NavSide: React.FC = () => {
  const location = useLocation();
  const [activeHref, setActiveHref] = useState(location.pathname);

  useEffect(() => {
    setActiveHref(location.pathname === "/" ? "/s3" : location.pathname);
  }, [location.pathname]);

  const navigate = useNavigate();
  return (
    <SideNavigation
      header={{ href: "/", text: CHATBOT_NAME }}
      activeHref={activeHref}
      onFollow={(event) => {
        if (!event.detail.external) {
          event.preventDefault();
          navigate(event.detail.href);
        }
      }}
      items={[
        { type: "link", text: "S3 Streams", href: "/s3" },
        { type: "link", text: "KVS Streams", href: "/kvs" },
        { type: "divider" },
        {
          type: "link",
          text: "Prompt Management",
          href: "/prompt",
          // info: <Badge color="red">23</Badge>,
        },
        { type: "divider" },
        {
          type: "link",
          text: "Workshop",
          href: "https://example.com",
          external: true,
        },
      ]}
    />
  );
};

export default NavSide;
