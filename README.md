## AI-Powered LinkedIn Job Application Bot (Python)

This repository contains an AI-powered Python bot that automates your job applications on LinkedIn, specifically targeting the "Easy Apply" feature.

**Features:**

- Leverages AI to tailor application responses to each job description.
- Customizable job search criteria based on keywords and filters.
- Securely stores your LinkedIn login credentials for easy use.

**Requirements:**

- Python 3.x (Download from [https://www.python.org/downloads/](https://www.python.org/downloads/))
- Required Libraries (listed in `requirements.txt`)

**Installation:**

1. Clone this repository.
2. Open a terminal in the project directory.
3. Install the required libraries: `pip install -r requirements.txt`

**Configuration:**

1. Edit the `config.yaml` file to provide your LinkedIn login credentials and desired job search filters (keywords, locations, etc.).

**Running the Bot:**

1. Execute the bot script using `python easyapplybot.py`

**Note:**

- This bot does not currently support uploading resumes or cover letters directly.
- It focuses on filling out forms within the "Easy Apply" system.
- Use this tool responsibly and ethically. Ensure your resume and experience align with the applied positions.

**Disclaimer:**

This bot is provided for educational purposes only. The authors are not responsible for any misuse or consequences of using this tool. LinkedIn terms of service should be respected while using this bot.

The run the bot install requirements

```bash
pip3 install -r requirements.txt
```

Enter your username, password, and search settings into the `config.yaml` file

```yaml
username: # Insert your username here
password: # Insert your password here

positions:
  -  # positions you want to search for
  -  # Another position you want to search for
  -  # A third position you want to search for

locations:
  -  # Location you want to search for
  -  # A second location you want to search in

uploads:
  Resume: # PATH TO Resume
  Cover Letter: # PATH TO cover letter
  Photo: # PATH TO photo
# Note file_key:file_paths contained inside the uploads section should be writted without a dash ('-')

output_filename:
  -  # PATH TO OUTPUT FILE (default output.csv)

blacklist:
  -  # Company names you want to ignore
```

**NOTE: AFTER EDITING SAVE FILE, DO NOT COMMIT FILE**

### Uploads

There is no limit to the number of files you can list in the uploads section.
The program takes the titles from the input boxes and tries to match them with
list in the config file.

## Execute

To execute the bot run the following in your terminal

```
python3 easyapplybot.py
```

## Docker

Start selenium grid with

```bash
docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" selenium/standalone-chrome:latest
```

Then enqueue the task to the remote driver with:

```python
options = Options()
driver = webdriver.Remote(command_executor='http://localhost:4444', options=options)
```

# TODO:
- [ ] fix fill_invalids select option
- [ ] don't select yes to requiring a visa