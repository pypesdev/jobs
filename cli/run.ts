import { error } from "console";
import { readConfig, writeConfig } from "./file-config";
import { execSync } from "child_process";
import { logger } from "./consts";
import { createInterface } from "readline";

const rl = createInterface({
  input: process.stdin,
  output: process.stdout,
});

const askQuestion = (question: string): Promise<string> => {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer);
    });
  });
};

export const runDefaultJobApplicationAgent = async () => {
  let config = await readConfig();

  if (!config.jobs) {
    config = { ...config, jobs: {} };
  }
  if (!config.jobs?.userName) {
    config.jobs!.userName = await askQuestion("Enter your linked-in email: \n");
  }
  if (!config.jobs?.password) {
    config.jobs!.password = await askQuestion(
      "Enter your linked-in password: \n"
    );
  }
  if (!config.jobs?.phoneNumber) {
    config.jobs!.phoneNumber = await askQuestion("Enter your phone number: \n");
  }
  await writeConfig(config);
};
