# GMail API Script Usage Guide

This guide provides instructions on how to use the email processing script to fetch emails from a PostgreSQL database, apply rules defined in a JSON file, and take actions on those emails based on the rules.

## Prerequisites

Before using the email processing script, ensure you have the following prerequisites installed:

- Python 3.x
- PostgreSQL
- Required Python packages (install via `pip install -r requirements.txt`)

## Configuration

1. Ensure PostgreSQL is installed and running on your system.
2. Set up the Gmail API and obtain credentials for OAuth authentication. Place the credentials file (`client_secret.json`) in the same directory as the script.
3. Configure the PostgreSQL database connection details in the script (`gmail_api.py`) and (`fetch_mails.py`) under the `connect_to_postgresql` section.

## Usage

1. **Fetching Emails:**

    Run the script `gmail_api.py` to fetch emails from using the GMail API and store the retrived emails in the PostgreSQL database.

    ```bash
    python gmail_api.py
    ```

    This script will connect to the GMail API using OAuth, fetch emails, and store them locally in the PostgreSQL database.

2. **Processing Emails:**

    After fetching emails, run the script `retrieve_mails.py` to apply rules defined in a JSON file and take actions on the emails.

    ```bash
    python retrieve_mails.py
    ```

    Replace `rules.json` with the path to your JSON file containing the rules.

## Rule Definition

The rules for processing emails are defined in a JSON file. Each rule consists of conditions and actions:

- **Conditions:** Specify criteria based on email attributes such as sender, subject, or received date.
- **Actions:** Define actions to be taken on emails that meet the conditions, such as marking as read, moving to a folder, etc.

Here's an example of a rule in the JSON format:

```json
{
  "conditions": [
    {"field": "sender", "predicate": "contains", "value": "example.com"},
    {"field": "received_at", "predicate": "greater_than", "value": "2023-01-01"}
  ],
  "predicate": "All",
  "actions": [
    {"action": "mark_as_read"},
    {"action": "move_message", "destination_folder": "Processed"}
  ]
}
```

## Common Gmail Labels (Accepted Values)

When specifying a destination folder for actions like moving messages, you can use the following commonly accepted values:

CHAT, SENT, INBOX, IMPORTANT, TRASH, DRAFT, SPAM, CATEGORY_FORUMS, CATEGORY_UPDATES, CATEGORY_PERSONAL, CATEGORY_PROMOTIONS, CATEGORY_SOCIAL, STARRED, UNREAD, Personal, Receipts, Work, Junk, Documents, Unwanted
