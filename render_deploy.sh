#!/bin/bash
# Render Deployment Script for AttendEase Backend
# This script helps prepare your application for Render deployment

echo "🚀 Preparing AttendEase Backend for Render Deployment"
echo "=================================================="

# Check if required files exist
echo "📋 Checking deployment files..."

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "❌ app.py not found!"
    exit 1
fi

echo "✅ All required files found!"

# Install dependencies locally to test
echo "📦 Testing local installation..."
pip install -r requirements.txt

echo "🎉 Ready for Render deployment!"
echo "Next steps:"
echo "1. Push your code to GitHub"
echo "2. Connect GitHub to Render"
echo "3. Create PostgreSQL database on Render"
echo "4. Create Web Service on Render"
echo "5. Configure environment variables"
