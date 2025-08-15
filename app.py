import os
import threading
import time
from flask import Flask, render_template_string, request, redirect, url_for, jsonify, send_from_directory
import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta
import math
from werkzeug.utils import secure_filename
import uuid
import webbrowser
from rev import *

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = ''
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
Cloud_Auth = {}
SETTINGS_FILE = 'cloud_settings.json'
ADMIN_PASSWORD = 'obi123'  # Cambia esto en producción

# Estructura para manejar las descargas
downloads = {}
sids = []

# Asegurar que la carpeta de descargas existe
#os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# HTML Template
INDEX_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neon Downloader</title>
    <style>
        :root {
    --primary: #0f172a;
    --primary-light: #1e293b;
    --primary-lighter: #334155;
    --accent: #38bdf8;
    --accent-dark: #0ea5e9;
    --text: #e2e8f0;
    --text-light: #f8fafc;
    --text-muted: #94a3b8;
    --danger: #ef4444;
    --success: #10b981;
    --warning: #f59e0b;
    --background: #0f172a;
    --card-bg: rgba(15, 23, 42, 0.8);
    --progress-bg: rgba(30, 41, 59, 0.5);
    --glass-effect: rgba(30, 41, 59, 0.3);
    --admin-accent: #8b5cf6;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

body {
    background: linear-gradient(135deg, var(--primary), var(--primary-light));
    min-height: 100vh;
    color: var(--text);
    line-height: 1.6;
}

/* Auth Overlay */
.auth-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    z-index: 3000;
    display: flex;
    justify-content: center;
    align-items: center;
}

.auth-box {
    background: var(--primary-light);
    border-radius: 16px;
    padding: 30px;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    border: 1px solid var(--glass-effect);
    text-align: center;
    animation: fadeIn 0.4s ease-out;
}

.auth-title {
    color: var(--accent);
    margin-bottom: 25px;
    font-size: 24px;
}

.auth-input {
    width: 100%;
    padding: 14px;
    margin-bottom: 20px;
    background: var(--primary);
    border: 1px solid var(--primary-lighter);
    border-radius: 8px;
    color: var(--text-light);
    font-size: 16px;
    transition: border-color 0.3s;
}

.auth-input:focus {
    outline: none;
    border-color: var(--accent);
}

.auth-btn {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, var(--accent), var(--accent-dark));
    color: var(--primary);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
}

.auth-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(56, 189, 248, 0.3);
}

.auth-error {
    color: var(--danger);
    margin-top: 15px;
    font-size: 14px;
    display: none;
}

/* Main Container */
.container {
    background: var(--card-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    width: 100%;
    max-width: 700px;
    padding: 40px;
    text-align: center;
    border: 1px solid var(--glass-effect);
    animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    overflow: hidden;
    position: relative;
    margin: 20px auto;
    display: none;
}

h1 {
    color: var(--text-light);
    margin-bottom: 30px;
    font-weight: 700;
    font-size: 28px;
    letter-spacing: -0.5px;
    position: relative;
    display: inline-block;
}

h1::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
    border-radius: 2px;
}

.input-group {
    display: flex;
    margin-bottom: 25px;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    transition: transform 0.3s, box-shadow 0.3s;
}

.input-group:focus-within {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.25);
}

.url-input {
    flex: 1;
    padding: 16px 20px;
    border: none;
    font-size: 16px;
    outline: none;
    background: var(--primary-light);
    color: var(--text-light);
    border: 1px solid var(--primary-lighter);
}

.url-input::placeholder {
    color: var(--text-muted);
    opacity: 0.8;
}

.btn {
    padding: 16px 28px;
    border: none;
    background: linear-gradient(135deg, var(--accent), var(--accent-dark));
    color: var(--primary);
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
}

.btn::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(56, 189, 248, 0.3);
}

.btn:hover::after {
    opacity: 1;
}

.btn:disabled {
    background: var(--primary-lighter);
    color: var(--text-muted);
    cursor: not-allowed;
    transform: none !important;
    box-shadow: none !important;
}

.btn-secondary {
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
    margin-top: 15px;
}

.btn-secondary:hover {
    background: rgba(56, 189, 248, 0.1);
    box-shadow: 0 5px 15px rgba(56, 189, 248, 0.1);
}

.progress-container {
    margin-top: 40px;
    display: none;
    animation: fadeIn 0.6s forwards;
}

.progress-section {
    margin-bottom: 30px;
    background: var(--progress-bg);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--primary-lighter);
}

.progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    align-items: center;
}

