import { ZodSchema } from "zod";

export interface ResponseLike {
  object?: any;
  text?: string;
}

export function parseResponse(response: ResponseLike, schema?: ZodSchema) {
  if (response.object) {
    return schema ? schema.parse(response.object) : response.object;
  } else if (response.text) {
    return schema ? schema.parse(JSON.parse(response.text)) : response.text;
  } else {
    throw new Error("No response object or text", { cause: response });
  }
}
