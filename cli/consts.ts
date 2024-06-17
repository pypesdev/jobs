import { execSync } from "child_process";
import gradient from "gradient-string";
import * as winston from "winston";

const poimandresTheme = {
  blue: "#add7ff",
  cyan: "#89ddff",
  green: "#5de4c7",
  magenta: "#fae4fc",
  red: "#d0679d",
  yellow: "#fffac2",
};

export const TITLE_TEXT = `
--------------------------------
______                        
(_____ \                       
_____) )   _ ____  _____  ___ 
|  ____/ | | |  _ \| ___ |/___)
| |    | |_| | |_| | ____|___ |
|_|     \__  |  __/|_____|___/ 
      (____/|_|               

--------------------------------
`;

export const renderTitle = () => {
  const pypesGradient = gradient(Object.values(poimandresTheme));
  console.log(pypesGradient.multiline(TITLE_TEXT));
};

/**
 * Highlight a string (in either purple, orange, or blue)
 */
type Color = "purple" | "orange" | "blue";
const colorCodes: Record<Color, string> = {
  purple: "\x1b[35m",
  orange: "\x1b[33m", // ANSI code for orange (yellow)
  blue: "\x1b[34m",
};
export const highlight = (str: string, color: Color = "purple") => {
  const colorCode = colorCodes[color] || colorCodes.purple;
  return `${colorCode}${str}\x1b[0m`;
};

/**
 * Logs a command and runs it
 */
export const runCommand = (cmd: string, options = {}) => {
  logger.debug(`Running ${highlight(cmd)}...`);
  return (execSync(cmd, options) ?? "").toString().trim();
};

/**
 * Calculate the difference in Minutes and Seconds
 * @returns A string of Minutes and Seconds
 */
export const calculateMinSec = (start: Date, end: Date) => {
  const numSec = Math.round((end.getTime() - start.getTime()) / 1000);
  let numMin = 0;
  let retString = "";

  if (numSec > 60) {
    numMin = Math.floor(numSec / 60);
    retString = `${numMin} Minutes and ${numSec % 60} Seconds`;
  } else {
    retString = `${numSec} seconds`;
  }

  return retString;
};

/**
 * Setup winston
 * Individual commands are logged at the debug level, to see them set LOG_LEVEL, i.e.
 * LOG_LEVEL=debug node tools/util.js invite
 */
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || "info",
  format: winston.format.combine(winston.format.splat(), winston.format.cli()),
  transports: [
    new winston.transports.Console({
      silent: process.env.NODE_ENV === "test",
    }),
  ],
});
