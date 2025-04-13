#!/usr/bin/env python3
"""
Script to upload Freshdesk tickets and attachments to SharePoint
"""
import os
import json
import argparse
import logging
from sharepoint_client import SharePointClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Upload Freshdesk tickets and attachments to SharePoint')
    parser.add_argument('--site-url', required=True, help='SharePoint site URL')
    parser.add_argument('--username', required=True, help='SharePoint username')
    parser.add_argument('--password', required=True, help='SharePoint password')
    parser.add_argument('--tickets-dir', required=True, help='Directory containing ticket data')
    parser.add_argument('--attachments-dir', required=True, help='Directory containing ticket attachments')
    parser.add_argument('--sharepoint-folder', default='FreshdeskTickets', help='Base folder in SharePoint')
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

def find_latest_tickets_file(tickets_dir):
    """
    Find the latest tickets JSON file in the directory
    
    Args:
        tickets_dir (str): Directory containing ticket data files
        
    Returns:
        str: Path to the latest tickets file
    """
    json_files = [f for f in os.listdir(tickets_dir) if f.startswith('tickets_') and f.endswith('.json')]
    
    if not json_files:
        raise FileNotFoundError(f"No ticket files found in {tickets_dir}")
    
    # Sort by filename (which includes timestamp)
    latest_file = sorted(json_files)[-1]
    return os.path.join(tickets_dir, latest_file)

def upload_ticket_to_sharepoint(client, ticket, attachments_dir, sharepoint_base_folder):
    """
    Upload a ticket and its attachments to SharePoint
    
    Args:
        client (SharePointClient): SharePoint client
        ticket (dict): Ticket object
        attachments_dir (str): Directory containing ticket attachments
        sharepoint_base_folder (str): Base folder in SharePoint
        
    Returns:
        dict: Upload results
    """
    ticket_id = ticket['id']
    ticket_subject = ticket.get('subject', 'No subject')
    
    # Create a folder for the ticket
    ticket_folder = f"{sharepoint_base_folder}/Ticket_{ticket_id}"
    client.create_folder(ticket_folder)
    
    # Save ticket metadata to a temporary file and upload it
    temp_metadata_file = f"/tmp/ticket_{ticket_id}_metadata.json"
    with open(temp_metadata_file, 'w') as f:
        json.dump(ticket, f, indent=2)
    
    # Upload the metadata file
    client.upload_file(temp_metadata_file, ticket_folder)
    
    # Clean up the temporary file
    os.remove(temp_metadata_file)
    
    # Check if there are attachments for this ticket
    ticket_attachments_dir = os.path.join(attachments_dir, f"ticket_{ticket_id}")
    if os.path.exists(ticket_attachments_dir):
        # Upload all attachments
        upload_results = client.upload_folder_contents(ticket_attachments_dir, ticket_folder)
        logger.info(f"Uploaded {upload_results['success']} attachments for ticket {ticket_id}")
        return {
            'ticket_id': ticket_id,
            'subject': ticket_subject,
            'metadata_uploaded': True,
            'attachments': upload_results
        }
    else:
        logger.info(f"No attachments found for ticket {ticket_id}")
        return {
            'ticket_id': ticket_id,
            'subject': ticket_subject,
            'metadata_uploaded': True,
            'attachments': {'success': 0, 'failed': 0, 'files': []}
        }

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create SharePoint client
    client = SharePointClient(args.site_url, args.username, args.password)
    
    # Find the latest tickets file
    try:
        tickets_file = find_latest_tickets_file(args.tickets_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    # Load tickets
    tickets = load_tickets_from_file(tickets_file)
    
    # Create the base folder in SharePoint
    client.create_folder(args.sharepoint_folder)
    
    # Upload each ticket and its attachments
    results = []
    for ticket in tickets:
        logger.info(f"Uploading ticket {ticket['id']}: {ticket.get('subject', 'No subject')}")
        result = upload_ticket_to_sharepoint(
            client, 
            ticket, 
            args.attachments_dir, 
            args.sharepoint_folder
        )
        results.append(result)
    
    # Save upload results
    results_file = os.path.join(args.tickets_dir, "upload_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Calculate summary statistics
    total_tickets = len(results)
    total_attachments_success = sum(r['attachments']['success'] for r in results)
    total_attachments_failed = sum(r['attachments']['failed'] for r in results)
    
    logger.info(f"Upload completed: {total_tickets} tickets, {total_attachments_success} attachments uploaded, {total_attachments_failed} attachments failed")
    logger.info(f"Results saved to {results_file}")

if __name__ == "__main__":
    main()
