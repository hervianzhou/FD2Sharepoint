#!/usr/bin/env python3
"""
Script to retrieve all tickets from Freshdesk
"""
import os
import json
import argparse
import logging
from datetime import datetime
from freshdesk_client import FreshdeskClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Retrieve tickets from Freshdesk')
    parser.add_argument('--domain', required=True, help='Freshdesk domain (e.g., company.freshdesk.com)')
    parser.add_argument('--api-key', required=True, help='Freshdesk API key')
    parser.add_argument('--output-dir', default='./data', help='Directory to save ticket data')
    parser.add_argument('--per-page', type=int, default=100, help='Number of tickets per page (max 100)')
    return parser.parse_args()

def save_tickets_to_file(tickets, output_dir):
    """
    Save tickets to a JSON file
    
    Args:
        tickets (list): List of ticket objects
        output_dir (str): Directory to save the file
        
    Returns:
        str: Path to the saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"tickets_{timestamp}.json"
    file_path = os.path.join(output_dir, filename)
    
    # Save tickets to file
    with open(file_path, 'w') as f:
        json.dump(tickets, f, indent=2)
        
    logger.info(f"Saved {len(tickets)} tickets to {file_path}")
    return file_path

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create Freshdesk client
    client = FreshdeskClient(args.domain, args.api_key)
    
    # Get all tickets
    logger.info("Retrieving all tickets from Freshdesk...")
    tickets = client.get_all_tickets(per_page=args.per_page)
    logger.info(f"Retrieved {len(tickets)} tickets")
    
    # Save tickets to file
    tickets_file = save_tickets_to_file(tickets, args.output_dir)
    
    # Create a ticket index file with just IDs and subjects for easier reference
    ticket_index = [{'id': ticket['id'], 'subject': ticket['subject']} for ticket in tickets]
    index_file = os.path.join(args.output_dir, 'ticket_index.json')
    with open(index_file, 'w') as f:
        json.dump(ticket_index, f, indent=2)
    
    logger.info(f"Saved ticket index to {index_file}")
    logger.info("Ticket retrieval completed successfully")

if __name__ == "__main__":
    main()
