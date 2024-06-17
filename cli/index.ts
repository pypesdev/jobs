#!/usr/bin/env node
import { Command } from "commander";
import { renderTitle } from "./consts";
import { runDefaultJobApplicationAgent } from "./run";

export const runCli = async (argv = process.argv) => {
  renderTitle();

  const program = new Command()
    .name("jobs")
    .description("A CLI for managing your job application agent")
    .version("1.0.0")
    .on("command:*", function () {
      program.outputHelp();
      process.exit(1);
    });

  const jobTask = new Command("jobs").description(
    "A subcommand to interact with your job applications"
  );

  jobTask
    .command("ls")
    .description("list tasks by name and id")
    .action(() => {
      console.log("~listing job applications");
    });

  program.addCommand(jobTask);
  program.parse(argv);
};
if (process.argv[2]) {
  runCli().catch((err) => {
    console.log("err", err);
  });
} else {
  runDefaultJobApplicationAgent().catch((err) => {
    console.log("err", err);
  });
}
