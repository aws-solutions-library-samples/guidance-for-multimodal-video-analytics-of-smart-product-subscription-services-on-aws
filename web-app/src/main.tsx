import { defaultDarkModeOverride, ThemeProvider } from "@aws-amplify/ui-react";
import { Mode } from "@cloudscape-design/global-styles";
import "@cloudscape-design/global-styles/index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "regenerator-runtime/runtime";
import { isLoginWithCognito } from "./aws-config";
import { Storage } from "./common/helpers/storage";
import userReduxStore from "./common/helpers/store";
import ErrorPage from "./components/ErrorPage";
import Layout from "./components/Layout";
import KVSVideo from "./pages/KVSVideo";
import PromptList from "./pages/PromptList";
import S3VideoList from "./pages/S3VideoList";
import { VisionAnalyticsPage } from "./pages/VisionAnalyticsPage";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const theme = Storage.getTheme();
Storage.applyTheme(theme);

const router = createBrowserRouter([
  {
    path: "/",
    element: isLoginWithCognito ? (
      <Layout.AuthWithCognito />
    ) : (
      <Layout.CustomizedAuth />
    ),
    errorElement: <ErrorPage />,
    children: [
      { path: "/login", element: <div>Login Page</div> },
      {
        index: true,
        element: <S3VideoList />,
        handle: {
          crumb: () => [{ text: "Video streams (S3)", href: "/s3" }],
        },
      },
      {
        path: "/s3",
        element: <S3VideoList />,
        handle: {
          crumb: () => [{ text: "Video streams (S3)", href: "/s3" }],
        },
      },
      {
        path: "/kvs",
        element: <KVSVideo />,
        handle: {
          crumb: () => [{ text: "Video streams (KVS)", href: "/kvs" }],
        },
      },
      {
        path: "/prompt",
        element: <PromptList />,
        handle: {
          crumb: () => [{ text: "Prompt Management", href: "/prompt" }],
        },
      },
      {
        path: "/s3/video-play-analytics",
        element: <VisionAnalyticsPage />,
        handle: {
          crumb: () => [
            { text: `Video streams (s3)`, href: `/s3` },
            { text: "Vision Analytics", href: "" },
          ],
        },
      },
      {
        path: "/kvs/video-play-analytics",
        element: <VisionAnalyticsPage />,
        handle: {
          crumb: () => [
            { text: `Video streams (kvs)`, href: `/kvs` },
            { text: "Vision Analytics", href: "" },
          ],
        },
      },
      { path: "*", element: <h4>404! Page Not Found...</h4> },
    ],
  },
]);

root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      <ThemeProvider
        theme={{
          name: "default-theme",
          overrides: [defaultDarkModeOverride],
        }}
        colorMode={theme === Mode.Dark ? "dark" : "light"}
      >
        <RouterProvider router={router} fallbackElement={<p>Loading</p>} />
      </ThemeProvider>
    </Provider>
  </React.StrictMode>
);