.progress-title {
    font-weight: 600;
    color: var(--text-light);
    margin-bottom: 5px;
    text-align: left;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.progress-title::before {
    content: '';
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 10px var(--accent);
}

.filename {
    font-weight: 500;
    color: var(--text-light);
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    flex: 1;
    text-align: left;
    font-size: 15px;
}

.file-size {
    color: var(--text-muted);
    font-size: 14px;
    margin-left: 15px;
    white-space: nowrap;
}

.progress-bar {
    height: 8px;
    background: var(--primary-light);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 15px;
    position: relative;
}

.progress-bar::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    animation: pulse 2s infinite;
}

.progress {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-dark));
    width: 0%;
    transition: width 0.4s ease-out;
    position: relative;
    z-index: 2;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 5px;
}

.progress-percent {
    font-weight: 600;
    color: var(--accent);
}

.speed {
    color: var(--text-light);
    display: flex;
    align-items: center;
    gap: 4px;
}

.speed::before {
    content: '⬇️';
    font-size: 12px;
}

.upload-speed::before {
    content: '⬆️';
}

.eta {
    color: var(--text-light);
    display: flex;
    align-items: center;
    gap: 4px;
}

.eta::before {
    content: '⏱️';
    font-size: 12px;
}

.btn-cancel {
    margin-top: 20px;
    padding: 12px 24px;
    background: transparent;
    color: var(--danger);
    border: 1px solid var(--danger);
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    width: 100%;
}

.btn-cancel:hover {
    background: rgba(239, 68, 68, 0.1);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(239, 68, 68, 0.1);
}

.status {
    margin-top: 20px;
    padding: 12px;
    border-radius: 8px;
    font-weight: 600;
    text-align: center;
    border: 1px solid transparent;
}

.status.downloading {
    background: rgba(56, 189, 248, 0.1);
    color: var(--accent);
    border-color: var(--accent);
}

.status.completed {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success);
    border-color: var(--success);
}

.status.canceled {
    background: rgba(239, 68, 68, 0.1);
    color: var(--danger);
    border-color: var(--danger);
}

.status.error {
    background: rgba(245, 158, 11, 0.1);
    color: var(--warning);
    border-color: var(--warning);
}

.status.uploading {
    background: rgba(56, 189, 248, 0.1);
    color: var(--accent);
    border-color: var(--accent);
    animation: pulse 2s infinite;
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(5px);
    z-index: 1000;
    justify-content: center;
    align-items: center;
    animation: fadeIn 0.3s ease-out;
}

.modal-content {
    background: var(--card-bg);
    border-radius: 16px;
    padding: 30px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    border: 1px solid var(--glass-effect);
    text-align: center;
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    transform: translateY(20px);
    opacity: 0;
}

.modal-title {
    color: var(--text-light);
    margin-bottom: 20px;
    font-size: 24px;
    font-weight: 700;
}

.file-info {
    margin: 20px 0;
    text-align: left;
    padding: 20px;
    background: var(--progress-bg);
    border-radius: 12px;
    border: 1px solid var(--primary-lighter);
}

.file-info-item {
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
}

.file-info-label {
    color: var(--text-muted);
    font-size: 14px;
}

.file-info-value {
    color: var(--text-light);
    font-weight: 500;
    text-align: right;
    max-width: 60%;
    word-break: break-all;
}

.download-link {
    display: block;
    background: rgba(56, 189, 248, 0.1);
    color: var(--accent);
    padding: 16px;
    border-radius: 8px;
    margin: 20px 0;
    word-break: break-all;
    text-decoration: none;
    border: 1px solid var(--accent);
    transition: all 0.3s;
    font-weight: 500;
}

.download-link:hover {
    background: rgba(56, 189, 248, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(56, 189, 248, 0.1);
}

.modal-btn {
    padding: 12px 24px;
    background: linear-gradient(135deg, var(--accent), var(--accent-dark));
    color: var(--primary);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    margin-top: 15px;
    width: 100%;
}

.modal-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(56, 189, 248, 0.2);
}

/* Panel de administración */
.admin-panel {
    position: fixed;
    top: 0;
    right: -400px;
    width: 380px;
    height: 100vh;
    background: var(--primary-light);
    backdrop-filter: blur(10px);
    border-left: 1px solid var(--glass-effect);
    padding: 20px;
    z-index: 2000;
    transition: right 0.3s ease-out;
    overflow-y: auto;
}

.admin-panel.active {
    right: 0;
}

.admin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--primary-lighter);
}

.admin-title {
    color: var(--admin-accent);
    font-size: 20px;
    font-weight: 600;
}

.close-admin {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 24px;
    cursor: pointer;
    transition: color 0.3s;
}

.close-admin:hover {
    color: var(--danger);
}

.form-group {
    margin-bottom: 20px;
}

.form-label {
    display: block;
    margin-bottom: 8px;
    color: var(--text-light);
    font-size: 14px;
    font-weight: 500;
}

