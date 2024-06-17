import { promises as fs } from "fs";
import os from "os";
import path from "path";

const CONFIG_FILE = ".pypesconfig.json";

export type Config = {
  jobs?: {
    userName?: string;
    password?: string;
    phoneNumber?: string;
  };
};

export const getConfigFilePath = () => {
  const homeDirectory = os.homedir();
  return path.join(homeDirectory, CONFIG_FILE);
};

export const readConfig = async (): Promise<Config> => {
  try {
    const filePath = getConfigFilePath();
    const data = await fs.readFile(filePath, "utf8");
    return JSON.parse(data);
  } catch (error) {
    if (isNodeJSError(error) && error.code === "ENOENT") {
      return {};
    } else {
      throw error;
    }
  }
};

export const writeConfig = async (update: Config) => {
  const filePath = getConfigFilePath();
  const currentConfig = await readConfig();
  const newConfig = { ...currentConfig, ...update };
  await fs.writeFile(filePath, JSON.stringify(newConfig, null, 2), "utf8");
};

export const isNodeJSError = (
  error: unknown
): error is NodeJS.ErrnoException => {
  return error instanceof Error;
};
