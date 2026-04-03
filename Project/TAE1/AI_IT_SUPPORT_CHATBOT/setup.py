"""
Setup Script for AI IT Support Chatbot
======================================
Handles initial setup, database initialization, and dependency installation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(step_num, total_steps, message):
    """Print step progress."""
    print(f"[{step_num}/{total_steps}] {message}")


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def create_directories():
    """Create necessary directories."""
    print("Creating project directories...")
    
    directories = [
        'logs',
        'database',
        'static/css',
        'static/js',
        'templates',
        'dialogflow'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created")


def install_dependencies():
    """Install Python dependencies."""
    print("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def initialize_database():
    """Initialize SQLite database."""
    print("Initializing database...")
    
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def create_env_file():
    """Create .env file from example if it doesn't exist."""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✓ Created .env file from .env.example")
            print("  Please update .env with your configuration")
        else:
            print("⚠ .env.example not found, skipping .env creation")
    else:
        print("✓ .env file already exists")


def test_chatbot_engine():
    """Test chatbot engine initialization."""
    print("Testing chatbot engine...")
    
    try:
        from chatbot_engine import ITSupportChatbot
        chatbot = ITSupportChatbot()
        
        # Test a simple query
        result = chatbot.get_response("internet not working")
        
        if result and 'response' in result:
            print("✓ Chatbot engine working")
            return True
        else:
            print("❌ Chatbot engine test failed")
            return False
    except Exception as e:
        print(f"❌ Failed to test chatbot engine: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("  Setup Complete! 🎉")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Update .env file with your configuration")
    print("  2. Run the application: python app.py")
    print("  3. Open browser and go to: http://localhost:5000")
    print("\nUseful commands:")
    print("  python app.py              # Start the server")
    print("  python chatbot_engine.py   # Test chatbot engine")
    print("  python database.py         # Test database")
    print("\nFor more information, see README.md")
    print("=" * 60 + "\n")


def main():
    """Main setup function."""
    print_header("AI IT Support Chatbot - Setup")
    
    total_steps = 6
    current_step = 0
    
    # Step 1: Check Python version
    current_step += 1
    print_step(current_step, total_steps, "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create directories
    current_step += 1
    print_step(current_step, total_steps, "Creating directories")
    create_directories()
    
    # Step 3: Install dependencies
    current_step += 1
    print_step(current_step, total_steps, "Installing dependencies")
    if not install_dependencies():
        print("\n⚠ Warning: Some dependencies failed to install.")
        print("  You may need to install them manually.")
    
    # Step 4: Initialize database
    current_step += 1
    print_step(current_step, total_steps, "Initializing database")
    if not initialize_database():
        print("\n⚠ Warning: Database initialization failed.")
        print("  The application will try to initialize it on first run.")
    
    # Step 5: Create .env file
    current_step += 1
    print_step(current_step, total_steps, "Creating environment file")
    create_env_file()
    
    # Step 6: Test chatbot engine
    current_step += 1
    print_step(current_step, total_steps, "Testing chatbot engine")
    if not test_chatbot_engine():
        print("\n⚠ Warning: Chatbot engine test failed.")
        print("  Please check the rules.json file.")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
