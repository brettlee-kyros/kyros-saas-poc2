[![Unit Tests](https://github.com/kyrosinsights/mixshift/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/kyrosinsights/mixshift/actions/workflows/unit-tests.yml)
# MixShift Dashboard

A comprehensive analytics dashboard for actuaries to identify mix shifts driving trends in triangles across different temporal dimensions. Built with Dash, Redis caching, and Databricks integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## 🔍 Overview

The MixShift dashboard helps actuaries quickly identify if mix shifts are driving trends in triangles across three different mix types:

1. **Snapshot Date Mix** - How distributions change between two Snapshot Dates
2. **Earn Month Mix** - How distributions change between two Earn Months  
3. **Join Month Mix** - How distributions change between two Join Months

The application uses KL Divergence to rank characteristics by the magnitude of their mix shift, providing statistical insights into distribution changes over time.

## ✨ Key Features

- **Interactive Data Exploration**: Dynamic segment and variable bubblers with AG-Grid integration
- **Statistical Analysis**: KL Divergence calculations for distribution comparison
- **Multiple Visualization Types**: Histogram and 100% stacked chart views
- **Real-time Caching**: Redis-powered caching for optimal performance
- **Databricks Integration**: Direct connection to enterprise data warehouse
- **Responsive Design**: Modern UI with Dash Design Kit and Mantine components
- **Comprehensive Testing**: Full test suite with pytest integration

## 🏗️ Architecture

### Core Components

- **Frontend**: Dash with Bootstrap, Mantine, and Design Kit components
- **Backend**: Flask server with Gunicorn for production
- **Caching**: Redis for performance optimization
- **Database**: Databricks SQL Connector for data access

### Data Flow

1. User selects dataset → Application fetches metadata from Redis
2. Weight and date options populated based on mix type
3. Segment bubbler shows available segments with weight calculations
4. Variable bubbler displays variables ranked by KL divergence
5. Distribution visualization updates based on selections

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.10+** (specified in project.toml)
- **Redis Server** (for caching)
- **Git** (for version control)
- **Databricks Access** (for data connections)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd mix-shift-dashboard
```

### 2. Install Kyros Common Library

Clone the required common library:

```bash
git clone https://kyrosinsights@dev.azure.com/kyrosinsights/Client%20Dash/_git/kyros-plotly-common kyros_plotly_common
```

### 3. Set Up Python Environment

Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing and development)
pip install -r requirements-dev.txt
```

### 5. Install and Configure Redis

#### Windows (using Chocolatey)
```bash
choco install redis-64
redis-server
```

#### Windows (using WSL2)
```bash
wsl --install
# In WSL2 terminal:
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

#### macOS (using Homebrew)
```bash
brew install redis
brew services start redis
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Verify Redis Installation
```bash
redis-cli ping
# Should return: PONG
```

### 6. Environment Configuration

Create a `.env` file in the project root:

```bash
ACCESS_TOKEN=dapi1234567890
DBX_SERVER_HOSTNAME=adb-1234567890.azuredatabricks.net
DBX_WAREHOUSE_HTTP_PATH=/sql/1.0/warehouses/1234567890
```

## 🏃‍♂️ Running the Application

### Development Mode

```bash
# Ensure Redis is running
redis-server

# In another terminal, run the application
python app.py
```

The application will be available at `http://localhost:port`

### Production Mode

```bash
# Using Gunicorn (as specified in Procfile)
gunicorn app:server --workers 4 --bind 0.0.0.0:8000
```

## 🛠️ Development

### Code Structure

The application follows a modular architecture:

- **`app.py`** - Main application entry point and layout
- **`pages/`** - Page-specific callbacks and logic
- **`utils/`** - Utility functions and helpers
- **`tests/`** - Comprehensive test suite
- **`kyros_plotly_common/`** - Shared components library

### Key Utilities

- **`utils/dbx_utils.py`** - Database connection and query functions
- **`utils/viz_functions.py`** - Visualization and chart generation
- **`utils/bubbler_functions.py`** - Interactive bubbler components
- **`utils/catalog_initializer.py`** - Metadata initialization
- **`utils/ui_helpers.py`** - UI component helpers

### Development Workflow

1. **Start Redis**: `redis-server`
2. **Run Tests**: `pytest`
3. **Start Application**: `python app.py`
4. **Code Changes**: Hot reload enabled in debug mode
5. **Run Linting**: Follow project code standards

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_mixshift_catalog_initializer.py

# Run with verbose output
pytest -v

# Run integration tests (requires browser)
pytest -m integration
```

### Test Categories

- **Unit Tests**: Individual function testing
- **Integration Tests**: Component interaction testing
- **UI Tests**: Interface and callback testing

### Test Configuration

Tests are configured in `pytest.ini` with:
- Logging enabled for debugging
- Integration test markers
- Verbose output options

## 🚀 Deployment

### Local Deployment

The application is configured for deployment with:

- **Procfile**: Gunicorn configuration for production
- **requirements.txt**: Production dependencies
- **project.toml**: Build configuration

### Dash Enterprise Deployment

1. Initialize your app on Dash Enterprise
2. Follow the [deployment documentation](https://plotly.kyrosinsights.com/docs/dash-enterprise/deployment)
3. Ensure Redis is configured in your deployment environment

## ⚙️ Configuration

### Redis Configuration

The application uses Redis for caching with the following default settings:

```python
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": "redis://127.0.0.1:6379",
    "CACHE_DEFAULT_TIMEOUT": 3 * 60 * 60  # 3 hours
}
```

### Database Configuration

Databricks connection is configured through environment variables and the `databricks_sql_connector`.

### UI Theme Configuration

The application uses a custom theme with responsive breakpoints:

```python
theme = {
    "breakpoint_font": "1300px",
    "breakpoint_stack_blocks": "500px",
    "font_size": "15px",
    "font_size_smaller_screen": "12px",
    "font_size_header": "18px"
}
```

## 🔧 Troubleshooting

### Common Issues

#### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server

# Check Redis logs
redis-cli monitor
```

### Logging

Application logs are available in the `logs/` directory.

## 📚 Additional Resources

- [MixShift Development Documentation](MIXSHIFT_DEV_DOCS.md)
- [MixShift User Guide](MIXSHIFT_USER_GUIDE.md)
- [Dash Documentation](https://dash.plotly.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Databricks SQL Connector](https://docs.databricks.com/dev-tools/python-sql-connector.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

## 📝 License

This project is proprietary software owned by Kyros Insights. All rights reserved.

---

For questions or support, please contact the development team or refer to the internal documentation.
