import {
  Authenticator,
  Button,
  Divider,
  Heading,
  Image,
  useTheme,
  View,
} from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { Amplify, Auth } from "aws-amplify";
import { useEffect, useState } from "react";
import {
  APP_LOGO,
  APP_TITLE,
  APP_VERSION,
  awsConfig,
  SSO_FED_AUTH_PROVIDER,
  useSSOLogin,
} from "../../aws-config";
import BaseLayout from "./BaseLayout";
import "./layout-with-cognito.css";

const THE_SWITCH = true;

export default function LayoutWithCognito() {
  useEffect(() => {
    try {
      Amplify.configure(awsConfig);
    } catch (e) {
      console.error(e);
    }
  }, []);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <Authenticator
      hideSignUp={useSSOLogin}
      components={
        !useSSOLogin
          ? {
              Header() {
                const { tokens } = useTheme();
                return THE_SWITCH ? (
                  <AuthTitle />
                ) : (
                  <View textAlign="center" padding={tokens.space.xxl}>
                    {APP_LOGO ? (
                      <Image
                        alt="App logo"
                        src={APP_LOGO}
                        // src="https://docs.amplify.aws/assets/logo-dark.svg"
                      />
                    ) : (
                      <Heading padding={tokens.space.small} level={4}>
                        {APP_TITLE}
                      </Heading>
                    )}
                  </View>
                );
              },
            }
          : {
              Header: AuthTitle,
              SignIn: {
                Header() {
                  return (
                    <View
                      padding="0.3rem 2rem"
                      style={{ borderTop: "2px solid black" }}
                    >
                      <Heading
                        fontSize="20px"
                        padding="1rem 0"
                        fontWeight={400}
                        textAlign="center"
                      >
                        Please Sign In
                      </Heading>
                      <Button
                        colorTheme="overlay"
                        // variation="primary"
                        loadingText="Signing in..."
                        isLoading={isLoading}
                        disabled={isLoading}
                        width="100%"
                        onClick={async () => {
                          try {
                            setIsLoading(true);
                            await Auth.federatedSignIn({
                              customProvider: SSO_FED_AUTH_PROVIDER,
                            });
                          } catch (error) {
                            console.error(error);
                          }
                        }}
                      >
                        Click to sign in with SSO
                      </Button>
                      <Divider
                        orientation="horizontal"
                        label="or"
                        margin="2rem 0 0 0"
                      />
                    </View>
                  );
                },
              },
            }
      }
      signUpAttributes={["email"]}
    >
      <WrapperBaseLayout />
    </Authenticator>
  );
}

function WrapperBaseLayout() {
  // const auth = useAuthenticator();
  return <BaseLayout />;
}

function AuthTitle() {
  const { tokens } = useTheme();
  return (
    <View
      textAlign="center"
      margin={`${tokens.space.xxl} auto ${tokens.space.large} auto`}
      position="relative"
    >
      <View>
        <View padding={tokens.space.small}>
          <Heading fontWeight="400" level={3}>
            Multi-modal Vision Analytics
          </Heading>
          {APP_VERSION && <Heading fontWeight="200">{APP_VERSION}</Heading>}
        </View>
        <Heading fontWeight="200">Guidance on Amazon Web Services</Heading>
        <Image
          width="50px"
          alt="Amazon Web Services Logo"
          src="/smile-logo.png"
        />
      </View>
    </View>
  );
}
