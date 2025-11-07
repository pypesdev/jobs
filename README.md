# How to Run the Job Application Bot

## Step 1: Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest version of Python for your operating system
3. Run the installer and make sure to check the box that says "Add Python to
   PATH" during installation
4. Restart your computer after installation

## Step 2: Install Required Packages

1. Open Terminal (Mac) or Command Prompt (Windows)
2. Navigate to the folder containing this project
3. Run the following command:
   ```
   pip install -r requirements.txt
   ```

## Step 3: Set Up Your OpenAI API Key

### On Mac/Linux:

1. Open Terminal
2. Run this command (replace `YOUR_API_KEY_HERE` with your actual API key):
   ```
   export OPENAI_API_KEY=YOUR_API_KEY_HERE
   ```
3. To make this permanent, add the same line to your `~/.zshrc` or
   `~/.bash_profile` file

### On Windows:

1. Open Command Prompt
2. Run this command (replace `YOUR_API_KEY_HERE` with your actual API key):
   ```
   setx OPENAI_API_KEY "YOUR_API_KEY_HERE"
   ```
3. Close and reopen Command Prompt for the change to take effect

## Step 4: Configure the Bot

1. Open the `config.yaml` file in a text editor
2. Fill in your LinkedIn email, password, and phone number
3. Add the job positions and locations you want to search for

## Step 5: Run the Bot

1. Open Terminal (Mac) or Command Prompt (Windows)
2. Navigate to the folder containing this project
3. Run the following command:
   ```
   python easyapplybot.py
   ```

The bot will start applying to jobs automatically based on your configuration!