.form-input {
    width: 100%;
    padding: 12px 15px;
    background: var(--primary);
    border: 1px solid var(--primary-lighter);
    border-radius: 8px;
    color: var(--text-light);
    font-size: 14px;
    transition: border-color 0.3s;
}

.form-input:focus {
    outline: none;
    border-color: var(--accent);
}

.form-select {
    width: 100%;
    padding: 12px 15px;
    background: var(--primary);
    border: 1px solid var(--primary-lighter);
    border-radius: 8px;
    color: var(--text-light);
    font-size: 14px;
    appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 16px;
}

.admin-btn {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, var(--admin-accent), #7c3aed);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    margin-top: 10px;
}

.admin-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(139, 92, 246, 0.3);
}

.admin-btn-secondary {
    background: transparent;
    border: 1px solid var(--admin-accent);
    color: var(--admin-accent);
}

.admin-btn-secondary:hover {
    background: rgba(139, 92, 246, 0.1);
}

.admin-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(5px);
    z-index: 1500;
    display: none;
}

.admin-overlay.active {
    display: block;
}

.btn-admin {
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--admin-accent), #7c3aed);
    color: white;
    border: none;
    font-size: 20px;
    cursor: pointer;
    box-shadow: 0 5px 20px rgba(139, 92, 246, 0.4);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
    display: none;
}

.btn-admin:hover {
    transform: translateY(-3px) scale(1.1);
}

/* Historial de descargas */
.history-section {
    margin-top: 40px;
    background: var(--progress-bg);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--primary-lighter);
    animation: fadeIn 0.6s forwards;
}

.section-title {
    color: var(--text-light);
    margin-bottom: 20px;
    font-size: 20px;
    text-align: left;
    position: relative;
    padding-bottom: 10px;
}

.section-title::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, var(--accent), transparent);
}

.history-stats {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    color: var(--text-muted);
    font-size: 14px;
}

.history-list {
    max-height: 300px;
    overflow-y: auto;
    margin-bottom: 20px;
}

.history-item {
    background: var(--primary-light);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s;
}

.history-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.history-file {
    display: flex;
    flex-direction: column;
    flex: 1;
    text-align: left;
}

.history-filename {
    color: var(--text-light);
    font-weight: 500;
    margin-bottom: 5px;
    word-break: break-all;
}

.history-size {
    color: var(--text-muted);
    font-size: 13px;
}

.history-date {
    color: var(--text-muted);
    font-size: 13px;
    margin: 0 15px;
    white-space: nowrap;
}

.history-actions button {
    background: rgba(56, 189, 248, 0.1);
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.3s;
}

.history-actions button:hover {
    background: rgba(56, 189, 248, 0.2);
}

/* Scrollbar personalizada */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--primary-light);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--accent);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-dark);
}

