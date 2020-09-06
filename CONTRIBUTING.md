# Contributing

## Local development

Follow these instructions to start developing locally.

### Install prerequisites

- Install **virtualenv** using **pip** if you don't have it already.

```
pip install virtualenv
```

### Clone and setup virtual environment

- Fork the [repo](https://github.com/Suyash458/WiktionaryParser).
- Run the script below in bash to clone the repository and install the
required programs in your Python virtual environment, replacing
`YOUR_GITHUB_USERNAME` with your GitHub username.

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/WiktionaryParser && \
  cd WiktionaryParser && \
  virtualenv venv && \ 
  source ./venv/scripts/activate && \
  pip install -r requirements.txt && \
  pip install -e .

```

Remember to always run `source ./venv/scripts/activate` to activate your
virtual environment before coding.

### Optional instructions for Visual Studio Code users

If you're using Visual Studio Code, create a file at *.vscode/settings.json*
with the content below.

```json
{
    "python.pythonPath": "venv\\Scripts\\python.exe",
    "python.testing.unittestArgs": [
        "-v",
        "-s",
        "./tests",
        "-p",
        "*test*.py"
    ],
    "python.testing.pytestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.unittestEnabled": true
}
```

This will setup autocompletion and the test explorer.


## Running tests

To run all tests, run the following command.

```bash
python -m unittest discover tests
```
