# 🛫 Cockpit Switch Testing Tool

A Flask-based web application for testing cockpit switches in a simulated F-35 control environment. Designed for both manual and automated validation of input and output switches using a JSON-defined test plan and real-time OPC UA communication.

## Features

- Panel-based test structure (e.g., PTMS, Flight Control Panel)
- Progressive test unlocking (tests are revealed one by one)
- Dual testing modes:
  - **Manual**: User manually checks switch status
  - **Auto**: Automatically proceeds through tests with real-time validation
- Input and Output test handling:
  - Input: Read live switch states via OPC
  - Output: Write values to nodes and prompt user confirmation
- Real-time OPC UA integration using `switch_reader.py`
- Dark mode with bright pastel-themed UI
- 'Test All' functionality to test all switches in sequence
- Panel-wise and global progress tracking
- Reset functionality (per panel and global)
- Support for test-specific images (e.g., switch photos)
- Skippable tests and revisit flow in auto mode

## Tech Stack

- Python 3
- Flask
- JSON (for test configuration)
- OPC UA via `opcua` library
- Bootstrap (for frontend styling)
- JavaScript (for polling and dynamic UI updates)

## Setup Instructions  

1. **Clone the Repository**
   ```bash
   git clone https://github.com/krishnasharma2005/Cockpit-Tester.git
   cd Cockpit-Tester

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

3. **Set OPC Node Configurations**
- Edit `test_plan.json` with your actual OPC UA node IDs and expected values.
- Confirm `switch_reader.py` has the correct IP, port, and credentials.

4. **Run the App**
   ```bash
   python app.py

5. **Access in Browser**
   ```bash
   http://localhost:5000

## Customization

- To add a new panel or switch, simply update `test_plan.json`
- For new UI styles, edit `static/cc/styles.css`
- You can edit the test logic in app.py to support more test types or validation logic

