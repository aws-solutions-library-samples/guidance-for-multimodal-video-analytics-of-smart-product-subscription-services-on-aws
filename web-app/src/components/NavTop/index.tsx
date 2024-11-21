import {
  ButtonDropdownProps,
  TopNavigation,
} from "@cloudscape-design/components";
import { Mode } from "@cloudscape-design/global-styles";
import { Auth } from "aws-amplify";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { APP_LOGO, APP_TITLE, isLoginWithCognito } from "../../aws-config";
import { CHATBOT_NAME } from "../../common/constant/constants";
import { Storage } from "../../common/helpers/storage";
import { ActionType, UserInfo, UserState } from "../../common/helpers/store";
import "./style.scss";

export default function NavTop() {
  const [theme, setTheme] = useState<Mode>(Storage.getTheme());

  const userInfo = useSelector((state: UserState) => state.userInfo);
  const dispatch = useDispatch();

  const onChangeThemeClick = () => {
    if (theme === Mode.Dark) {
      setTheme(Storage.applyTheme(Mode.Light));
    } else {
      setTheme(Storage.applyTheme(Mode.Dark));
    }
  };
  const onUserProfileClick = ({
    detail,
  }: {
    detail: ButtonDropdownProps.ItemClickDetails;
  }) => {
    if (detail.id === "signout") {
      if (isLoginWithCognito) {
        Auth.signOut().then();
      } else {
        const user: UserInfo = { ...userInfo, isLogin: false };
        dispatch({ type: ActionType.UpdateUserInfo, state: user });
      }
    }
  };

  return (
    <TopNavigation
      identity={{
        href: "/",
        title: APP_TITLE,
        logo: APP_LOGO
          ? {
              src: APP_LOGO,
              alt: { CHATBOT_NAME } + " Logo",
            }
          : undefined,
      }}
      utilities={[
        {
          type: "button",
          text: theme === Mode.Dark ? "Light Mode" : "Dark Mode",
          onClick: onChangeThemeClick,
        },
        {
          type: "menu-dropdown",
          text: userInfo?.displayName || "Authenticating",
          iconName: "user-profile",
          onItemClick: onUserProfileClick,
          items: [
            {
              id: "signout",
              text: "Sign out",
            },
          ],
        },
      ]}
    />
  );
}
