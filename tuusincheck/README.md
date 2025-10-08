# Tethering Network Monitor App

A Windows 11 application that monitors network usage of applications during tethering every 3 minutes.

## Features

- **Real-time Monitoring**: Monitor network usage of each process every 3 minutes
- **GUI Display**: Intuitive graphical interface to display network usage
- **Data Saving**: Save monitoring data in JSON format
- **Cumulative Statistics**: Track cumulative network usage per application
- **Auto Update**: Automatically update display every 5 seconds

## System Requirements

- Windows 11
- Python 3.8 or higher
- Administrator privileges (recommended)

## Installation

### 1. Install Python
If Python 3.8 or higher is not installed, download and install from [Python official website](https://www.python.org/downloads/).

### 2. Install Dependencies
Use one of the following methods to install dependencies:

#### Method A: Use batch file (recommended)
```cmd
install.bat
```

#### Method B: Manual installation
```cmd
pip install -r requirements.txt
```

## Usage

### 起動方法の選択

#### 方法1: 独立起動（推奨）⭐
PowerShellやコマンドプロンプトを閉じてもアプリが動作し続けます。

**通常モード:**
- `独立起動.bat` をダブルクリック
- または `独立起動.vbs` をダブルクリック

**管理者モード（推奨）:**
- `独立起動(管理者).bat` をダブルクリック
- または `独立起動(管理者).vbs` をダブルクリック

#### 方法2: 通常起動
PowerShellやコマンドプロンプトを閉じるとアプリも終了します。

```cmd
テザリング通信量チェック(管理者).bat
```

#### 方法3: コマンドライン
```cmd
python network_monitor_v2.py
```
または
```cmd
pythonw network_monitor_v2.py  # ウィンドウなし
```

### 2. Start Monitoring
1. Click "Start Monitoring" button
2. Network usage of each app will be monitored every 3 minutes
3. Results will be displayed in real-time

### 3. Save Data
- Click "Save Data" button to save monitoring data to JSON file
- Files are saved with format: `network_usage_YYYYMMDD_HHMMSS.json`

### 4. Stop Monitoring
- Click "Stop Monitoring" button to stop monitoring
- Click "Clear Data" button to reset cumulative data

## Display Items

| Item | Description |
|------|-------------|
| PID | Process ID |
| App Name | Process name |
| Sent | Bytes sent |
| Received | Bytes received |
| Total | Total (sent + received) |
| Last Update | Last update time |

## File Structure

```
tuusincheck/
├── network_monitor.py    # Main application
├── requirements.txt     # Dependencies
├── install.bat         # Installation script
├── start_app.bat       # App launcher
└── README.md           # This file
```

## Notes

### Security
- Running with administrator privileges is recommended
- Some processes may not be monitored due to access permissions

### Performance
- Slight CPU usage during monitoring
- Memory usage may increase during long-term monitoring

### Tethering Environment
- Most effective when used during tethering
- Can also be used with regular Wi-Fi connections, but particularly useful for tethering data limit management

## Troubleshooting

### Common Issues

#### 1. "psutil" module not found
```cmd
pip install psutil
```

#### 2. Administrator privilege error
- Run Command Prompt as Administrator
- Or run PowerShell as Administrator

#### 3. Some processes not displayed
- Run with administrator privileges
- System processes may not be displayed

#### 4. Cannot start monitoring
- May conflict with other network monitoring software
- Temporarily stop other monitoring software

## Technical Specifications

### Monitoring Interval
- Data collection: 3 minutes
- Display update: 5 seconds

### Data Format
JSON file format:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "total_usage": {
    "1234": {
      "bytes_sent": 1024000,
      "bytes_recv": 2048000
    }
  }
}
```

### Supported Protocols
- TCP
- UDP
- Other network protocols

## License

This application is provided under the MIT License.

## Support

If you encounter issues, please contact with the following information:
- Windows 11 version
- Python version
- Error messages
- Execution environment details

## Update History

### v1.0.0 (2024-01-01)
- Initial release
- Basic network usage monitoring
- GUI interface
- Data saving functionality