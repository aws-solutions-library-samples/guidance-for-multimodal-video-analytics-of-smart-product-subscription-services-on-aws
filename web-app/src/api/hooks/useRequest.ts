import { useCallback, useState } from "react";
import toast from "react-hot-toast";
import { RequestOptionsInit, ResponseError } from "umi-request";
import request from "../request";

type IRestfulResponse<R> = {
  data?: R;
  message?: string;
};
type IUseRequestOptions<R, T> = {
  method: "GET" | "POST" | "PUT" | "DELETE";
  onSuccess?: (params: {
    data: R | undefined;
    message?: string;
    setData: React.Dispatch<React.SetStateAction<R | undefined>>;
  }) => void;
  onError?: (error: any) => void;
  params?: T;
};

const defaultErrorHander = (
  error: ResponseError,
  path: string,
  method: string
) => {
  const str = `[useRequest error] on url path: ${path}, method: ${method} `;
  toast.error(str);
  console.error(str, JSON.stringify(error));
};
/**
 * @R response data type
 * @T request data type
 */
const useRequest = <R = any, T extends object | undefined = undefined>(
  path: string,
  { method, onSuccess, onError, params }: IUseRequestOptions<R, T>,
  initValue?: R
) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<R | undefined>(initValue);
  const [message, setMessage] = useState("");
  const run = useCallback(
    async (args?: T) => {
      setLoading(true);
      const errorHandler = onError
        ? onError
        : (error: ResponseError) => defaultErrorHander(error, path, method);
      const extra = method === "GET" ? { params } : { data: args };
      const options: RequestOptionsInit = { method, errorHandler, ...extra };
      const result = await request<IRestfulResponse<R>>(path, options);
      if (result?.data) setData(result.data);
      if (result?.message) setMessage(result.message || "");
      onSuccess?.({ data: result?.data, message: result?.message, setData });
      setLoading(false);
      return result;
    },
    [method, onError, onSuccess, path, params]
  );

  return { loading, setLoading, data, setData, run, message };
};

export default useRequest;
