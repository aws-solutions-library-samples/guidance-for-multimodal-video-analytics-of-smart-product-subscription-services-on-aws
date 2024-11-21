import {
  Button,
  Flex,
  Heading,
  PasswordField,
  TextField,
  useTheme,
} from "@aws-amplify/ui-react";
import { useState } from "react";
import { alertMsg } from "../../../common/helpers/tools";
import BaseLayout from "../BaseLayout";
import "./style.scss";

export default function CustomLogin() {
  const { tokens } = useTheme();

  const [userName, setUserName] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLogin, setIsLogin] = useState(false);

  const doLogin = async () => {
    console.log("login");
    setIsLoading(true);
    /*const reg =
      /^\w+((.\w+)|(-\w+))@[A-Za-z0-9]+((.|-)[A-Za-z0-9]+).[A-Za-z0-9]+$/;*/
    if (!userName) {
      alertMsg("Please enter your valid user name", "warning");
      setIsLoading(false);
      return;
    }
    if (!password) {
      alertMsg("Please enter your password", "warning");
      setIsLoading(false);
      return;
    }
    if (
      userName !== import.meta.env.VITE_DEFAULT_USER ||
      password !== import.meta.env.VITE_DEFAULT_PASSWORD
    ) {
      alertMsg("Username or password is error", "warning");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(false);
      setIsLogin(true);
    } catch (error) {
      alertMsg("Wrong user name or password", "error");
      setIsLoading(false);
    }
  };

  return (
    <div>
      {isLogin ? (
        <BaseLayout />
      ) : (
        <div className="login-page">
          <Flex
            as="form"
            direction="column"
            className="login-container"
            gap={tokens.space.medium}
          >
            <Heading level={3}>Login</Heading>
            <TextField
              label="Username"
              name="username"
              autoComplete="username"
              placeholder="your username"
              value={userName}
              onChange={(e) => {
                setUserName(e.target.value);
              }}
            />
            <PasswordField
              label="Password"
              name="password"
              placeholder="your password"
              isRequired={true}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
              }}
            />
            <Button
              variation="primary"
              isDisabled={userName === "" || password === ""}
              isLoading={isLoading}
              onClick={doLogin}
            >
              Login
            </Button>
          </Flex>
        </div>
      )}
    </div>
  );
}
