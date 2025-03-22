# StudyPal

An app to create flashcards, or make them for you.

## Setup

### Create a Virtual Environment

To create a virtual environment, run the following command:

```bash
python -m venv venv
```

### Activate the Virtual Environment

Activate the virtual environment using the following command:

- On Windows:

```bash
venv\Scripts\activate
```

- On macOS and Linux:

```bash
source venv/bin/activate
```

### Install Dependencies

Once the virtual environment is activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Update Environment Variables

Before running the application, make sure to update the environment variables in the `.env` file:

```dotenv
TOGETHER_API_KEY=your_together_key (optional)
JWT_SECRET_KEY=your_jwt_secret_key
SECRET_KEY=your_secret_key
JWT_EXPIRES_IN=expiration_time (3365)
GITHUB_TOKEN=your_github_token
```

Replace the placeholder values with your actual credentials and settings.

#### Getting a GitHub API Key

1. Go to [GitHub Developer Settings](https://github.com/settings/tokens).
2. Click on "Generate new token".
3. Select the scopes needed for your application.
4. Click on "Generate token".
5. Copy the generated token and update the `GITHUB_API_KEY` in your `.env` file.

For more information on GitHub tokens, visit the [GitHub Marketplace Models](https://github.com/marketplace/models).

### Run the Application

To run the application, use the following command:

```bash
python app.py
```

## Requirements

Here is the list of dependencies required for this project. These are included in the `requirements.txt` file:

- Flask
- Flask-SQLAlchemy
- werkzeug
- flask-jwt-extended
- python-dotenv
- Flask-Cors
- pyjwt
- together
- Azure AI Inference


## Useful Links

- [GitHub](https://github.com)