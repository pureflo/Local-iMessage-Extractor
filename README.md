# iMessage Database Extractor 📱

A Python tool for extracting and exporting iMessage conversations from macOS/iOS backup databases. This tool allows you to search contacts, extract message histories, and export conversations to CSV format.

## ✨ Features

- 🔍 **Search Contacts**: Find contacts by phone number, email, or name
- 💬 **Extract Messages**: Retrieve complete message histories with timestamps
- 📊 **Text Analysis**: Analyze message content including attachments and special message types
- 🔄 **NSAttributedString Support**: Properly decodes Apple's rich text format
- 📁 **CSV Export**: Export conversations to CSV for analysis or archival
- 🐛 **Debug Mode**: Detailed logging and schema inspection for troubleshooting
- 🎯 **Smart Text Extraction**: Handles multiple message formats (text, attributedBody, payload_data)

## 📋 Requirements

- Python 3.6+
- macOS or access to an iOS backup
- Read access to iMessage database (`chat.db`)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Local-iMessage-Extractor.git
cd imessage-extractor
```

2. No additional dependencies required! Uses Python standard library only.

## 💾 Database Location

The script expects the iMessage database at one of these locations:

- **Default**: `~/Downloads/chat.db`
- **macOS**: `~/Library/Messages/chat.db`
- **iOS Backup**: Extract from iPhone backup

### Copying the Database (macOS)

```bash
# Copy from Messages app (requires Full Disk Access)
cp ~/Library/Messages/chat.db ~/Downloads/chat.db
```

## 🎮 Usage

### Basic Usage

```bash
python3 imessage-extractor.py
```

### With Custom Database Path

```bash
python3 imessage-extractor.py --db-path /path/to/chat.db
```

### Debug Mode

```bash
python3 imessage-extractor.py --debug
```

### Analyze Specific Contact

```bash
python3 imessage-extractor.py --analyze-contact "+1234567890"
```

## 📱 Interactive Menu

When you run the script, you'll see:

```
🗨️  Enhanced iMessage Database Extractor v1.1.2
============================================================
✅ Connected to database: /Users/you/Downloads/chat.db
📊 Total messages in database: 123,456

📱 Options:
1. Search for contacts (with text analysis)
2. Extract messages with debugging
3. Analyze empty messages for contact
4. Exit
```

## 🔧 Features in Detail

### Contact Search
- Lists all contacts with message counts
- Shows how many messages contain actual text vs. attachments
- Sorted by message frequency

### Message Extraction
- Extracts all messages for a selected contact
- Handles various message types:
  - Regular text messages
  - Rich text (NSAttributedString)
  - Attachments
  - Reactions and effects
  - App messages (games, payments, etc.)

### CSV Export Format
The exported CSV includes:
- **date**: Timestamp in readable format (YYYY-MM-DD HH:MM:SS)
- **sender**: "Me" or contact identifier
- **message**: Message text or placeholder for special content
- **service**: iMessage, SMS, etc.
- **has_attachments**: Yes/No
- **message_type**: Text or specific app bundle ID

## 🐛 Troubleshooting

### Common Issues

1. **"Database file not found"**
   - Ensure chat.db is in the expected location
   - Use `--db-path` to specify custom location

2. **"no such column: payload_data"**
   - You're using an older version - update to v1.1.2+

3. **Permission Denied**
   - On macOS, grant Terminal "Full Disk Access" in System Preferences
   - Copy the database to Downloads folder as a workaround

4. **Empty or Binary Messages**
   - Use `--debug` mode to see raw message data
   - The tool now handles NSAttributedString format automatically

## 📊 Database Schema

The tool works with the standard iMessage database structure:
- `message` table: Core message data
- `handle` table: Contact information
- `chat` table: Conversation threads
- `attachment` table: Media files (referenced, not extracted)

## ⚠️ Privacy & Security

- **Local Processing**: All processing happens locally on your machine
- **No Network Access**: The tool never sends data over the network
- **Sensitive Data**: Message databases contain private conversations - handle with care
- **Backups**: Always work with a copy of your chat.db, not the original


## 📝 Version History

- **v1.1.2** - Fixed sqlite3.Row access errors, improved NSAttributedString extraction
- **v1.1.1** - Fixed payload_data column name (was payloadData)
- **v1.1.0** - Added text debugging and empty message analysis
- **v1.0.0** - Initial release

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 👤 Author

**Shawn**

## 🙏 Acknowledgments

- Thanks to the Apple Archive Format documentation community
- SQLite for the robust database engine
- Contributors and testers

## ⚡ Quick Start Example

```bash
# 1. Copy your iMessage database
cp ~/Library/Messages/chat.db ~/Downloads/

# 2. Run the extractor
python3 imessage-extractor.py

# 3. Search for a contact
# Choose option 1, enter name/number

# 4. Extract messages
# Choose option 2, select contact

# 5. Export to CSV
# Confirm export when prompted
```

## 🔮 Future Enhancements

- [ ] Support for extracting attachments/media
- [ ] Group chat support
- [ ] Message threading visualization
- [ ] JSON export format
- [ ] Statistical analysis features
- [ ] GUI version
- [ ] Windows support for iOS backups

## 📧 Support

For issues, questions, or suggestions, please [open an issue](https://github.com/yourusername/imessage-extractor/issues) on GitHub.

---

**Note**: This tool is for personal use only. Ensure you have the right to access and export any messages you extract. Always respect privacy and applicable laws.
