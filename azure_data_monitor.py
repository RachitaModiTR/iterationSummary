import os
import time
import json
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('azure_data_monitor.log'),
        logging.StreamHandler()
    ]
)

class AzureDataMonitor(FileSystemEventHandler):
    """Monitor Azure DevOps data files for changes"""
    
    def __init__(self, data_directory="./data", callback=None):
        self.data_directory = Path(data_directory)
        self.callback = callback
        self.monitored_extensions = {'.json', '.csv', '.xlsx', '.txt'}
        self.last_processed = {}
        
        # Ensure data directory exists
        self.data_directory.mkdir(exist_ok=True)
        
        logging.info(f"🔍 Azure Data Monitor initialized")
        logging.info(f"📁 Monitoring directory: {self.data_directory.absolute()}")
        logging.info(f"📋 Monitored file types: {', '.join(self.monitored_extensions)}")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only monitor specific file types
        if file_path.suffix.lower() not in self.monitored_extensions:
            return
            
        # Avoid processing the same file too frequently
        current_time = time.time()
        if file_path in self.last_processed:
            if current_time - self.last_processed[file_path] < 2:  # 2 second cooldown
                return
        
        self.last_processed[file_path] = current_time
        
        logging.info(f"📝 File modified: {file_path.name}")
        self.process_file_change(file_path, "modified")
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        if file_path.suffix.lower() not in self.monitored_extensions:
            return
            
        logging.info(f"✨ New file created: {file_path.name}")
        self.process_file_change(file_path, "created")
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        if file_path.suffix.lower() not in self.monitored_extensions:
            return
            
        logging.info(f"🗑️ File deleted: {file_path.name}")
        self.process_file_change(file_path, "deleted")
    
    def process_file_change(self, file_path, event_type):
        """Process file changes and extract relevant information"""
        try:
            file_info = {
                'timestamp': datetime.now().isoformat(),
                'file_path': str(file_path),
                'file_name': file_path.name,
                'event_type': event_type,
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                'file_extension': file_path.suffix.lower()
            }
            
            # Try to analyze file content if it exists and is readable
            if event_type != "deleted" and file_path.exists():
                file_info.update(self.analyze_file_content(file_path))
            
            # Log the change
            self.log_change(file_info)
            
            # Call callback if provided
            if self.callback:
                self.callback(file_info)
                
        except Exception as e:
            logging.error(f"❌ Error processing file change for {file_path}: {str(e)}")
    
    def analyze_file_content(self, file_path):
        """Analyze file content to extract metadata"""
        analysis = {}
        
        try:
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    analysis['record_count'] = len(data) if isinstance(data, list) else 1
                    analysis['content_type'] = 'json'
                    
                    # Check if it looks like Azure DevOps data
                    if isinstance(data, list) and len(data) > 0:
                        first_item = data[0]
                        if isinstance(first_item, dict):
                            if 'fields' in first_item or 'System.Id' in str(first_item):
                                analysis['data_source'] = 'azure_devops'
                                analysis['work_items'] = len(data)
            
            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
                analysis['record_count'] = len(df)
                analysis['column_count'] = len(df.columns)
                analysis['content_type'] = 'csv'
                analysis['columns'] = list(df.columns)
                
                # Check for Azure DevOps columns
                azure_columns = ['id', 'title', 'state', 'assignee', 'story_points']
                if any(col.lower() in [c.lower() for c in df.columns] for col in azure_columns):
                    analysis['data_source'] = 'azure_devops'
            
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                analysis['record_count'] = len(df)
                analysis['column_count'] = len(df.columns)
                analysis['content_type'] = 'excel'
                analysis['columns'] = list(df.columns)
            
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    analysis['content_type'] = 'text'
                    analysis['line_count'] = len(content.splitlines())
                    analysis['char_count'] = len(content)
                    
        except Exception as e:
            logging.warning(f"⚠️ Could not analyze content of {file_path}: {str(e)}")
            analysis['analysis_error'] = str(e)
        
        return analysis
    
    def log_change(self, file_info):
        """Log file change to monitoring log"""
        log_entry = {
            'timestamp': file_info['timestamp'],
            'event': f"{file_info['event_type'].upper()}: {file_info['file_name']}",
            'details': {
                'size': f"{file_info['file_size']} bytes",
                'type': file_info['file_extension']
            }
        }
        
        if 'record_count' in file_info:
            log_entry['details']['records'] = file_info['record_count']
        
        if 'data_source' in file_info:
            log_entry['details']['source'] = file_info['data_source']
        
        # Write to monitoring log file
        log_file = self.data_directory / 'monitoring_log.json'
        
        try:
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging.error(f"❌ Error writing to monitoring log: {str(e)}")
    
    def get_monitoring_stats(self):
        """Get monitoring statistics"""
        log_file = self.data_directory / 'monitoring_log.json'
        
        if not log_file.exists():
            return {
                'total_events': 0,
                'recent_events': [],
                'file_types': {},
                'data_sources': {}
            }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Calculate statistics
            stats = {
                'total_events': len(logs),
                'recent_events': logs[-10:] if logs else [],  # Last 10 events
                'file_types': {},
                'data_sources': {}
            }
            
            for log in logs:
                # Count file types
                file_type = log['details'].get('type', 'unknown')
                stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1
                
                # Count data sources
                data_source = log['details'].get('source', 'unknown')
                stats['data_sources'][data_source] = stats['data_sources'].get(data_source, 0) + 1
            
            return stats
            
        except Exception as e:
            logging.error(f"❌ Error reading monitoring stats: {str(e)}")
            return {'error': str(e)}

def start_monitoring(data_directory="./data", callback=None):
    """Start the file monitoring service"""
    event_handler = AzureDataMonitor(data_directory, callback)
    observer = Observer()
    observer.schedule(event_handler, str(event_handler.data_directory), recursive=True)
    
    observer.start()
    logging.info(f"🚀 Azure Data Monitor started successfully")
    logging.info(f"📡 Monitoring: {Path(data_directory).absolute()}")
    
    try:
        return observer, event_handler
    except Exception as e:
        logging.error(f"❌ Error starting monitor: {str(e)}")
        observer.stop()
        raise

def stop_monitoring(observer):
    """Stop the file monitoring service"""
    if observer:
        observer.stop()
        observer.join()
        logging.info("🛑 Azure Data Monitor stopped")

if __name__ == "__main__":
    # Example usage
    def data_change_callback(file_info):
        """Example callback function"""
        print(f"🔔 Data change detected: {file_info['file_name']} ({file_info['event_type']})")
        if 'record_count' in file_info:
            print(f"📊 Records: {file_info['record_count']}")
        if 'data_source' in file_info:
            print(f"🎯 Source: {file_info['data_source']}")
    
    # Start monitoring
    observer, monitor = start_monitoring("./data", data_change_callback)
    
    try:
        print("🔍 Monitoring started. Press Ctrl+C to stop...")
        print(f"📁 Drop files in the './data' directory to see monitoring in action")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping monitor...")
        stop_monitoring(observer)
