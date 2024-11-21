import { extend } from "umi-request";
import { HTTP_URL } from "../aws-config";

const request = extend({
  prefix: HTTP_URL,
  timeout: 30 * 1000,
  headers: { "Content-Type": "application/json" },
});

export default request;

// request.interceptors.request.use((url, options) => {
//   if (!isLoginWithCognito) return { url, options };
//   const headers = { ...getBearerTokenObj(), ...options.headers };
//   return { url, options: { ...options, headers } };
// });

// request.interceptors.response.use((response) => {
//   if (response.status === 500) toast.error("Internal Server Error");
//   if (!isLoginWithCognito) return response;
//   if (response.status === 401) logout();
//   return response;
// });