/* Responsive */
@media (max-width: 600px) {
    .container {
        padding: 25px;
        border-radius: 12px;
    }
    
    h1 {
        font-size: 24px;
    }
    
    .input-group {
        flex-direction: column;
    }
    
    .url-input {
        border-radius: 12px 12px 0 0;
    }
    
    .btn {
        width: 100%;
        border-radius: 0 0 12px 12px;
    }
    
    .progress-section {
        padding: 15px;
    }
    
    .modal-content {
        padding: 20px;
        width: 95%;
    }
    
    .admin-panel {
        width: 90%;
        right: -100%;
    }
    
    .history-item {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .history-date {
        margin: 5px 0;
    }
    
    .history-actions {
        align-self: flex-end;
    }
}
    </style>
</head>
<body>
    <!-- Overlay de autenticación -->
    <div class="auth-overlay" id="authOverlay">
        <div class="auth-box">
            <h2 class="auth-title">Acceso Administrativo</h2>
            <input type="password" id="authPassword" class="auth-input" placeholder="Contraseña">
            <button class="auth-btn" onclick="checkAuth()">Acceder</button>
            <div class="auth-error" id="authError">Contraseña incorrecta</div>
        </div>
    </div>

    <!-- Contenedor principal -->
    <div class="container" id="mainContainer">
        <h1>Neon Downloader</h1>
        <div class="input-group">
            <input type="text" id="url-input" class="url-input" placeholder="Pega aquí la URL del archivo..." required>
            <button id="download-btn" class="btn" onclick="handleDownload()">
                <span id="btn-text">Descargar</span>
            </button>
        </div>
        
        <button id="external-btn" class="btn btn-secondary" onclick="openExternalLink()">
            <span>Visitar Soporte</span>
        </button>
        
        <div id="progress-container" class="progress-container">
            <!-- Progreso de descarga -->
            <div class="progress-section">
                <div class="progress-title">Descarga</div>
                <div class="progress-header">
                    <span id="filename" class="filename"></span>
                    <span id="file-size" class="file-size"></span>
                </div>
                <div class="progress-bar">
                    <div id="download-progress" class="progress"></div>
                </div>
                <div class="progress-info">
                    <span id="download-progress-percent" class="progress-percent">0%</span>
                    <span id="download-speed" class="speed">0 KB/s</span>
                    <span id="download-eta" class="eta">--:--:--</span>
                </div>
            </div>
            
            <!-- Progreso de subida -->
            <div class="progress-section">
                <div class="progress-title">Subida</div>
                <div class="progress-bar">
                    <div id="upload-progress" class="progress"></div>
                </div>
                <div class="progress-info">
                    <span id="upload-progress-percent" class="progress-percent">0%</span>
                    <span id="upload-speed" class="speed upload-speed">0 KB/s</span>
                    <span id="upload-status" class="eta">Pendiente</span>
                </div>
            </div>
            
            <div id="status" class="status downloading">Preparando descarga...</div>
            <button id="cancel-btn" class="btn-cancel" onclick="cancelDownload()">Cancelar Proceso</button>
        </div>

        <!-- Sección de Historial -->
        <div id="history-section" class="history-section" style="display: none;">
            <h2 class="section-title">Historial de Descargas</h2>
            <div class="history-stats">
                <span id="total-downloads">0 archivos</span>
                <span id="total-size">0 MB</span>
            </div>
            <div class="history-list" id="history-list">
                <!-- Los elementos del historial se agregarán aquí dinámicamente -->
            </div>
            <button class="btn btn-secondary" onclick="clearHistory()">Limpiar Historial</button>
        </div>
    </div>

    <!-- Modal para descarga completada -->
    <div id="downloadModal" class="modal">
        <div class="modal-content">
            <h2 class="modal-title">¡Proceso Completado!</h2>
            
            <div class="file-info">
                <div class="file-info-item">
                    <span class="file-info-label">Nombre:</span>
                    <span id="modal-filename" class="file-info-value"></span>
                </div>
                <div class="file-info-item">
                    <span class="file-info-label">Tamaño:</span>
                    <span id="modal-filesize" class="file-info-value"></span>
                </div>
                <div class="file-info-item">
                    <span class="file-info-label">Ubicación:</span>
                    <span id="modal-location" class="file-info-value"></span>
                </div>
            </div>
            
            <a id="fileDownloadLink" href="#" class="download-link">
                <span id="link-text">Preparando enlace...</span>
            </a>
            
            <button class="modal-btn" onclick="closeModal()">Cerrar</button>
        </div>
    </div>

    <!-- Botón flotante de administración -->
    <button class="btn-admin" id="adminBtn" onclick="toggleAdminPanel()">⚙️</button>

    <!-- Panel de administración -->
    <div class="admin-panel" id="adminPanel">
        <div class="admin-header">
            <h2 class="admin-title">Configuración del Sistema</h2>
            <button class="close-admin" onclick="toggleAdminPanel()">×</button>
        </div>
        
        <div class="form-group">
            <label class="form-label">Cloud Host</label>
            <input type="text" id="cloudHost" class="form-input" placeholder="Ej: https://api.micloud.com/">
        </div>
        
        <div class="form-group">
            <label class="form-label">Username</label>
            <input type="text" id="cloudUsername" class="form-input" placeholder="Ingrese el usuario">
        </div>
        
        <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" id="cloudPassword" class="form-input" placeholder="Ingrese la contraseña">
        </div>
        
        <div class="form-group">
            <label class="form-label">Tipo de Autenticación</label>
            <input type="text" id="authType" class="form-input" placeholder="Ej: TypeCloud">
        </div>

        <div class="form-group">
            <label class="form-label">Limite (GB)</label>
            <input type="number" id="downLimit" class="form-input" placeholder="Ej: 10">
        </div>
        
        <button class="admin-btn" onclick="saveSettings()">Guardar Configuración</button>
        <button class="admin-btn admin-btn-secondary" onclick="loadSettings()">Cargar Configuración</button>
    </div>

    <script>
        // Configuración
        const EXTERNAL_LINK = "https://ejemplo.com/soporte";
        const ADMIN_PASSWORD = "obi123";
        let downloadId = null;
        let updateInterval = null;
        let isAuthenticated = false;

        // Autenticación
        function checkAuth() {
            const password = document.getElementById('authPassword').value;
            const errorElement = document.getElementById('authError');
            
            if (password === ADMIN_PASSWORD) {
                isAuthenticated = true;
                document.getElementById('authOverlay').style.display = 'none';
                document.getElementById('mainContainer').style.display = 'block';
                document.getElementById('adminBtn').style.display = 'flex';
                
                // Cargar configuración al autenticar
                loadSettings();
                // Cargar historial al autenticar
                loadHistory();
            } else {
                errorElement.style.display = 'block';
                document.getElementById('authPassword').value = '';
                setTimeout(() => {
                    errorElement.style.display = 'none';
                }, 3000);
            }
        }

        // Panel de administración
        function toggleAdminPanel() {
            if (!isAuthenticated) return;
            
            const panel = document.getElementById('adminPanel');
            panel.classList.toggle('active');
        }

        function saveSettings() {
            if (!isAuthenticated) return;
            
            const settings = {
                cloudHost: document.getElementById('cloudHost').value,
                username: document.getElementById('cloudUsername').value,
                password: document.getElementById('cloudPassword').value,
                authType: document.getElementById('authType').value,
                downLimit: document.getElementById('downLimit').value
            };

            fetch('/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': ADMIN_PASSWORD
                },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Configuración guardada correctamente');
                } else {
                    alert('Error: ' + (data.message || 'Error al guardar configuración'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al conectar con el servidor');
            });
        }

        function loadSettings() {
            if (!isAuthenticated) return;
            
            fetch('/settings', {
                headers: {
                    'Authorization': ADMIN_PASSWORD
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('cloudHost').value = data.settings.cloudHost || 'aws';
                    document.getElementById('cloudUsername').value = data.settings.username || '';
                    document.getElementById('cloudPassword').value = data.settings.password || '';
                    document.getElementById('authType').value = data.settings.authType || 'api_key';
                    document.getElementById('downLimit').value = data.settings.downLimit || 'api_key';
                    console.log('Configuración cargada correctamente');
                } else {
                    console.error('Error:', data.message || 'Error al cargar configuración');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        // Historial de descargas
        function loadHistory() {
            fetch('/api/history')
                .then(response => response.json())
                .then(data => {
                    const historyList = document.getElementById('history-list');
                    historyList.innerHTML = '';
                    
                    if (data.history && data.history.length > 0) {
                        document.getElementById('history-section').style.display = 'block';
                        
                        data.history.forEach(item => {
                            const historyItem = document.createElement('div');
                            historyItem.className = 'history-item';
                            historyItem.innerHTML = `
                                <div class="history-file">
                                    <span class="history-filename">${item.filename}</span>
                                    <span class="history-size">${formatFileSize(item.size)}</span>
                                </div>
                                <div class="history-date">${new Date(item.timestamp).toLocaleString()}</div>
                                <div class="history-actions">
                                    <button class="history-download" onclick="location.href='${item.url}';">Descargar</button>
                                </div>
                            `;
                            historyList.appendChild(historyItem);
                        });
                        
                        document.getElementById('total-downloads').textContent = `${data.history.length} archivos`;
                        document.getElementById('total-size').textContent = `${formatFileSize(data.total_size)}`;
                    }
                })
                .catch(error => {
                    console.error('Error al cargar historial:', error);
                });
        }

        function clearHistory() {
            if (confirm('¿Estás seguro de que deseas borrar todo el historial de descargas?')) {
                fetch('/api/history', {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadHistory();
                    }
                })
                .catch(error => {
                    console.error('Error al borrar historial:', error);
                });
            }
        }

        function downloadFromHistory(filename) {
            window.location.href = `/download-file/${downloadId}/${encodeURIComponent(filename)}`;
        }

        // Funciones del Neon Downloader
        function openExternalLink() {
            window.open(EXTERNAL_LINK, '_blank');
        }
        
        function handleDownload() {
            const url = document.getElementById('url-input').value.trim();
            if (!url) {
                alert('Por favor ingresa una URL válida');
                return;
            }
            
            const downloadBtn = document.getElementById('download-btn');
            const btnText = document.getElementById('btn-text');
            downloadBtn.disabled = true;
            btnText.textContent = 'Preparando...';
            
            fetch('/start-download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `url=${encodeURIComponent(url)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    downloadId = data.download_id;
                    window.history.pushState({}, '', `/download/${downloadId}`);
                    showProgress();
                    updateProgress();
                    updateInterval = setInterval(updateProgress, 1000);
                } else {
                    alert('Error: ' + data.message);
                    resetDownloadButton();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al iniciar la descarga');
                resetDownloadButton();
            });
        }
        
        function resetDownloadButton() {
            const downloadBtn = document.getElementById('download-btn');
            const btnText = document.getElementById('btn-text');
            downloadBtn.disabled = false;
            btnText.textContent = 'Descargar';
        }
        
        function showProgress() {
            document.getElementById('progress-container').style.display = 'block';
        }
        
        function updateProgress() {
            if (!downloadId) return;
            
            fetch(`/progress/${downloadId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    clearInterval(updateInterval);
                    document.getElementById('status').textContent = 'Error: ' + data.error;
                    document.getElementById('status').className = 'status error';
                    resetDownloadButton();
                    return;
                }
                
                // Actualizar información de descarga
                document.getElementById('filename').textContent = data.filename || 'Desconocido';
                document.getElementById('file-size').textContent = formatFileSize(data.downloaded) + ' / ' + formatFileSize(data.total_size);
                document.getElementById('download-progress').style.width = data.download_progress + '%';
                document.getElementById('download-progress-percent').textContent = data.download_progress + '%';
                document.getElementById('download-speed').textContent = formatSpeed(data.download_speed);
                document.getElementById('download-eta').textContent = data.download_eta || '--:--:--';
                
                // Actualizar información de subida
                document.getElementById('upload-progress').style.width = data.upload_progress + '%';
                document.getElementById('upload-progress-percent').textContent = data.upload_progress + '%';
                document.getElementById('upload-speed').textContent = formatSpeed(data.upload_speed || 0);
                document.getElementById('upload-status').textContent = getUploadStatusText(data.upload_status);
                
                // Actualizar estado general
                const statusElement = document.getElementById('status');
                if (data.status === 'completed') {
                    statusElement.textContent = '¡Proceso completado con éxito!';
                    statusElement.className = 'status completed';
                    clearInterval(updateInterval);
                    resetDownloadButton();
                    document.getElementById('btn-text').textContent = 'Nueva descarga';
                    
                    // Mostrar modal con resultados
                    showDownloadModal(data);
                } else if (data.status === 'downloading') {
                    statusElement.textContent = 'Descargando...';
                    statusElement.className = 'status downloading';
                } else if (data.status === 'uploading') {
                    statusElement.textContent = 'Subiendo archivo...';
                    statusElement.className = 'status uploading';
                } else if (data.status === 'canceled') {
                    statusElement.textContent = 'Proceso cancelado';
                    statusElement.className = 'status canceled';
                    clearInterval(updateInterval);
                    resetDownloadButton();
                } else if (data.status === 'error') {
                    statusElement.textContent = 'Error: ' + (data.message || 'Error desconocido');
                    statusElement.className = 'status error';
                    clearInterval(updateInterval);
                    resetDownloadButton();
                }
            })
            .catch(error => {
                console.error('Error al actualizar progreso:', error);
            });
        }
        
        function getUploadStatusText(status) {
            const statusTexts = {
                'pending': 'Pendiente',
                'uploading': 'Subiendo...',
                'completed': 'Completado',
                'error': 'Error'
            };
            return statusTexts[status] || status;
        }
        
        function showDownloadModal(data) {
            const modal = document.getElementById('downloadModal');
            const downloadLink = document.getElementById('fileDownloadLink');
            const linkText = document.getElementById('link-text');
            
            // Configurar información del archivo
            document.getElementById('modal-filename').textContent = data.filename || 'Archivo descargado';
            document.getElementById('modal-filesize').textContent = formatFileSize(data.total_size || 0);
            document.getElementById('modal-location').textContent = data.public_url ? 'Servidor remoto' : 'Local';
            
            // Configurar enlace de descarga
            if (data.public_url) {
                downloadLink.href = data.public_url;
                linkText.textContent = 'Abrir enlace público';
                downloadLink.target = '_blank';
            } else {
                downloadLink.href = `/download-file/${downloadId}/${encodeURIComponent(data.filename)}`;
                linkText.textContent = 'Descargar archivo local';
                downloadLink.target = '_self';
            }
            
            // Mostrar modal
            modal.style.display = 'flex';
            setTimeout(() => {
                document.querySelector('.modal-content').style.transform = 'translateY(0)';
                document.querySelector('.modal-content').style.opacity = '1';
            }, 10);
            
            // Actualizar el historial después de completar la descarga
            loadHistory();
        }
        
        function closeModal() {
            const modalContent = document.querySelector('.modal-content');
            modalContent.style.transform = 'translateY(20px)';
            modalContent.style.opacity = '0';
            
            setTimeout(() => {
                document.getElementById('downloadModal').style.display = 'none';
            }, 300);
        }
        
        function cancelDownload() {
            if (!downloadId) return;
            
            document.getElementById('cancel-btn').disabled = true;
            document.getElementById('status').textContent = 'Cancelando...';
            
            fetch(`/cancel-download/${downloadId}`)
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    document.getElementById('cancel-btn').disabled = false;
                }
            })
            .catch(error => {
                console.error('Error al cancelar:', error);
                document.getElementById('cancel-btn').disabled = false;
            });
        }
        
        function formatFileSize(bytes) {
            if (!bytes) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function formatSpeed(bytesPerSecond) {
            if (!bytesPerSecond) return '0 KB/s';
            const k = 1024;
            const sizes = ['Bytes/s', 'KB/s', 'MB/s', 'GB/s'];
            const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
            return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // Manejar la tecla Enter en el input
        document.getElementById('url-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleDownload();
            }
        });
        
        // Cerrar modal haciendo click fuera del contenido
        window.addEventListener('click', function(event) {
            const modal = document.getElementById('downloadModal');
            if (event.target === modal) {
                closeModal();
            }
        });

        // Inicialización
        document.addEventListener('DOMContentLoaded', function() {
            // Mostrar solo el overlay de autenticación al inicio
            document.getElementById('mainContainer').style.display = 'none';
            document.getElementById('authOverlay').style.display = 'flex';
        });
    </script>
</body>
</html>
"""

# Estructura para almacenar el historial
download_history = []

def get_history_file():
    return 'download_history.json'

def load_history():
    history_file = get_history_file()
    with open(history_file, 'r') as f:
            return json.load(f)
    return []

def save_history():
    history_file = get_history_file()
    with open(history_file, 'w') as f:
        json.dump(download_history, f)

def limited(size):
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    # Calcular tamaño total actual
    total_size = sum(item['size'] for item in download_history)
    print(settings['downLimit'] * 1024**3)
    if total_size + size > settings['downLimit'] * 1024**3:
        return True
    return False

def add_to_history(filename, size,cloud_sid,url_down):
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    # Calcular tamaño total actual
    total_size = sum(item['size'] for item in download_history)
    
    # Verificar límite de almacenamiento
    if total_size + size > settings['downLimit'] * 1024**3:
        return False
    
    # Agregar al historial
    download_history.append({
        'filename': filename,
        'size': size,
        'timestamp': datetime.now().isoformat(),
        'url': url_down,
        'cloud_sid':cloud_sid
    })
    
    # Mantener solo los últimos 100 registros
    if len(download_history) > 100:
        download_history.pop(0)
    
    save_history()
    return True

def clear_history():
    global download_history
    download_history = []
    save_history()
    return True

@app.route('/api/history', methods=['GET', 'DELETE'])
def handle_history():
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    if request.method == 'GET':
        return jsonify({
            'history': download_history,
            'total_size': sum(item['size'] for item in download_history),
            'max_size': settings['downLimit'] * 1024**3
        })
    elif request.method == 'DELETE':
        if clear_history():
            return jsonify({'success': True})
        return jsonify({'success': False}), 500

def upload_file(filepath, download_id):
    try:
        settings = {}
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        print('start uploading..')
        file_size = os.path.getsize(filepath)
        chunk_size = 1024 * 1024  # 1MB
        uploaded = 0
        revCli = RevCli(settings['username'],settings['password'],host=settings['cloudHost'],type=settings['authType'])
        loged = revCli.login()

        def upload_progress(filename,bytes_read,len,speed,clock_time,args):
            downloads[download_id].update({'upload_progress': int(bytes_read/len*100),
                                           'uploaded': bytes_read,
                                           'upload_speed': speed,
                                           'upload_status': 'uploading'})

        public_url = ''

        if loged:
            Cloud_Auth['cookies'] = revCli.getsession().cookies.get_dict()
            sid = revCli.create_sid()
            public_url = revCli.upload(filepath,upload_progress,sid=sid)
            add_to_history(filepath,file_size,sid,public_url)
            sids.append(sid)
            try:
                os.unlink(filepath)
            except:pass
            downloads[download_id].update({'upload_progress': 100,
                                           'uploaded': file_size,
                                           'upload_speed': file_size,
                                           'upload_status': 'uploading'})
        return {
            'success': True,
            'public_url': public_url,
            'message': 'Subida completada'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def download_and_upload(download_id, url):
    try:
        # Configurar información inicial
        downloads[download_id] = {
            'url': url,
            'filename': 'Obteniendo información...',
            'total_size': 0,
            'downloaded': 0,
            'download_speed': 0,
            'download_eta': '--:--:--',
            'upload_progress': 0,
            'upload_speed': 0,
            'uploaded': 0,
            'status': 'downloading',
            'upload_status': 'pending',
            'public_url': None,
            'stop_event': threading.Event(),
            'start_time': time.time(),
            'message': ''
        }
        
        # Descargar el archivo
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            
            # Obtener nombre del archivo
            content_disposition = r.headers.get('content-disposition')
            if content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
            else:
                filename = os.path.basename(urlparse(url).path) or f'descarga-{download_id[:6]}'
            
            total_size = int(r.headers.get('content-length', 0))

            if limited(total_size):
                downloads[download_id].update({
                    'status': 'error',
                    'upload_status': 'Error Limited!',
                    'message': "A exedido el limite de Archivos, Limpie el Historial!."})
                return
            
            downloads[download_id].update({
                'filename': secure_filename(filename),
                'total_size': total_size
            })
            
            # Guardar archivo localmente
            filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], downloads[download_id]['filename'])
            with open(filepath, 'wb') as f:
                start_time = time.time()
                for chunk in r.iter_content(chunk_size=8192):
                    if downloads[download_id]['stop_event'].is_set():
                        downloads[download_id]['status'] = 'canceled'
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        return
                    
                    f.write(chunk)
                    downloaded = f.tell()
                    
                    # Calcular progreso descarga
                    current_time = time.time()
                    time_elapsed = current_time - start_time
                    speed = downloaded / time_elapsed if time_elapsed > 0 else 0
                    eta = (total_size - downloaded) / speed if speed > 0 and total_size > 0 else 0
                    
                    downloads[download_id].update({
                        'downloaded': downloaded,
                        'download_speed': speed,
                        'download_eta': format_time(eta),
                        'last_update': current_time
                    })
            
            # Descarga completada
            downloads[download_id]['status'] = 'uploading'
            
            # Iniciar subida del archivo
            upload_result = upload_file(filepath, download_id)
            
            if upload_result['success']:
                downloads[download_id].update({
                    'status': 'completed',
                    'upload_status': 'completed',
                    'public_url': upload_result['public_url'],
                    'message': upload_result['message']
                })
            else:
                downloads[download_id].update({
                    'status': 'error',
                    'upload_status': 'error',
                    'message': upload_result['message']
                })
    
    except Exception as e:
        downloads[download_id].update({
            'status': 'error',
            'upload_status': 'error',
            'message': str(e)
        })

def format_time(seconds):
    return str(timedelta(seconds=seconds)).split('.')[0]

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/start-download', methods=['POST'])
def start_download():
    url = request.form.get('url')
    if not url:
        return jsonify({'success': False, 'message': 'URL no proporcionada'})
    
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return jsonify({'success': False, 'message': 'URL no válida'})
        
        download_id = str(uuid.uuid4())
        
        # Iniciar el hilo de descarga y subida
        thread = threading.Thread(target=download_and_upload, args=(download_id, url))
        thread.start()
        
        downloads[download_id]['thread'] = thread
        
        return jsonify({
            'success': True,
            'download_id': download_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/progress/<download_id>')
def progress(download_id):
    if download_id not in downloads:
        return jsonify({'error': 'ID de descarga no válido'})
    
    download = downloads[download_id]
    
    # Calcular progresos
    download_progress = 0
    if download['total_size'] > 0:
        download_progress = min(100, round((download['downloaded'] / download['total_size']) * 100, 2))
    
    upload_progress = download.get('upload_progress', 0)
    
    return jsonify({
        'filename': download['filename'],
        'total_size': download['total_size'],
        'downloaded': download['downloaded'],
        'download_progress': download_progress,
        'download_speed': download.get('download_speed', 0),
        'download_eta': download.get('download_eta', '--:--:--'),
        'upload_progress': upload_progress,
        'upload_speed': download.get('upload_speed', 0),
        'upload_status': download.get('upload_status', 'pending'),
        'status': download['status'],
        'public_url': download.get('public_url'),
        'message': download.get('message', '')
    })

@app.route('/cancel-download/<download_id>', methods=['POST'])
def cancel_download(download_id):
    if download_id not in downloads:
        return jsonify({'success': False, 'message': 'ID de descarga no válido'})
    
    downloads[download_id]['stop_event'].set()
    return jsonify({'success': True})

@app.route('/download-file/<download_id>/<filename>')
def download_file_endpoint(download_id, filename):
    if download_id not in downloads or downloads[download_id]['status'] != 'completed':
        return "Descarga no encontrada o no completada", 404
    
    try:
        return send_from_directory(
            app.config['DOWNLOAD_FOLDER'],
            downloads[download_id]['filename'],
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError:
        return "Archivo no encontrado", 404

@app.route('/download/<download_id>')
def download_page(download_id):
    return render_template_string(INDEX_HTML)

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    # Verificar autenticación
    auth = request.headers.get('Authorization')
    if not auth or auth != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    if request.method == 'POST':
        try:
            # Recibir y guardar configuración
            settings = request.get_json()
            
            # Validación básica
            if not settings or not isinstance(settings, dict):
                return jsonify({'success': False, 'message': 'Datos de configuración inválidos'})
            
            # Guardar en archivo
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            
            return jsonify({'success': True, 'message': 'Configuración guardada correctamente'})
        
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'GET':
        try:
            # Cargar configuración existente
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                return jsonify({'success': True, 'settings': settings})
            else:
                return jsonify({'success': True, 'settings': {
                    'cloudHost': 'aws',
                    'username': '',
                    'password': '',
                    'authType': 'api_key'
                }})
        
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True, threaded=True,port=443)