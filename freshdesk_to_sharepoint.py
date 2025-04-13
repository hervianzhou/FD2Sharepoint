#!/usr/bin/env python3
"""
Main script to orchestrate the entire process of retrieving Freshdesk tickets,
downloading attachments, and uploading to SharePoint
"""
import os
import argparse
import logging
import json
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("freshdesk_to_sharepoint.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Retrieve Freshdesk tickets and upload to SharePoint')
    
    # Freshdesk arguments
    parser.add_argument('--freshdesk-domain', required=True, help='Freshdesk domain (e.g., company.freshdesk.com)')
    parser.add_argument('--freshdesk-api-key', required=True, help='Freshdesk API key')
    
    # SharePoint arguments
    parser.add_argument('--sharepoint-url', required=True, help='SharePoint site URL')
    parser.add_argument('--sharepoint-username', required=True, help='SharePoint username')
    parser.add_argument('--sharepoint-password', required=True, help='SharePoint password')
    parser.add_argument('--sharepoint-folder', default='FreshdeskTickets', help='Base folder in SharePoint')
    
    # Directory arguments
    parser.add_argument('--data-dir', default='./data', help='Directory to store data')
    
    return parser.parse_args()

def create_directories(base_dir):
    """Create necessary directories"""
    tickets_dir = os.path.join(base_dir, 'tickets')
    attachments_dir = os.path.join(base_dir, 'attachments')
    
    os.makedirs(tickets_dir, exist_ok=True)
    os.makedirs(attachments_dir, exist_ok=True)
    
    return tickets_dir, attachments_dir

def run_command(command):
    """Run a command and log the output"""
    logger.info(f"Running command: {command}")
    start_time = time.time()
    exit_code = os.system(command)
    duration = time.time() - start_time
    
    if exit_code == 0:
        logger.info(f"Command completed successfully in {duration:.2f} seconds")
    else:
        logger.error(f"Command failed with exit code {exit_code}")
    
    return exit_code == 0

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create directories
    tickets_dir, attachments_dir = create_directories(args.data_dir)
    
    # Start time for the entire process
    start_time = datetime.now()
    logger.info(f"Starting Freshdesk to SharePoint migration at {start_time}")
    
    # Step 1: Retrieve tickets from Freshdesk
    logger.info("Step 1: Retrieving tickets from Freshdesk")
    retrieve_tickets_cmd = (
        f"python3 retrieve_tickets.py "
        f"--domain {args.freshdesk_domain} "
        f"--api-key {args.freshdesk_api_key} "
        f"--output-dir {tickets_dir}"
    )
    if not run_command(retrieve_tickets_cmd):
        logger.error("Failed to retrieve tickets from Freshdesk")
        return
    
    # Step 2: Download attachments
    logger.info("Step 2: Downloading attachments")
    # Find the latest tickets file
    json_files = [f for f in os.listdir(tickets_dir) if f.startswith('tickets_') and f.endswith('.json')]
    if not json_files:
        logger.error(f"No ticket files found in {tickets_dir}")
        return
    
    latest_tickets_file = os.path.join(tickets_dir, sorted(json_files)[-1])
    
    download_attachments_cmd = (
        f"python3 download_attachments.py "
        f"--domain {args.freshdesk_domain} "
        f"--api-key {args.freshdesk_api_key} "
        f"--tickets-file {latest_tickets_file} "
        f"--output-dir {attachments_dir}"
    )
    if not run_command(download_attachments_cmd):
        logger.error("Failed to download attachments")
        return
    
    # Step 3: Upload to SharePoint
    logger.info("Step 3: Uploading to SharePoint")
    upload_to_sharepoint_cmd = (
        f"python3 upload_to_sharepoint.py "
        f"--site-url {args.sharepoint_url} "
        f"--username {args.sharepoint_username} "
        f"--password {args.sharepoint_password} "
        f"--tickets-dir {tickets_dir} "
        f"--attachments-dir {attachments_dir} "
        f"--sharepoint-folder {args.sharepoint_folder}"
    )
    if not run_command(upload_to_sharepoint_cmd):
        logger.error("Failed to upload to SharePoint")
        return
    
    # Calculate statistics
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Load upload results
    upload_results_file = os.path.join(tickets_dir, "upload_results.json")
    if os.path.exists(upload_results_file):
        with open(upload_results_file, 'r') as f:
            results = json.load(f)
        
        total_tickets = len(results)
        total_attachments_success = sum(r['attachments']['success'] for r in results)
        total_attachments_failed = sum(r['attachments']['failed'] for r in results)
        
        # Generate summary report
        summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'total_tickets': total_tickets,
            'total_attachments_success': total_attachments_success,
            'total_attachments_failed': total_attachments_failed,
            'freshdesk_domain': args.freshdesk_domain,
            'sharepoint_url': args.sharepoint_url,
            'sharepoint_folder': args.sharepoint_folder
        }
        
        # Save summary report
        summary_file = os.path.join(args.data_dir, "migration_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Migration completed in {duration}")
        logger.info(f"Total tickets: {total_tickets}")
        logger.info(f"Total attachments uploaded: {total_attachments_success}")
        logger.info(f"Total attachments failed: {total_attachments_failed}")
        logger.info(f"Summary saved to {summary_file}")
        
        # Generate a human-readable report
        report_file = os.path.join(args.data_dir, "migration_report.txt")
        with open(report_file, 'w') as f:
            f.write("Freshdesk to SharePoint Migration Report\n")
            f.write("=======================================\n\n")
            f.write(f"Start time: {start_time}\n")
            f.write(f"End time: {end_time}\n")
            f.write(f"Duration: {duration}\n\n")
            f.write(f"Freshdesk domain: {args.freshdesk_domain}\n")
            f.write(f"SharePoint site: {args.sharepoint_url}\n")
            f.write(f"SharePoint folder: {args.sharepoint_folder}\n\n")
            f.write(f"Total tickets processed: {total_tickets}\n")
            f.write(f"Total attachments uploaded: {total_attachments_success}\n")
            f.write(f"Total attachments failed: {total_attachments_failed}\n\n")
            
            f.write("Ticket Details:\n")
            f.write("--------------\n")
            for ticket in results:
                f.write(f"Ticket {ticket['ticket_id']}: {ticket['subject']}\n")
                f.write(f"  Attachments: {ticket['attachments']['success']} uploaded, {ticket['attachments']['failed']} failed\n")
        
        logger.info(f"Detailed report saved to {report_file}")
    else:
        logger.warning(f"Upload results file not found: {upload_results_file}")
        logger.info(f"Migration completed in {duration}")

if __name__ == "__main__":
    main()
