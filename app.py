from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import signal
import sys
import time
import os
from config import Config
from utils.audio_handler import AudioHandler
from utils.text_to_speech import TextToSpeech

# Try to import AI API providers - GeminiAPI or OpenRouterAPI
gemini_api = None
API_PROVIDER = None

try:
    from utils.gemini_api import GeminiAPI
    API_PROVIDER = "gemini"
except ImportError:
    try:
        from utils.openrouter_api import OpenRouterAPI
        API_PROVIDER = "openrouter" 
    except ImportError:
        API_PROVIDER = None

# Load API key from environment or fallback (first version had hardcoded fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyBljIYoGCRFHOPccj_Xpy5DaNPjvM7Qg5s"

# Ensure API key is available (second version had strict requirement)
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable must be set")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
config = Config()
audio_handler = None
tts = None
conversation_history = []

# Initialize AI client based on available provider
if API_PROVIDER == "gemini":
    try:
        gemini_api = GeminiAPI(GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to initialize GeminiAPI: {e}")
        gemini_api = None
elif API_PROVIDER == "openrouter":
    try:
        gemini_api = OpenRouterAPI(GEMINI_API_KEY)  
    except Exception as e:
        print(f"Failed to initialize OpenRouterAPI: {e}")
        gemini_api = None
else:
    print("Warning: No valid AI API provider found. Will initialize later.")
    gemini_api = None

# Enhanced HTML template with premium styling (from first version)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Voice Assistant Pro</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-dark: #0f0f23;
            --primary-blue: #1e40af;
            --secondary-purple: #7c3aed;
            --accent-cyan: #06b6d4;
            --accent-pink: #ec4899;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --glass-bg: rgba(255, 255, 255, 0.08);
            --glass-border: rgba(255, 255, 255, 0.12);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.8);
            --text-muted: rgba(255, 255, 255, 0.6);
            --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
            --shadow-xl: 0 35px 60px -15px rgba(0, 0, 0, 0.7);
            --glow-primary: 0 0 40px rgba(30, 64, 175, 0.4);
            --glow-accent: 0 0 30px rgba(236, 72, 153, 0.3);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: 
                radial-gradient(circle at 20% 20%, rgba(124, 58, 237, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(30, 64, 175, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 90%, rgba(236, 72, 153, 0.2) 0%, transparent 50%),
                linear-gradient(135deg, #0f0f23 0%, #1e1b4b 50%, #312e81 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow-x: hidden;
            position: relative;
        }

        /* Particle background animation */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            overflow: hidden;
        }

        .particle {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            animation: floatParticle linear infinite;
        }

        @keyframes floatParticle {
            0% {
                transform: translateY(0) translateX(0);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) translateX(var(--random-x));
                opacity: 0;
            }
        }

        /* Animated gradient background */
        .gradient-bg {
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg, 
                rgba(30, 64, 175, 0.1) 0%, 
                rgba(124, 58, 237, 0.1) 25%, 
                rgba(236, 72, 153, 0.1) 50%, 
                rgba(6, 182, 212, 0.1) 75%, 
                rgba(16, 185, 129, 0.1) 100%
            );
            background-size: 400% 400%;
            animation: gradientFlow 30s ease infinite;
            z-index: -1;
            opacity: 0.5;
        }

        @keyframes gradientFlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Main container with enhanced glassmorphism */
        .container {
            background: var(--glass-bg);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--glass-border);
            border-radius: 30px;
            padding: 2.5rem;
            width: 100%;
            max-width: 800px; /* Wider for laptop */
            box-shadow: var(--shadow-xl);
            position: relative;
            overflow: hidden;
            animation: containerPulse 8s ease-in-out infinite;
            transform-style: preserve-3d;
            perspective: 1000px;
        }

        @keyframes containerPulse {
            0%, 100% { 
                transform: translateY(0px);
                box-shadow: var(--shadow-xl);
            }
            50% { 
                transform: translateY(-8px);
                box-shadow: var(--shadow-xl), var(--glow-primary);
            }
        }

        /* Animated border gradient */
        .container::before {
            content: '';
            position: absolute;
            inset: 0;
            padding: 2px;
            background: linear-gradient(135deg, 
                var(--primary-blue), 
                var(--secondary-purple), 
                var(--accent-pink), 
                var(--accent-cyan)
            );
            border-radius: inherit;
            mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask-composite: exclude;
            -webkit-mask-composite: xor;
            animation: borderRotate 10s linear infinite;
            z-index: -1;
        }

        @keyframes borderRotate {
            0% { 
                filter: hue-rotate(0deg);
                background-position: 0% 0%;
            }
            100% { 
                filter: hue-rotate(360deg);
                background-position: 100% 100%;
            }
        }

        /* Header styling */
        .header {
            text-align: center;
            margin-bottom: 2.5rem;
            position: relative;
            z-index: 10;
        }

        .header h1 {
            background: linear-gradient(135deg, var(--text-primary), var(--accent-cyan), var(--accent-pink));
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.8rem;
            font-weight: 900;
            margin-bottom: 0.8rem;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
            animation: gradientText 6s ease-in-out infinite;
        }

        @keyframes gradientText {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        .header p {
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 500;
            opacity: 0.9;
        }

        .header .icon {
            font-size: 1.5rem;
            margin-right: 0.8rem;
            background: linear-gradient(45deg, var(--accent-cyan), var(--accent-pink));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: iconPulse 3s ease-in-out infinite;
        }

        @keyframes iconPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        /* Enhanced chat container */
        .chat-container {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 25px;
            padding: 2rem;
            margin-bottom: 2.5rem;
            max-height: 350px;
            min-height: 220px;
            overflow-y: auto;
            scroll-behavior: smooth;
            position: relative;
            box-shadow: inset 0 2px 20px rgba(0, 0, 0, 0.3);
        }

        .chat-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 3s linear infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .chat-container::-webkit-scrollbar {
            width: 8px;
        }

        .chat-container::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }

        .chat-container::-webkit-scrollbar-thumb {
            background: linear-gradient(45deg, var(--primary-blue), var(--secondary-purple));
            border-radius: 10px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }

        .chat-container::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(45deg, var(--accent-cyan), var(--accent-pink));
        }

        /* Enhanced message styling */
        .message {
            margin: 1.5rem 0;
            padding: 1.5rem 2rem;
            border-radius: 25px;
            max-width: 85%;
            font-size: 0.95rem;
            font-weight: 500;
            line-height: 1.6;
            word-wrap: break-word;
            animation: messageSlideIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transform-origin: center;
        }

        @keyframes messageSlideIn {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.8) rotateX(90deg);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1) rotateX(0deg);
            }
        }

        .user-message {
            background: linear-gradient(135deg, 
                rgba(30, 64, 175, 0.7) 0%, 
                rgba(124, 58, 237, 0.7) 100%
            );
            color: var(--text-primary);
            margin-left: auto;
            text-align: right;
            box-shadow: 0 10px 30px rgba(30, 64, 175, 0.3), var(--glow-primary);
            border-left: 3px solid var(--accent-cyan);
        }

        .user-message::before {
            content: '';
            position: absolute;
            right: -10px;
            top: 50%;
            transform: translateY(-50%);
            width: 0;
            height: 0;
            border-left: 10px solid rgba(30, 64, 175, 0.7);
            border-top: 10px solid transparent;
            border-bottom: 10px solid transparent;
        }

        .ai-message {
            background: linear-gradient(135deg, 
                rgba(236, 72, 153, 0.6) 0%, 
                rgba(16, 185, 129, 0.6) 100%
            );
            color: var(--text-primary);
            box-shadow: 0 10px 30px rgba(236, 72, 153, 0.3), var(--glow-accent);
            border-left: 3px solid var(--accent-green);
        }

        .ai-message::before {
            content: '';
            position: absolute;
            left: -10px;
            top: 50%;
            transform: translateY(-50%);
            width: 0;
            height: 0;
            border-right: 10px solid rgba(236, 72, 153, 0.6);
            border-top: 10px solid transparent;
            border-bottom: 10px solid transparent;
        }

        .message .icon {
            margin-right: 0.8rem;
            font-size: 1.1rem;
            opacity: 0.9;
        }

        /* Enhanced controls grid */
        .controls {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.2rem;
            margin-bottom: 2.5rem;
        }

        /* Premium button styling */
        .btn {
            padding: 1.3rem 1.8rem;
            border: none;
            border-radius: 20px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            transform-style: preserve-3d;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.6s;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn:hover {
            transform: translateY(-5px) scale(1.05);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }

        .btn:active {
            transform: translateY(-2px) scale(1.02);
        }

        .btn-record {
            background: linear-gradient(135deg, var(--accent-green), var(--accent-cyan));
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
        }

        .btn-record:hover {
            box-shadow: 0 20px 40px rgba(16, 185, 129, 0.6), 0 0 30px var(--accent-green);
        }

        .btn-stop {
            background: linear-gradient(135deg, #ef4444, var(--accent-pink));
            box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
        }

        .btn-stop:hover {
            box-shadow: 0 20px 40px rgba(239, 68, 68, 0.6), 0 0 30px #ef4444;
        }

        .btn-mute {
            background: linear-gradient(135deg, var(--secondary-purple), var(--primary-blue));
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        }

        .btn-mute:hover {
            box-shadow: 0 20px 40px rgba(124, 58, 237, 0.6), 0 0 30px var(--secondary-purple);
        }

        .btn-clear {
            background: linear-gradient(135deg, #6b7280, #374151);
            box-shadow: 0 8px 25px rgba(107, 114, 128, 0.4);
        }

        .btn-clear:hover {
            box-shadow: 0 20px 40px rgba(107, 114, 128, 0.6), 0 0 30px #6b7280;
        }

        .btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            transform: none;
        }

        .btn:disabled:hover {
            transform: none;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }

        /* Enhanced status indicators */
        .status {
            text-align: center;
            padding: 1.5rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            font-weight: 700;
            font-size: 1.1rem;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .status::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: statusShimmer 2s linear infinite;
        }

        @keyframes statusShimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        .status.recording {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(239, 68, 68, 0.3));
            color: #fbbf24;
            border-color: rgba(245, 158, 11, 0.5);
            box-shadow: 0 0 30px rgba(245, 158, 11, 0.3);
        }

        .status.processing {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.3), rgba(30, 64, 175, 0.3));
            color: #06b6d4;
            border-color: rgba(6, 182, 212, 0.5);
            box-shadow: 0 0 30px rgba(6, 182, 212, 0.3);
        }

        .status.speaking {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(34, 197, 94, 0.3));
            color: #10b981;
            border-color: rgba(16, 185, 129, 0.5);
            box-shadow: 0 0 30px rgba(16, 185, 129, 0.3);
        }

        /* Enhanced text input */
        .text-input {
            width: 100%;
            padding: 1.5rem 2rem;
            border: 2px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            font-size: 1.05rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
            resize: vertical;
            min-height: 100px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
            backdrop-filter: blur(15px);
            transition: all 0.4s ease;
            font-family: inherit;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.2);
        }

        .text-input::placeholder {
            color: var(--text-muted);
            font-weight: 400;
        }

        .text-input:focus {
            outline: none;
            border-color: var(--accent-cyan);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 
                inset 0 2px 10px rgba(0, 0, 0, 0.2),
                0 0 25px rgba(6, 182, 212, 0.4),
                0 0 50px rgba(6, 182, 212, 0.2);
            transform: scale(1.02);
        }

        .send-btn {
            width: 100%;
            background: linear-gradient(135deg, var(--primary-blue), var(--secondary-purple), var(--accent-pink));
            background-size: 300% 300%;
            margin-bottom: 2.5rem;
            font-size: 1.1rem;
            padding: 1.5rem;
            animation: gradientShift 8s ease infinite;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .send-btn:hover {
            animation-duration: 2s;
        }

        /* Enhanced recording indicator */
        .recording-indicator {
            display: none;
            text-align: center;
            margin: 2rem 0;
            color: var(--text-primary);
            font-weight: 700;
            font-size: 1.1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .recording-dot {
            width: 16px;
            height: 16px;
            background: linear-gradient(45deg, #ef4444, #f97316);
            border-radius: 50%;
            display: inline-block;
            margin-right: 1rem;
            animation: recordingPulse 1.5s ease-in-out infinite;
            box-shadow: 0 0 20px #ef4444, 0 0 40px #f97316;
        }

        @keyframes recordingPulse {
            0%, 100% { 
                opacity: 1; 
                transform: scale(1);
                box-shadow: 0 0 20px #ef4444, 0 0 40px #f97316;
            }
            50% { 
                opacity: 0.3; 
                transform: scale(1.4);
                box-shadow: 0 0 30px #ef4444, 0 0 60px #f97316;
            }
        }

        /* Enhanced footer */
        .footer {
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 400;
            opacity: 0.8;
        }

        .footer .icon {
            margin: 0 0.3rem;
            color: var(--accent-cyan);
        }

        /* Responsive enhancements */
        @media (max-width: 900px) {
            .container {
                max-width: 700px;
            }
            
            .controls {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 768px) {
            .container {
                max-width: 600px;
                padding: 2rem;
            }
            
            .header h1 {
                font-size: 2.4rem;
            }
            
            .chat-container {
                max-height: 300px;
            }
        }

        @media (max-width: 640px) {
            .container {
                max-width: 500px;
                padding: 1.8rem;
            }
            
            .header h1 {
                font-size: 2.2rem;
            }
            
            .controls {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .btn {
                padding: 1.2rem;
                font-size: 0.95rem;
            }
            
            .chat-container {
                max-height: 280px;
                padding: 1.5rem;
            }
            
            .message {
                padding: 1.2rem 1.5rem;
                border-radius: 20px;
            }
        }

        @media (max-height: 750px) {
            .chat-container {
                max-height: 250px;
                min-height: 180px;
            }
            
            .container {
                padding: 2rem;
            }
        }

        /* Smooth page transitions */
        .page-transition {
            animation: pageLoad 1s ease-out;
        }

        @keyframes pageLoad {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        /* Enhanced loading states */
        .loading-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <!-- Animated background elements -->
    <div class="gradient-bg"></div>
    <div class="particles" id="particles"></div>
    
    <div class="container page-transition">
        <div class="header">
            <h1><i class="fas fa-microphone-alt icon"></i>AI Voice Assistant Pro</h1>
            <p>Experience the future of voice interaction</p>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message ai-message">
                <i class="fas fa-robot icon"></i>Welcome to the future! I'm your advanced AI voice assistant. Click "Start Recording" to speak with me, or type your message below. Let's create something amazing together! ✨
            </div>
        </div>
        
        <div class="controls">
            <button id="startRecording" class="btn btn-record">
                <i class="fas fa-microphone"></i> Start Recording
            </button>
            <button id="stopRecording" class="btn btn-stop" disabled>
                <i class="fas fa-stop-circle"></i> Stop Recording
            </button>
            <button id="stopSpeaking" class="btn btn-mute">
                <i class="fas fa-volume-mute"></i> Stop Speaking
            </button>
            <button id="clearChat" class="btn btn-clear">
                <i class="fas fa-trash-alt"></i> Clear Chat
            </button>
        </div>
        
        <div class="recording-indicator" id="recordingIndicator">
            <div class="recording-dot"></div>
            <span>Recording in progress...</span>
        </div>
        
        <textarea id="textInput" class="text-input" placeholder="Type your message here and press Enter..."></textarea>
        <button id="sendText" class="btn send-btn">
            <i class="fas fa-paper-plane"></i> Send Message
        </button>
        
        <div class="footer">
            <p><i class="fas fa-sparkles icon"></i>Powered by Gemini AI<i class="fas fa-brain icon"></i>Speech Recognition<i class="fas fa-volume-up icon"></i>Text-to-Speech</p>
        </div>
    </div>

    <script>
        let isRecording = false;
        let isProcessing = false;

        // Create particle background
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const particleCount = 30;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.classList.add('particle');
                
                // Random properties
                const size = Math.random() * 5 + 2;
                const posX = Math.random() * 100;
                const posY = Math.random() * 100 + 100;
                const duration = Math.random() * 20 + 10;
                const delay = Math.random() * -20;
                const opacity = Math.random() * 0.5 + 0.1;
                const randomX = (Math.random() - 0.5) * 100;
                
                particle.style.width = `${size}px`;
                particle.style.height = `${size}px`;
                particle.style.left = `${posX}%`;
                particle.style.top = `${posY}%`;
                particle.style.opacity = opacity;
                particle.style.animationDuration = `${duration}s`;
                particle.style.animationDelay = `${delay}s`;
                particle.style.setProperty('--random-x', `${randomX}px`);
                
                particlesContainer.appendChild(particle);
            }
        }

        // Initialize particles
        createParticles();

        const startRecordingBtn = document.getElementById('startRecording');
        const stopRecordingBtn = document.getElementById('stopRecording');
        const stopSpeakingBtn = document.getElementById('stopSpeaking');
        const clearChatBtn = document.getElementById('clearChat');
        const sendTextBtn = document.getElementById('sendText');
        const textInput = document.getElementById('textInput');
        const chatContainer = document.getElementById('chatContainer');
        const status = document.getElementById('status');
        const recordingIndicator = document.getElementById('recordingIndicator');

        function showStatus(message, type) {
            status.innerHTML = `<i class="fas fa-circle"></i> ${message}`;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }

        function hideStatus() {
            status.style.display = 'none';
        }

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            messageDiv.innerHTML = `<i class="fas fa-${isUser ? 'user' : 'robot'} icon"></i>${content}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function setRecordingState(recording) {
            isRecording = recording;
            startRecordingBtn.disabled = recording || isProcessing;
            stopRecordingBtn.disabled = !recording;
            recordingIndicator.style.display = recording ? 'block' : 'none';
            
            if (recording) {
                showStatus('🎤 Listening... Speak now!', 'recording');
            }
        }

        function setProcessingState(processing) {
            isProcessing = processing;
            startRecordingBtn.disabled = processing || isRecording;
            sendTextBtn.disabled = processing;
            
            if (processing) {
                showStatus('🧠 Processing your message...', 'processing');
                sendTextBtn.classList.add('loading-pulse');
            } else {
                sendTextBtn.classList.remove('loading-pulse');
            }
        }

        // Event Listeners
        startRecordingBtn.addEventListener('click', async () => {
            try {
                setRecordingState(true);
                const response = await fetch('/start_recording', { method: 'POST' });
                const data = await response.json();
                
                if (!data.success) {
                    alert('Failed to start recording: ' + data.error);
                    setRecordingState(false);
                    hideStatus();
                }
            } catch (error) {
                console.error('Error starting recording:', error);
                alert('Error starting recording');
                setRecordingState(false);
                hideStatus();
            }
        });

        stopRecordingBtn.addEventListener('click', async () => {
            try {
                setRecordingState(false);
                setProcessingState(true);
                
                const response = await fetch('/stop_recording', { method: 'POST' });
                const data = await response.json();
                
                if (data.success && data.transcribed_text) {
                    addMessage(data.transcribed_text, true);
                    
                    if (data.ai_response) {
                        showStatus('🔊 Speaking response...', 'speaking');
                        addMessage(data.ai_response, false);
                        
                        setTimeout(() => {
                            hideStatus();
                        }, 3000);
                    }
                } else {
                    alert('Failed to process recording: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error stopping recording:', error);
                alert('Error processing recording');
            } finally {
                setProcessingState(false);
            }
        });

        sendTextBtn.addEventListener('click', async () => {
            const text = textInput.value.trim();
            if (!text) return;
            
            try {
                setProcessingState(true);
                addMessage(text, true);
                textInput.value = '';
                
                const response = await fetch('/send_text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                
                const data = await response.json();
                
                if (data.success && data.ai_response) {
                    showStatus('🔊 Speaking response...', 'speaking');
                    addMessage(data.ai_response, false);
                    
                    setTimeout(() => {
                        hideStatus();
                    }, 3000);
                } else {
                    alert('Failed to get AI response: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error sending text:', error);
                alert('Error sending message');
            } finally {
                setProcessingState(false);
            }
        });

        stopSpeakingBtn.addEventListener('click', async () => {
            try {
                await fetch('/stop_speaking', { method: 'POST' });
                hideStatus();
            } catch (error) {
                console.error('Error stopping speech:', error);
            }
        });

        clearChatBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to clear the chat history?')) {
                try {
                    await fetch('/clear_history', { method: 'POST' });
                    chatContainer.innerHTML = `
                        <div class="message ai-message">
                            <i class="fas fa-robot icon"></i>Welcome back! I'm your advanced AI voice assistant. Click "Start Recording" to speak with me, or type your message below. Let's create something amazing together! ✨
                        </div>
                    `;
                    hideStatus();
                } catch (error) {
                    console.error('Error clearing chat:', error);
                }
            }
        });

        // Enhanced keyboard interactions
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendTextBtn.click();
            }
        });

        // Auto-resize textarea
        textInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });

        // Enhanced visual feedback
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                if (!btn.disabled) {
                    btn.style.filter = 'brightness(1.1)';
                }
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.filter = 'brightness(1)';
            });
        });

        // Initialize
        hideStatus();
        console.log('🚀 Enhanced AI Voice Assistant Pro initialized successfully!');
    </script>
</body>
</html>
"""

def initialize_components():
    """Initialize all application components."""
    global audio_handler, gemini_api, tts

    try:
        print("Initializing Voice Chatbot...")

        # Validate configuration
        config.validate_config()

        # Initialize components
        print("Initializing audio handler...")
        audio_handler = AudioHandler()

        print("Initializing AI API...")
        if API_PROVIDER == "gemini" and gemini_api is None:
            gemini_api = GeminiAPI(api_key=GEMINI_API_KEY)
        elif API_PROVIDER == "openrouter" and gemini_api is None:
            gemini_api = OpenRouterAPI(api_key=GEMINI_API_KEY)
        elif gemini_api is None:
            raise RuntimeError("No valid AI API provider available")

        print("Initializing Text-to-Speech...")
        tts = TextToSpeech()

        # Test connections
        print("Testing AI API connection...")
        test_result = gemini_api.test_connection()
        print(test_result)
        if "successful" in test_result:
            print("✓ All components initialized successfully!")
        else:
            print("⚠ Warning: AI API connection test failed")

        return True

    except Exception as e:
        print(f"✗ Error initializing components: {e}")
        return False

def cleanup_components():
    """Clean up all components on shutdown."""
    global audio_handler, tts

    print("Cleaning up components...")

    if audio_handler:
        audio_handler.cleanup()

    if tts:
        tts.cleanup()

    print("Cleanup completed.")

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print("\nShutting down gracefully...")
    cleanup_components()
    sys.exit(0)

@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_recording', methods=['POST'])
def start_recording():
    """Start audio recording."""
    try:
        if audio_handler.start_recording():
            return jsonify({'success': True, 'message': 'Recording started'})
        else:
            return jsonify({'success': False, 'error': 'Already recording'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    """Stop recording and process the audio."""
    global conversation_history
    try:
        audio_file = audio_handler.stop_recording()
        if not audio_file:
            return jsonify({'success': False, 'error': 'No audio recorded'})

        transcribed_text = audio_handler.transcribe_audio(audio_file)
        if not transcribed_text:
            return jsonify({'success': False, 'error': 'Could not transcribe audio'})

        # Check AI client initialized before use (from second version)
        if gemini_api is None:
            raise RuntimeError("AI API client is not initialized")

        ai_response = gemini_api.generate_response(transcribed_text, conversation_history=conversation_history)

        conversation_history.append({"role": "user", "content": transcribed_text})
        conversation_history.append({"role": "assistant", "content": ai_response})

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        if ai_response:
            tts.speak(ai_response)

        return jsonify({
            'success': True,
            'transcribed_text': transcribed_text,
            'ai_response': ai_response
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_text', methods=['POST'])
def send_text():
    """Process text input and generate AI response."""
    global conversation_history
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})

        # Check AI client initialized before use (from second version)
        if gemini_api is None:
            raise RuntimeError("AI API client is not initialized")

        ai_response = gemini_api.generate_response(text, conversation_history=conversation_history)

        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": ai_response})

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        if ai_response:
            tts.speak(ai_response)

        return jsonify({
            'success': True,
            'ai_response': ai_response
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_speaking', methods=['POST'])
def stop_speaking():
    """Stop text-to-speech playback."""
    try:
        tts.stop_speaking()
        return jsonify({'success': True, 'message': 'Speech stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear conversation history."""
    global conversation_history
    try:
        conversation_history = []
        return jsonify({'success': True, 'message': 'History cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status')
def get_status():
    """Get current application status."""
    return jsonify({
        'recording': audio_handler.is_recording if audio_handler else False,
        'speaking': tts.is_busy() if tts else False,
        'conversation_length': len(conversation_history),
        'components_initialized': all([audio_handler, gemini_api, tts])
    })

@app.route('/model_info')
def get_model_info():
    """Get AI model info."""
    try:
        if gemini_api is None:
            return jsonify({'success': False, 'error': 'AI API client not initialized'})
        
        info = gemini_api.get_model_info(gemini_api.model)
        return jsonify({'success': True, 'model_info': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Example Gemini API payload (from first version)
payload = {
    "contents": [
        {
            "role": "user",
            "parts": [
                {"text": "Your prompt here"}
            ]
        }
    ]
}

def run_console_mode():
    """Run the application in console mode."""
    print("\n" + "="*50)
    print("VOICE CHATBOT PRO - CONSOLE MODE")
    print("="*50)
    print("Commands:")
    print("  'voice' - Record and send voice message")
    print("  'text' - Send text message")
    print("  'quit' - Exit the application")
    print("="*50 + "\n")

    try:
        while True:
            command = input("\nEnter command (voice/text/quit): ").strip().lower()

            if command == 'quit':
                break
            elif command == 'voice':
                print("\nStarting voice recording...")
                transcribed_text = audio_handler.record_and_transcribe()

                if transcribed_text:
                    print(f"You said: {transcribed_text}")

                    ai_response = gemini_api.generate_response(
                        transcribed_text,
                        conversation_history=conversation_history
                    )

                    if ai_response:
                        print(f"AI: {ai_response}")

                        conversation_history.append({"role": "user", "content": transcribed_text})
                        conversation_history.append({"role": "assistant", "content": ai_response})

                        tts.speak(ai_response, blocking=True)
                else:
                    print("No speech detected or transcription failed.")

            elif command == 'text':
                text = input("Enter your message: ").strip()
                if text:
                    ai_response = gemini_api.generate_response(
                        text,
                        conversation_history=conversation_history
                    )

                    if ai_response:
                        print(f"AI: {ai_response}")

                        conversation_history.append({"role": "user", "content": text})
                        conversation_history.append({"role": "assistant", "content": ai_response})

                        tts.speak(ai_response, blocking=True)
            else:
                print("Invalid command. Use 'voice', 'text', or 'quit'.")

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error in console mode: {e}")

if __name__ == '__main__':
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize components
    if not initialize_components():
        print("Failed to initialize components. Exiting.")
        sys.exit(1)

    # Check if running in web mode or console mode
    if len(sys.argv) > 1 and sys.argv[1] == 'console':
        run_console_mode()
    else:
        print(f"\n🚀 Starting Enhanced Voice Chatbot Pro Web Server...")
        print(f"🎨 Features: Premium UI, Advanced Animations, Glassmorphism Design")
        print(f"📱 Open your browser and go to: http://localhost:5000")
        print(f"🎤 You can speak or type messages to interact with the AI")
        print(f"⌨️  Or run 'python app.py console' for console mode")
        print(f"🛑 Press Ctrl+C to stop the server\n")
        
        try:
            app.run(
                host='0.0.0.0',
                port=5000,
                debug=config.DEBUG,
                threaded=True,
                use_reloader=False  # Disable reloader to prevent component re-initialization issues
            )
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            cleanup_components()
