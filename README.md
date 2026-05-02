# Project Setup

## Python Environment

### Installed Packages
- **Flask 3.1.2** - Web framework
- **SQLAlchemy 2.0.46** - SQL toolkit and ORM

### Virtual Environment Commands
```bash
# Activate the virtual environment
venv\Scripts\activate

# Deactivate the virtual environment
deactivate

# Install dependencies (if cloning this project)
venv\Scripts\pip install -r requirements.txt
```

## React Setup

✅ **React app created** in the `frontend` folder

### Available React Commands:
```bash
cd frontend

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Quick Start

### Backend (Flask):
1. Activate the virtual environment: `venv\Scripts\activate`
2. Run the Flask app: `python app.py`
3. Backend will be available at `http://localhost:5050` (we use 5050 instead of the default 5000 because macOS AirPlay Receiver squats on port 5000)

### Frontend (React):
1. Navigate to frontend: `cd frontend`
2. Start development server: `npm start`
3. Open browser to `http://localhost:3000`

## Stage 1 - Hello World Demo

The project includes:
- ✅ `app.py` - Flask backend with hello world API endpoints
- ✅ `frontend/src/App.js` - React hello world page
- ✅ All dependencies installed and configured

## Tech Stack
- **Backend**: Python 3.13, Flask 3.1.2, SQLAlchemy 2.0.46
- **Frontend**: React (via Create React App)
- **Node.js**: v24.13.0
- **npm**: v11.6.2
