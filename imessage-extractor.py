#!/usr/bin/env python3
"""
Enhanced iMessage Database Extractor with Text Debugging
Includes additional debugging for messages with no text content

Author: Shawn
Fixed: Column name compatibility (payload_data)
"""

import sqlite3
import csv
import json
import os
import argparse
import sys
import re
from datetime import datetime
from pathlib import Path

__version__ = "1.1.2"

class iMessageExtractor:
    def __init__(self, db_path=None, debug=False):
        """Initialize the extractor with database path"""
        if db_path is None:
            self.db_path = os.path.expanduser("~/Downloads/chat.db")
        else:
            self.db_path = os.path.expanduser(db_path)
        
        self.conn = None
        self.debug = debug
        
    def log(self, message, level="INFO"):
        """Simple logging function"""
        if self.debug or level in ["ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def connect_to_database(self):
        """Connect to the SQLite database"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ Database file not found: {self.db_path}")
                return False
                
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            # Test connection and show schema info
            cursor = self.conn.execute("SELECT COUNT(*) FROM message")
            message_count = cursor.fetchone()[0]
            
            print(f"✅ Connected to database: {self.db_path}")
            print(f"📊 Total messages in database: {message_count:,}")
            
            # Show database schema for debugging
            if self.debug:
                self.show_message_schema()
            
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return False
    
    def show_message_schema(self):
        """Show the structure of the message table for debugging"""
        try:
            cursor = self.conn.execute("PRAGMA table_info(message)")
            columns = cursor.fetchall()
            
            print("\n🔍 Message table schema:")
            for col in columns:
                print(f"  {col['name']} ({col['type']})")
            
            # Check for messages with different text field patterns
            text_analysis_queries = [
                ("Non-null text messages", "SELECT COUNT(*) FROM message WHERE text IS NOT NULL AND text != ''"),
                ("Null text messages", "SELECT COUNT(*) FROM message WHERE text IS NULL"),
                ("Empty text messages", "SELECT COUNT(*) FROM message WHERE text = ''"),
                ("Messages with attributedBody", "SELECT COUNT(*) FROM message WHERE attributedBody IS NOT NULL"),
                ("Messages with payload_data", "SELECT COUNT(*) FROM message WHERE payload_data IS NOT NULL"),
            ]
            
            print("\n📊 Text content analysis:")
            for description, query in text_analysis_queries:
                try:
                    cursor = self.conn.execute(query)
                    count = cursor.fetchone()[0]
                    print(f"  {description}: {count:,}")
                except Exception as e:
                    print(f"  {description}: Error - {e}")
                    
        except Exception as e:
            print(f"Error analyzing schema: {e}")
    
    def convert_apple_timestamp(self, apple_timestamp):
        """Convert Apple timestamp to readable datetime"""
        if apple_timestamp is None:
            return None
        
        try:
            apple_epoch = datetime(2001, 1, 1)
            seconds = apple_timestamp / 1_000_000_000
            return apple_epoch.timestamp() + seconds
        except Exception as e:
            self.log(f"Timestamp conversion error: {e}", "WARNING")
            return None
    
    def extract_message_text(self, message_row):
        """Extract text from various possible fields in the message"""
        # Convert Row object to dict if needed
        if not isinstance(message_row, dict):
            message_row = dict(message_row)
        
        # Try different fields where text might be stored
        text_candidates = [
            message_row.get('text'),
            message_row.get('body'),  # Sometimes used in older versions
            message_row.get('attributedBody'),  # Rich text content
            message_row.get('payload_data'),  # Encoded content
        ]
        
        for candidate in text_candidates:
            if candidate and str(candidate).strip():
                # Handle potential binary data
                if isinstance(candidate, bytes):
                    try:
                        # Check if it's an NSAttributedString (Apple's format)
                        if b'NSAttributedString' in candidate or b'NSMutableAttributedString' in candidate:
                            # Extract readable text from NSAttributedString
                            # Look for continuous sequences of printable characters
                            # Find all sequences of printable ASCII/UTF-8 text
                            text_parts = []
                            i = 0
                            while i < len(candidate):
                                # Skip non-printable bytes
                                while i < len(candidate) and (candidate[i] < 0x20 or candidate[i] > 0x7E):
                                    i += 1
                                # Collect printable bytes
                                start = i
                                while i < len(candidate) and 0x20 <= candidate[i] <= 0x7E:
                                    i += 1
                                if i > start:
                                    text = candidate[start:i].decode('utf-8', errors='ignore')
                                    # Filter out class names and keep meaningful text
                                    if len(text) > 20 and not text.startswith('NS') and not text.startswith('__kIM'):
                                        text_parts.append(text)
                            
                            # Return the longest meaningful text found
                            if text_parts:
                                return max(text_parts, key=len)
                        else:
                            return candidate.decode('utf-8')
                    except (UnicodeDecodeError, Exception) as e:
                        self.log(f"Failed to decode binary data: {e}", "DEBUG")
                        continue
                elif candidate:
                    return str(candidate).strip()
        
        return None
    
    def analyze_empty_messages(self, handle_id, limit=10):
        """Analyze messages that appear to have no text content"""
        query = """
        SELECT 
            m.ROWID,
            m.text,
            m.attributedBody,
            m.payload_data,
            m.cache_has_attachments,
            m.balloon_bundle_id,
            m.associated_message_type,
            m.message_summary_info,
            m.date,
            m.service,
            hex(m.payload_data) as payload_hex
        FROM message m
        JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        JOIN chat c ON cmj.chat_id = c.ROWID
        JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
        JOIN handle h ON chj.handle_id = h.ROWID
        WHERE h.ROWID = ? AND (m.text IS NULL OR m.text = '')
        ORDER BY m.date ASC
        LIMIT ?
        """
        
        cursor = self.conn.execute(query, (handle_id, limit))
        messages = cursor.fetchall()
        
        if messages:
            print(f"\n🔍 Analyzing {len(messages)} messages with no text:")
            for msg in messages:
                # Convert Row to dict for easier access
                msg_dict = dict(msg)
                print(f"\nMessage ID: {msg_dict['ROWID']}")
                print(f"  Date: {msg_dict['date']}")
                print(f"  Has attachments: {bool(msg_dict['cache_has_attachments'])}")
                print(f"  Balloon bundle: {msg_dict['balloon_bundle_id']}")
                print(f"  Message type: {msg_dict['associated_message_type']}")
                print(f"  Service: {msg_dict['service']}")
                print(f"  Text field: {repr(msg_dict['text'])}")
                print(f"  AttributedBody: {repr(msg_dict['attributedBody'])}")
                print(f"  PayloadData length: {len(msg_dict['payload_data']) if msg_dict['payload_data'] else 0}")
                if msg_dict['payload_data'] and len(msg_dict['payload_data']) < 200:
                    print(f"  PayloadData hex: {msg_dict['payload_hex']}")
    
    def search_contacts(self, search_term="", limit=50):
        """Search for contacts by name, phone, or email"""
        if not self.conn:
            return []
        
        try:
            if search_term:
                query = """
                SELECT DISTINCT 
                    h.ROWID as handle_id,
                    h.id as contact_identifier,
                    h.uncanonicalized_id,
                    h.service,
                    COUNT(m.ROWID) as message_count,
                    SUM(CASE WHEN m.text IS NOT NULL AND m.text != '' THEN 1 ELSE 0 END) as text_message_count,
                    MAX(m.date) as last_message_date
                FROM handle h
                LEFT JOIN chat_handle_join chj ON h.ROWID = chj.handle_id
                LEFT JOIN chat c ON chj.chat_id = c.ROWID
                LEFT JOIN chat_message_join cmj ON c.ROWID = cmj.chat_id
                LEFT JOIN message m ON cmj.message_id = m.ROWID
                WHERE (h.id LIKE ? OR h.uncanonicalized_id LIKE ?)
                GROUP BY h.ROWID
                HAVING message_count > 0
                ORDER BY message_count DESC
                LIMIT ?
                """
                search_pattern = f"%{search_term}%"
                cursor = self.conn.execute(query, (search_pattern, search_pattern, limit))
            else:
                query = """
                SELECT DISTINCT 
                    h.ROWID as handle_id,
                    h.id as contact_identifier,
                    h.uncanonicalized_id,
                    h.service,
                    COUNT(m.ROWID) as message_count,
                    SUM(CASE WHEN m.text IS NOT NULL AND m.text != '' THEN 1 ELSE 0 END) as text_message_count,
                    MAX(m.date) as last_message_date
                FROM handle h
                LEFT JOIN chat_handle_join chj ON h.ROWID = chj.handle_id
                LEFT JOIN chat c ON chj.chat_id = c.ROWID
                LEFT JOIN chat_message_join cmj ON c.ROWID = cmj.chat_id
                LEFT JOIN message m ON cmj.message_id = m.ROWID
                GROUP BY h.ROWID
                HAVING message_count > 0
                ORDER BY message_count DESC
                LIMIT ?
                """
                cursor = self.conn.execute(query, (limit,))
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error searching contacts: {e}")
            return []
    
    def get_messages_for_contact(self, handle_id, limit=None, analyze_empty=False):
        """Get all messages for a specific contact with enhanced text extraction"""
        if not self.conn:
            return []
        
        try:
            # Enhanced query to get more fields for text extraction
            query = """
            SELECT DISTINCT
                m.ROWID as message_id,
                m.text,
                m.attributedBody,
                m.payload_data,
                m.date,
                m.date_read,
                m.date_delivered,
                m.is_from_me,
                m.service,
                m.account,
                m.subject,
                m.cache_has_attachments,
                m.balloon_bundle_id,
                m.associated_message_type,
                m.message_summary_info,
                h.id as contact_identifier,
                h.uncanonicalized_id
            FROM message m
            JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
            JOIN chat c ON cmj.chat_id = c.ROWID
            JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
            JOIN handle h ON chj.handle_id = h.ROWID
            WHERE h.ROWID = ?
            ORDER BY m.date ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = self.conn.execute(query, (handle_id,))
            messages = cursor.fetchall()
            
            if analyze_empty:
                self.analyze_empty_messages(handle_id)
            
            # Process messages with enhanced text extraction
            processed_messages = []
            text_found_count = 0
            
            for msg in messages:
                msg_dict = dict(msg)
                
                # Enhanced text extraction
                extracted_text = self.extract_message_text(msg)
                msg_dict['extracted_text'] = extracted_text
                
                if extracted_text:
                    text_found_count += 1
                    msg_dict['display_text'] = extracted_text
                else:
                    # Provide more specific placeholders based on message type
                    if msg_dict['cache_has_attachments']:
                        msg_dict['display_text'] = '[Attachment]'
                    elif msg_dict['balloon_bundle_id']:
                        msg_dict['display_text'] = f'[App Message: {msg_dict["balloon_bundle_id"]}]'
                    elif msg_dict['associated_message_type']:
                        msg_dict['display_text'] = '[Reaction/Effect]'
                    else:
                        msg_dict['display_text'] = '[No text content]'
                
                # Convert timestamps
                if msg_dict['date']:
                    timestamp = self.convert_apple_timestamp(msg_dict['date'])
                    if timestamp:
                        msg_dict['readable_date'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        msg_dict['readable_date'] = 'Unknown'
                else:
                    msg_dict['readable_date'] = 'Unknown'
                
                msg_dict['sender'] = 'Me' if msg_dict['is_from_me'] else msg_dict['contact_identifier']
                processed_messages.append(msg_dict)
            
            print(f"📝 Text extraction summary: {text_found_count}/{len(messages)} messages have readable text")
            
            return processed_messages
            
        except Exception as e:
            print(f"❌ Error extracting messages: {e}")
            return []
    
    def export_to_csv(self, messages, contact_name, output_dir="~/Downloads"):
        """Export messages to CSV with enhanced text handling"""
        try:
            output_dir = os.path.expanduser(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            safe_name = "".join(c for c in str(contact_name) if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"messages_{safe_name}_{timestamp}.csv"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['date', 'sender', 'message', 'service', 'has_attachments', 'message_type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for msg in messages:
                    writer.writerow({
                        'date': msg['readable_date'],
                        'sender': msg['sender'],
                        'message': msg['display_text'],
                        'service': msg['service'] or 'Unknown',
                        'has_attachments': 'Yes' if msg['cache_has_attachments'] else 'No',
                        'message_type': msg['balloon_bundle_id'] or 'Text'
                    })
            
            print(f"✅ Messages exported to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")
            return None
    
    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main function with enhanced debugging options"""
    parser = argparse.ArgumentParser(description='Extract messages from iMessage database')
    parser.add_argument('--db-path', help='Path to chat.db file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--analyze-contact', help='Analyze empty messages for a specific contact')
    
    args = parser.parse_args()
    
    print(f"🗨️  Enhanced iMessage Database Extractor v{__version__}")
    print("="*60)
    
    extractor = iMessageExtractor(db_path=args.db_path, debug=args.debug)
    
    if not extractor.connect_to_database():
        sys.exit(1)
    
    try:
        if args.analyze_contact:
            # Analyze a specific contact for debugging
            contacts = extractor.search_contacts(args.analyze_contact)
            if contacts:
                contact = contacts[0]
                print(f"\n🔍 Analyzing contact: {contact['contact_identifier']}")
                print(f"Total messages: {contact['message_count']}")
                print(f"Text messages: {contact['text_message_count']}")
                messages = extractor.get_messages_for_contact(contact['handle_id'], analyze_empty=True)
            return
        
        # Regular interactive mode
        while True:
            print("\n📱 Options:")
            print("1. Search for contacts (with text analysis)")
            print("2. Extract messages with debugging")
            print("3. Analyze empty messages for contact")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                search_term = input("🔍 Enter search term: ").strip()
                contacts = extractor.search_contacts(search_term)
                
                if contacts:
                    print(f"\n📞 Found {len(contacts)} contact(s):")
                    for i, contact in enumerate(contacts, 1):
                        print(f"{i:2d}. {contact['contact_identifier']} "
                              f"({contact['message_count']} total, {contact['text_message_count']} with text)")
                
            elif choice == '2':
                search_term = input("🔍 Enter contact to extract: ").strip()
                contacts = extractor.search_contacts(search_term)
                
                if contacts:
                    for i, contact in enumerate(contacts, 1):
                        print(f"{i:2d}. {contact['contact_identifier']}")
                    
                    try:
                        selection = int(input("Select contact: ")) - 1
                        if 0 <= selection < len(contacts):
                            selected = contacts[selection]
                            messages = extractor.get_messages_for_contact(
                                selected['handle_id'], 
                                analyze_empty=True
                            )
                            
                            if messages:
                                # Show sample messages
                                print(f"\n📝 First 5 messages:")
                                for msg in messages[:5]:
                                    print(f"[{msg['readable_date']}] {msg['sender']}: {msg['display_text']}")
                                
                                if input("\nExport to CSV? (y/n): ").lower() == 'y':
                                    extractor.export_to_csv(messages, selected['contact_identifier'])
                    except ValueError:
                        print("❌ Invalid selection")
            
            elif choice == '3':
                search_term = input("🔍 Enter contact to analyze: ").strip()
                contacts = extractor.search_contacts(search_term)
                
                if contacts:
                    contact = contacts[0]
                    extractor.analyze_empty_messages(contact['handle_id'])
            
            elif choice == '4':
                break
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    finally:
        extractor.close_connection()

if __name__ == "__main__":
    main()
