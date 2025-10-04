#!/bin/bash

# Start both backend and frontend for development

echo "🚀 Starting Space Bio Engine Development Environment"
echo "=================================================="

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Start backend
echo "📡 Starting Flask backend on port 5002..."
cd backend
python app_memory.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if curl -s http://127.0.0.1:5002/api/health > /dev/null; then
    echo "✅ Backend is running successfully"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend
echo "🌐 Starting Next.js frontend on port 3000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Development servers started!"
echo "   Backend:  http://127.0.0.1:5002"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait
