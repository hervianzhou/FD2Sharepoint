#!/usr/bin/env python3
"""
Script to download attachments for all tickets from Freshdesk
"""
import os
import json
import argparse
import logging
from freshdesk_client import FreshdeskClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Download attachments for Freshdesk tickets')
    parser.add_argument('--domain', required=True, help='Freshdesk domain (e.g., company.freshdesk.com)')
    parser.add_argument('--api-key', required=True, help='Freshdesk API key')
    parser.add_argument('--tickets-file', help='JSON file containing tickets (if not provided, will fetch tickets)')
    parser.add_argument('--output-dir', default='./attachments', help='Directory to save attachments')
    return parser.parse_args()

def load_tickets_from_file(file_path):
    """
    Load tickets from a JSON file
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        list: List of ticket objects
    """
    with open(file_path, 'r') as f:
        tickets = json.load(f)
    
    logger.info(f"Loaded {len(tickets)} tickets from {file_path}")
    return tickets

def download_attachments_for_ticket(client, ticket_id, output_dir):
    """
    Download all attachments for a specific ticket
    
    Args:
        client (FreshdeskClient): Freshdesk client
        ticket_id (int): Ticket ID
        output_dir (str): Directory to save attachments
        
    Returns:
        list: List of paths to downloaded attachments
    """
    # Get ticket details to access attachments
    ticket = client.get_ticket(ticket_id)
    
    # Create ticket-specific directory
    ticket_dir = os.path.join(output_dir, f"ticket_{ticket_id}")
    os.makedirs(ticket_dir, exist_ok=True)
    
    # Save ticket metadata
    ticket_metadata_path = os.path.join(ticket_dir, "ticket_metadata.json")
    with open(ticket_metadata_path, 'w') as f:
        json.dump(ticket, f, indent=2)
    
    # Get attachments
    attachments = ticket.get('attachments', [])
    if not attachments:
        logger.info(f"No attachments found for ticket {ticket_id}")
        return []
    
    logger.info(f"Found {len(attachments)} attachments for ticket {ticket_id}")
    
    # Download each attachment
    downloaded_files = []
    for attachment in attachments:
        attachment_id = attachment['id']
        try:
            file_path = client.download_attachment(attachment_id, ticket_dir)
            downloaded_files.append(file_path)
            logger.info(f"Downloaded attachment {attachment_id} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to download attachment {attachment_id}: {e}")
    
    return downloaded_files

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create Freshdesk client
    client = FreshdeskClient(args.domain, args.api_key)
    
    # Get tickets (either from file or by fetching)
    if args.tickets_file and os.path.exists(args.tickets_file):
        tickets = load_tickets_from_file(args.tickets_file)
    else:
        logger.info("No tickets file provided or file not found. Retrieving tickets from Freshdesk...")
        tickets = client.get_all_tickets()
        logger.info(f"Retrieved {len(tickets)} tickets")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Download attachments for each ticket
    total_attachments = 0
    for ticket in tickets:
        ticket_id = ticket['id']
        logger.info(f"Processing ticket {ticket_id}: {ticket.get('subject', 'No subject')}")
        
        downloaded_files = download_attachments_for_ticket(client, ticket_id, args.output_dir)
        total_attachments += len(downloaded_files)
    
    logger.info(f"Downloaded a total of {total_attachments} attachments for {len(tickets)} tickets")
    logger.info("Attachment download completed successfully")

if __name__ == "__main__":
    main()
