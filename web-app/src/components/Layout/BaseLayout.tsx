import { AppLayout, BreadcrumbGroup } from "@cloudscape-design/components";
import { Auth } from "aws-amplify";
import { useEffect, useState } from "react";
import { Toaster } from "react-hot-toast";
import { useDispatch } from "react-redux";
import { Outlet, UIMatch, useMatches, useNavigate } from "react-router-dom";
import useWebSocket from "react-use-websocket";
import { isLoginWithCognito, WEBSOCKET_URL } from "../../aws-config";
import { CustomContext } from "../../common/helpers/context";
import { ActionType, UserInfo } from "../../common/helpers/store";
import { useNavigationPanelState } from "../../common/hooks/use-navigation-panel-state";
import NavSide from "../NavSide";
import CustomTopNavigation from "../NavTop";

type ICrumbItems = Readonly<{ text: string; href: string }[]>;

const BaseLayout: React.FC = () => {
  const [sideNavOpen, setSideNavOpen] = useNavigationPanelState();
  const navigate = useNavigate();
  const matches = useMatches();
  const [crumbs] = (
    matches as UIMatch<unknown, { crumb: () => ICrumbItems[] }>[]
  )
    .filter((match) => Boolean(match.handle?.crumb))
    .map((match) => match.handle.crumb());

  const dispatch = useDispatch();
  useEffect(() => {
    if (isLoginWithCognito) {
      (async () => {
        const user = await Auth.currentUserInfo();
        console.log({ user });
        const loginUser: UserInfo = {
          userId: user?.attributes?.sub || "",
          displayName:
            user?.attributes?.displayName ||
            user?.attributes?.email ||
            findUserId(user) ||
            user?.username ||
            "",
          loginExpiration: 0,
          isLogin: true,
        };
        dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
      })();
    } else {
      const loginUser: UserInfo = {
        userId: import.meta.env.VITE_DEFAULT_USER || "",
        displayName: import.meta.env.VITE_DEFAULT_USER || "",
        loginExpiration: +new Date() + 18000000,
        isLogin: true,
      };
      dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
    }
  }, [dispatch]);

  const [message, setMessage] = useState<MessageEvent<any>>();
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const { sendJsonMessage: sendMessage } = useWebSocket(WEBSOCKET_URL, {
    onOpen: (openMessage) => {
      console.log("websocket connection opened, ", openMessage),
        setIsConnected(true);
    },
    onMessage: (event) => {
      setMessage(event);
    },
    onClose: (closeMessage) =>
      console.error("websocket connection closed, ", closeMessage),
    onError: (errorMessage) =>
      console.error("websocket connection error, ", errorMessage),
    shouldReconnect: () => true,
    reconnectAttempts: 10,
  });

  return (
    <CustomContext.Provider
      value={{ sendMessage, message, isConnected, setMessage, setSideNavOpen }}
    >
      <Toaster />
      <CustomTopNavigation />
      <AppLayout
        headerSelector="#awsui-top-navigation"
        navigationOpen={!sideNavOpen.collapsed}
        onNavigationChange={({ detail }) =>
          setSideNavOpen({ collapsed: !detail.open })
        }
        breadcrumbs={
          crumbs?.length ? (
            <BreadcrumbGroup
              items={[{ text: "Home", href: "/" }, ...crumbs] as any}
              onFollow={(e) => {
                e.preventDefault();
                navigate(e.detail.href);
              }}
            />
          ) : undefined
        }
        toolsHide={true}
        navigation={<NavSide />}
        content={<Outlet />}
      />
    </CustomContext.Provider>
  );
};

export default BaseLayout;

function findUserId(user?: any) {
  const pattern = /"userId"\s*:\s*"(\w+)"/;
  const match = user?.attributes?.identities?.match(pattern);
  if (!match) return console.log("fn: findUserId log - userId not found");
  const userId = match[1];
  console.log(`fn: findUserId log - userId: ${userId}`);
  return `UserID - ${userId}`;
}
