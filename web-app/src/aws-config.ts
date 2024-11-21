export const APP_TITLE = import.meta.env.VITE_TITLE;
export const APP_VERSION = import.meta.env.VITE_APP_VERSION;
export const APP_LOGO = import.meta.env.VITE_LOGO || "";

export const WEBSOCKET_URL = import.meta.env.VITE_WEBSOCKET_URL;
export const HTTP_URL = import.meta.env.VITE_HTTP_URL;

export const DEFAULT_STREAM_NAME = import.meta.env.VITE_DEFAULT_STREAM_NAME;

export const isLoginWithCognito = import.meta.env.VITE_LOGIN_TYPE === "Cognito";

export const useSSOLogin =
  import.meta.env.VITE_USE_SSO_LOGIN === "true" ? true : false;

console.info({
  VITE_LOGIN_TYPE: import.meta.env.VITE_LOGIN_TYPE,
  VITE_USE_SSO_LOGIN: import.meta.env.VITE_USE_SSO_LOGIN,
});

export const SSO_FED_AUTH_PROVIDER = import.meta.env.VITE_SSO_FED_AUTH_PROVIDER;

const extraConfigUseSSOLogin = useSSOLogin
  ? {
      mandatorySignIn: false,
      authenticationFlowType: "USER_SRP_AUTH",
      oauth: {
        domain: import.meta.env.VITE_SSO_OAUTH_DOMAIN,
        scope: ["email", "openid", "aws.cognito.signin.user.admin", "profile"],
        redirectSignIn: window.location.origin,
        redirectSignOut: window.location.origin,
        responseType: "code",
      },
    }
  : {};

export const awsConfig = {
  Auth: {
    region: import.meta.env.VITE_COGNITO_REGION,
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
    userPoolWebClientId: import.meta.env.VITE_COGNITO_USER_POOL_WEB_CLIENT_ID,
    ...extraConfigUseSSOLogin,
  },
  API: {
    endpoints: [
      {
        region: import.meta.env.VITE_COGNITO_REGION,
        name: "API",
        endpoint: import.meta.env.VITE_API_GATEWAY_ENDPOINT,
      },
    ],
  },
  Storage: {
    bucket1: {
      region: import.meta.env.VITE_COGNITO_REGION,
      bucket: import.meta.env.VITE_STORAGE_VIDEO_BUCKET,
    },
    bucket2: {
      region: import.meta.env.VITE_COGNITO_REGION,
      bucket: import.meta.env.VITE_STORAGE_INFORMATION_BUCKET,
    },
    customPrefix: {
      public: "",
      protected: "",
      private: "",
    },
  },
};
