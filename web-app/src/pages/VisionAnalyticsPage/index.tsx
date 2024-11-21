import { useContext, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { CustomContext } from "../../common/helpers/context";
import ContentVisionAnalytics from "./ContentVisionAnalytics";
import "./style.scss";

export function VisionAnalyticsPage() {
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type");
  const name = searchParams.get("name");
  const { setSideNavOpen } = useContext(CustomContext);

  useEffect(() => {
    setSideNavOpen({ collapsed: true });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return type && name ? (
    <ContentVisionAnalytics type={type} name={name} />
  ) : (
    <h3>Error 404: No Type or Name in url search params</h3>
  );
}
