# Freshdesk to SharePoint Migration Tool

This tool retrieves tickets and attachments from Freshdesk and uploads them to SharePoint, with each ticket having its own folder.

## Requirements

- Python 3.10 or higher
- Freshdesk API key
- SharePoint credentials (username and password)

## Installation

1. Clone this repository or download the files
2. Create a virtual environment and activate it:
```
python3 -m venv venv
source venv/bin/activate
```
3. Install the required packages:
```
pip install requests python-freshdesk Office365-REST-Python-Client
```

## Components

The solution consists of several Python scripts:

- `freshdesk_client.py`: Client for interacting with the Freshdesk API
- `sharepoint_client.py`: Client for interacting with SharePoint
- `retrieve_tickets.py`: Script to retrieve all tickets from Freshdesk
- `download_attachments.py`: Script to download attachments for all tickets
- `upload_to_sharepoint.py`: Script to upload tickets and attachments to SharePoint
- `freshdesk_to_sharepoint.py`: Main script that orchestrates the entire process

## Usage

### Running the Complete Process

To run the complete process (retrieve tickets, download attachments, upload to SharePoint), use the main script:

```
python freshdesk_to_sharepoint.py \
  --freshdesk-domain your-domain.freshdesk.com \
  --freshdesk-api-key your-api-key \
  --sharepoint-url https://yourcompany.sharepoint.com/sites/yoursite \
  --sharepoint-username your.email@yourcompany.com \
  --sharepoint-password your-password \
  --sharepoint-folder FreshdeskTickets \
  --data-dir ./data
```

### Running Individual Steps

You can also run each step individually:

1. Retrieve tickets:
```
python retrieve_tickets.py \
  --domain your-domain.freshdesk.com \
  --api-key your-api-key \
  --output-dir ./data/tickets
```

2. Download attachments:
```
python download_attachments.py \
  --domain your-domain.freshdesk.com \
  --api-key your-api-key \
  --tickets-file ./data/tickets/tickets_YYYYMMDD_HHMMSS.json \
  --output-dir ./data/attachments
```

3. Upload to SharePoint:
```
python upload_to_sharepoint.py \
  --site-url https://yourcompany.sharepoint.com/sites/yoursite \
  --username your.email@yourcompany.com \
  --password your-password \
  --tickets-dir ./data/tickets \
  --attachments-dir ./data/attachments \
  --sharepoint-folder FreshdeskTickets
```

## Output

The tool creates the following output:

- `./data/tickets/`: JSON files containing ticket data
- `./data/attachments/`: Downloaded attachments organized by ticket ID
- `./data/migration_summary.json`: Summary of the migration in JSON format
- `./data/migration_report.txt`: Detailed report of the migration in text format
- `freshdesk_to_sharepoint.log`: Log file with detailed information about the process

## SharePoint Structure

In SharePoint, the tickets and attachments are organized as follows:

```
FreshdeskTickets/
  ├── Ticket_123/
  │   ├── ticket_123_metadata.json
  │   ├── attachment1.pdf
  │   └── attachment2.jpg
  ├── Ticket_456/
  │   ├── ticket_456_metadata.json
  │   └── attachment3.docx
  └── ...
```

Each ticket has its own folder containing the ticket metadata and all attachments.

## Security Considerations

- The script requires your SharePoint credentials. Consider using environment variables or a secure credential store instead of passing them as command-line arguments.
- API keys and passwords are sensitive information. Ensure they are kept secure and not committed to version control.

## Troubleshooting

- If you encounter authentication issues with SharePoint, verify your credentials and ensure your account has sufficient permissions.
- For Freshdesk API issues, check that your API key is correct and has the necessary permissions.
- Check the log file for detailed error messages.
