#!/bin/bash

# Paris 2026 Marathon Tracker - Start Script

echo "🇫🇷 Starting Paris 2026 Marathon Tracker..."
echo ""

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Setting up backend..."
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check if database exists
if [ ! -f "data/marathon.db" ]; then
    echo "📊 Importing training plan..."
    source backend/venv/bin/activate
    python scripts/import_plan.py
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "🚀 Starting servers..."
echo ""

# Start backend
echo "🔧 Starting backend on http://localhost:8000..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Start frontend
echo "🎨 Starting frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✨ Paris 2026 Marathon Tracker is running!"
echo ""
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
