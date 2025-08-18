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
CLIENT_PASSWORD = 'client2025'  # Cambia esto en producción

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
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
       :root {
    /* Light Theme */
    --color-primary: #0082c9;
    --color-primary-light: #e6f2f9;
    --color-primary-dark: #006aa3;
    --color-text: #222222;
    --color-text-light: #555555;
    --color-text-lighter: #777777;
    --color-background: #f5f5f5;
    --color-background-dark: #e4e4e4;
    --color-card: #ffffff;
    --color-card-hover: #f8f8f8;
    --color-border: #dddddd;
    --color-success: #2e7d32;
    --color-warning: #ed6c02;
    --color-error: #d32f2f;
    --color-shadow: rgba(0, 0, 0, 0.1);
    --color-overlay: rgba(0, 0, 0, 0.5);
    --color-progress: #4caf50;
    --color-progress-bg: #e0e0e0;
    --color-storage: #4caf50;
    --color-storage-warning: #ff9800;
    --color-storage-danger: #f44336;
}

[data-theme="dark"] {
    /* Dark Theme */
    --color-primary: #0082c9;
    --color-primary-light: #1a2a3a;
    --color-primary-dark: #006aa3;
    --color-text: #e4e4e4;
    --color-text-light: #b0b0b0;
    --color-text-lighter: #8a8a8a;
    --color-background: #1e1e1e;
    --color-background-dark: #171717;
    --color-card: #2d2d2d;
    --color-card-hover: #383838;
    --color-border: #444444;
    --color-success: #4caf50;
    --color-warning: #ff9800;
    --color-error: #f44336;
    --color-shadow: rgba(0, 0, 0, 0.3);
    --color-overlay: rgba(0, 0, 0, 0.7);
    --color-progress: #4caf50;
    --color-progress-bg: #444444;
    --color-storage: #4caf50;
    --color-storage-warning: #ff9800;
    --color-storage-danger: #f44336;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', 'Open Sans', 'Helvetica Neue', sans-serif;
    transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}

body {
    background-color: var(--color-background);
    color: var(--color-text);
    line-height: 1.6;
    min-height: 100vh;
}

/* Layout */
.app-container {
    display: none;
    min-height: 100vh;
    flex-direction: column;
}

.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem 1.5rem;
    background-color: var(--color-card);
    box-shadow: 0 2px 10px var(--color-shadow);
    z-index: 100;
    position: sticky;
    top: 0;
}

.header-left, .header-right {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.logo {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--color-primary);
}

.logo i {
    font-size: 1.5rem;
}

.storage-info {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 0.9rem;
}

.storage-progress {
    width: 100px;
    height: 8px;
    background-color: var(--color-progress-bg);
    border-radius: 4px;
    overflow: hidden;
}

.storage-bar {
    height: 100%;
    background-color: var(--color-storage);
    width: 0%;
    transition: width 0.5s ease-out;
}

.app-content {
    flex: 1;
    padding: 1.5rem;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
}

/* Tabs */
.tabs {
    display: flex;
    border-bottom: 1px solid var(--color-border);
    margin-bottom: 1.5rem;
    gap: 0.5rem;
}

.tab-btn {
    padding: 0.8rem 1.5rem;
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--color-text-light);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    transition: all 0.2s;
}

.tab-btn:hover {
    color: var(--color-primary);
}

.tab-btn.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
}

.tab-content {
    display: none;
    animation: fadeIn 0.3s ease-out;
}

.tab-content.active {
    display: block;
}

/* Cards */
.card {
    background-color: var(--color-card);
    border-radius: 10px;
    box-shadow: 0 2px 10px var(--color-shadow);
    margin-bottom: 1.5rem;
    overflow: hidden;
    border: 1px solid var(--color-border);
}

.card:hover {
    box-shadow: 0 4px 15px var(--color-shadow);
}

.card-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--color-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.card-header h2 {
    font-size: 1.2rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.card-content {
    padding: 1.5rem;
}

.file-actions {
    display: flex;
    gap: 0.8rem;
}

/* Inputs & Buttons */
.input-group {
    display: flex;
    width: 100%;
}

.url-input {
    flex: 1;
    padding: 0.8rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 6px 0 0 6px;
    font-size: 1rem;
    outline: none;
    background-color: var(--color-card);
    color: var(--color-text);
}

.url-input:focus {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgba(0, 130, 201, 0.2);
}

.btn {
    padding: 0.8rem 1.5rem;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    transition: all 0.2s;
}

.btn-primary {
    background-color: var(--color-primary);
    color: white;
}

.btn-primary:hover {
    background-color: var(--color-primary-dark);
    transform: translateY(-1px);
}

.btn-secondary {
    background-color: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);
}

.btn-secondary:hover {
    background-color: var(--color-primary-light);
}

.btn-cancel {
    background-color: transparent;
    color: var(--color-error);
    border: 1px solid var(--color-error);
}

.btn-cancel:hover {
    background-color: rgba(244, 67, 54, 0.1);
}

.btn-icon {
    background: none;
    border: none;
    color: var(--color-text-light);
    font-size: 1.2rem;
    cursor: pointer;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.btn-icon:hover {
    background-color: var(--color-background-dark);
    color: var(--color-primary);
}

/* Progress */
.progress-section {
    margin-bottom: 1.5rem;
}

.progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.8rem;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.progress-header h3 {
    font-size: 1rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.file-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.filename {
    font-weight: 500;
    color: var(--color-text);
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    max-width: 300px;
}

.file-size {
    color: var(--color-text-light);
    font-size: 0.9rem;
}

.progress-bar-container {
    margin-bottom: 0.5rem;
}

.progress-bar {
    height: 8px;
    background-color: var(--color-progress-bg);
    border-radius: 4px;
    overflow: hidden;
}

.progress {
    height: 100%;
    background-color: var(--color-primary);
    width: 0%;
    transition: width 0.4s ease-out;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    font-size: 0.9rem;
    color: var(--color-text-light);
}

.progress-percent {
    font-weight: 600;
    color: var(--color-primary);
}

.speed, .eta {
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

/* Status */
.status {
    margin: 1.5rem 0;
    padding: 0.8rem 1rem;
    border-radius: 6px;
    font-weight: 500;
    text-align: center;
    border: 1px solid transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
}

.status.downloading {
    background-color: rgba(0, 130, 201, 0.1);
    color: var(--color-primary);
    border-color: rgba(0, 130, 201, 0.2);
}

.status.completed {
    background-color: rgba(76, 175, 80, 0.1);
    color: var(--color-success);
    border-color: rgba(76, 175, 80, 0.2);
}

.status.canceled {
    background-color: rgba(244, 67, 54, 0.1);
    color: var(--color-error);
    border-color: rgba(244, 67, 54, 0.2);
}

.status.error {
    background-color: rgba(237, 108, 2, 0.1);
    color: var(--color-warning);
    border-color: rgba(237, 108, 2, 0.2);
}

.status.uploading {
    background-color: rgba(0, 130, 201, 0.1);
    color: var(--color-primary);
    border-color: rgba(0, 130, 201, 0.2);
}

/* History */
.history-list {
    max-height: 500px;
    overflow-y: auto;
    margin-bottom: 1.5rem;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 0;
    color: var(--color-text-light);
    text-align: center;
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.history-item {
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 0.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: var(--color-background-dark);
    transition: all 0.2s;
    border: 1px solid var(--color-border);
}

.history-item:hover {
    background-color: var(--color-card-hover);
    transform: translateY(-1px);
    box-shadow: 0 2px 5px var(--color-shadow);
}

.history-file {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
}

.history-filename {
    color: var(--color-text);
    font-weight: 500;
    margin-bottom: 0.3rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-size {
    color: var(--color-text-light);
    font-size: 0.85rem;
}

.history-date {
    color: var(--color-text-light);
    font-size: 0.85rem;
    margin: 0 1rem;
    white-space: nowrap;
}

.history-actions {
    display: flex;
    gap: 0.5rem;
}

.history-actions button {
    background-color: rgba(0, 130, 201, 0.1);
    color: var(--color-primary);
    border: 1px solid rgba(0, 130, 201, 0.3);
    border-radius: 4px;
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: all 0.2s;
}

.history-actions button:hover {
    background-color: rgba(0, 130, 201, 0.2);
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: var(--color-overlay);
    backdrop-filter: blur(5px);
    z-index: 2000;
    justify-content: center;
    align-items: center;
    animation: fadeIn 0.3s ease-out;
}

.modal-content {
    background-color: var(--color-card);
    border-radius: 10px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 5px 20px var(--color-shadow);
    overflow: hidden;
    animation: modalIn 0.3s ease-out forwards;
    transform: translateY(20px);
    opacity: 0;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
}

.modal-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--color-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h2 {
    font-size: 1.2rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.modal-body {
    padding: 1.5rem;
    overflow-y: auto;
}

.modal-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--color-border);
    display: flex;
    justify-content: flex-end;
}

.file-info {
    margin: 1rem 0;
}

.file-info-item {
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
}

.file-info-label {
    color: var(--color-text-light);
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.file-info-value {
    color: var(--color-text);
    font-weight: 500;
    text-align: right;
    max-width: 60%;
    word-break: break-word;
}

.download-link {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: rgba(0, 130, 201, 0.1);
    color: var(--color-primary);
    padding: 1rem;
    border-radius: 6px;
    margin: 1.5rem 0;
    text-decoration: none;
    border: 1px solid rgba(0, 130, 201, 0.3);
    transition: all 0.2s;
}

.download-link:hover {
    background-color: rgba(0, 130, 201, 0.2);
    transform: translateY(-1px);
}

/* Cleaning Modal */
.cleaning {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
    text-align: center;
}

.cleaning-animation {
    margin-bottom: 1.5rem;
    position: relative;
    width: 100px;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.cleaning-animation i {
    font-size: 3rem;
    color: var(--color-primary);
    animation: pulse 1.5s infinite;
}

.cleaning-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background-color: var(--color-progress-bg);
    border-radius: 2px;
    overflow: hidden;
}

.cleaning-bar {
    height: 100%;
    background-color: var(--color-primary);
    width: 0%;
}

/* Form */
.form-group {
    margin-bottom: 1.5rem;
}

.form-label {
    display: block;
    margin-bottom: 0.5rem;
    color: var(--color-text);
    font-size: 0.95rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.form-input {
    width: 100%;
    padding: 0.8rem 1rem;
    background-color: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    color: var(--color-text);
    font-size: 1rem;
    transition: all 0.2s;
}

.form-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgba(0, 130, 201, 0.2);
}

.form-actions {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes modalIn {
    to { transform: translateY(0); opacity: 1; }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.fa-spin {
    animation: spin 1s linear infinite;
}

/* Responsive */
@media (max-width: 768px) {
    .app-content {
        padding: 1rem;
    }
    
    .header-right {
        gap: 1rem;
    }
    
    .storage-info {
        display: none;
    }
    
    .tab-btn {
        padding: 0.8rem 1rem;
        font-size: 0.9rem;
    }
    
    .card-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
    
    .file-actions {
        width: 100%;
        justify-content: flex-end;
    }
    
    .history-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
    
    .history-date {
        margin: 0;
    }
    
    .history-actions {
        align-self: flex-end;
    }
    
    .form-actions {
        flex-direction: column;
    }
}

@media (max-width: 480px) {
    .input-group {
        flex-direction: column;
    }
    
    .url-input {
        border-radius: 6px 6px 0 0;
    }
    
    .btn {
        width: 100%;
        border-radius: 0 0 6px 6px;
    }
    
    .progress-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .file-info {
        width: 100%;
    }
    
    .filename {
        max-width: 100%;
    }
}
/* Estilos para el overlay de autenticación */
.auth-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    opacity: 1;
    transition: opacity 0.3s ease;
}

.auth-box {
    background: var(--card-bg);
    border-radius: 16px;
    padding: 2.5rem;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    transform: translateY(0);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border: 1px solid var(--border-color);
}

.auth-box:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
}

.auth-box .logo {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 2rem;
    color: var(--primary-color);
}

.auth-box .logo i {
    font-size: 3.5rem;
    margin-bottom: 1rem;
}

.auth-box .logo span {
    font-size: 1.8rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.auth-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.auth-form h2 {
    text-align: center;
    margin: 0 0 1rem;
    font-size: 1.5rem;
    color: var(--text-color);
}

.auth-input {
    padding: 1rem 1.5rem;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: var(--input-bg);
    color: var(--text-color);
    font-size: 1rem;
    transition: all 0.3s ease;
    outline: none;
}

.auth-input:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.1);
}

.auth-btn {
    padding: 1rem;
    border-radius: 8px;
    background: var(--primary-color);
    color: white;
    border: none;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.3s ease;
}

.auth-btn:hover {
    background: var(--primary-hover);
    transform: translateY(-2px);
}

.auth-btn:active {
    transform: translateY(0);
}

.auth-error {
    color: #ff6b6b;
    background: rgba(255, 107, 107, 0.1);
    padding: 0.8rem 1rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    opacity: 0;
    height: 0;
    overflow: hidden;
    transition: all 0.3s ease;
}

.auth-error.show {
    opacity: 1;
    height: auto;
    padding: 0.8rem 1rem;
    margin-top: 0.5rem;
}
    </style>
</head>
<body>
    <!-- Overlay de autenticación -->
    <div class="auth-overlay" id="authOverlay">
        <div class="auth-box">
            <div class="logo">
                <i class="fas fa-cloud-upload-alt"></i>
                <span>Neon - Cloud - Transfer</span>
            </div>
            <div class="auth-form">
                <h2>Acceso Administrativo</h2>
                <input type="password" id="authPassword" class="auth-input" placeholder="Contraseña">
                <button class="auth-btn" onclick="checkAuth()">
                    <i class="fas fa-sign-in-alt"></i> Acceder
                </button>
                <div class="auth-error" id="authError">
                    <i class="fas fa-exclamation-circle"></i> Contraseña incorrecta
                </div>
            </div>
        </div>
    </div>

    <!-- Contenedor principal -->
    <div class="app-container" id="mainContainer">
        <!-- Header -->
        <header class="app-header">
            <div class="header-left">
                <div class="logo">
                    <i class="fas fa-cloud-upload-alt"></i>
                    <span>Neon - Cloud - Transfer</span>
                </div>
            </div>
            <div class="header-right">
                <div class="storage-info" id="storageInfo">
                    <div class="storage-progress">
                        <div class="storage-bar" id="storageBar"></div>
                    </div>
                    <span id="storageText">0 GB / 10 GB</span>
                </div>
                <button class="btn-icon" id="themeToggle">
                    <i class="fas fa-moon"></i>
                </button>
            </div>
        </header>

        <!-- Contenido principal -->
        <main class="app-content">
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab-btn active" data-tab="transfer">
                    <i class="fas fa-exchange-alt"></i> Transferencia
                </button>
                <button class="tab-btn" data-tab="files">
                    <i class="fas fa-folder"></i> Archivos
                </button>
                <button id="btn-settings" class="tab-btn" data-tab="settings">
                    <i class="fas fa-cog"></i> Configuración
                </button>
            </div>

            <!-- Contenido de los tabs -->
            <div class="tab-content active" id="transfer-tab">
                <div class="card download-card">
                    <div class="input-group">
                        <input type="text" id="url-input" class="url-input" placeholder="Pega aquí la URL del archivo..." required>
                        <button id="download-btn" class="btn btn-primary" onclick="handleDownload()">
                            <span id="btn-text">Descargar</span>
                            <i class="fas fa-arrow-down"></i>
                        </button>
                    </div>
                </div>

                <!-- Progreso de descarga -->
                <div class="card progress-card" id="progress-container" style="display: none;padding:10px;">
                    <div class="progress-section">
                        <div class="progress-header">
                            <h3><i class="fas fa-download"></i> Descarga</h3>
                            <div class="file-info">
                                <span id="filename" class="filename"></span>
                                <span id="file-size" class="file-size"></span>
                            </div>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar">
                                <div id="download-progress" class="progress"></div>
                            </div>
                            <div class="progress-info">
                                <span id="download-progress-percent" class="progress-percent">0%</span>
                                <span id="download-speed" class="speed"><i class="fas fa-tachometer-alt"></i> 0 KB/s</span>
                                <span id="download-eta" class="eta"><i class="far fa-clock"></i> --:--:--</span>
                            </div>
                        </div>
                    </div>

                    <div class="progress-section">
                        <div class="progress-header">
                            <h3><i class="fas fa-upload"></i> Subida</h3>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar">
                                <div id="upload-progress" class="progress"></div>
                            </div>
                            <div class="progress-info">
                                <span id="upload-progress-percent" class="progress-percent">0%</span>
                                <span id="upload-speed" class="speed"><i class="fas fa-tachometer-alt"></i> 0 KB/s</span>
                                <span id="upload-status" class="eta"><i class="fas fa-info-circle"></i> Pendiente</span>
                            </div>
                        </div>
                    </div>

                    <div id="status" class="status downloading">
                        <i class="fas fa-sync-alt fa-spin"></i> Preparando descarga...
                    </div>
                    <button id="cancel-btn" class="btn btn-cancel" onclick="cancelDownload()">
                        <i class="fas fa-times-circle"></i> Cancelar Proceso
                    </button>
                </div>
            </div>

            <!-- Tab Archivos -->
            <div class="tab-content" id="files-tab">
                <div class="card files-card">
                    <div class="card-header">
                        <h2><i class="fas fa-history"></i> Historial de Archivos</h2>
                        <div class="file-actions">
                            <button class="btn btn-secondary" onclick="clearHistory()" id="clearHistoryBtn">
                                <i class="fas fa-trash-alt"></i> Limpiar Historial
                            </button>
                        </div>
                    </div>
                    <div class="card-content">
                        <div class="history-list" id="history-list">
                            <!-- Los elementos del historial se agregarán aquí dinámicamente -->
                            <div class="empty-state" id="emptyState">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>No hay archivos en el historial</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab Configuración -->
            <div class="tab-content" id="settings-tab">
                <div class="card settings-card">
                    <div class="card-header">
                        <h2><i class="fas fa-cogs"></i> Configuración del Sistema</h2>
                    </div>
                    <div class="card-content">
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-key"></i> Master-Password</label>
                            <input type="text" id="masterPassword" class="form-input" placeholder="Ej: Obi123">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-server"></i> Cloud Host</label>
                            <input type="text" id="cloudHost" class="form-input" placeholder="Ej: https://api.micloud.com/">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-user"></i> Username</label>
                            <input type="text" id="cloudUsername" class="form-input" placeholder="Ingrese el usuario">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-lock"></i> Password</label>
                            <input type="password" id="cloudPassword" class="form-input" placeholder="Ingrese la contraseña">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-user-shield"></i> Tipo de Autenticación</label>
                            <input type="text" id="authType" class="form-input" placeholder="Ej: TypeCloud">
                        </div>

                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-hdd"></i> Límite de Almacenamiento (GB)</label>
                            <input type="number" id="downLimit" class="form-input" placeholder="Ej: 10">
                        </div>
                        
                        <div class="form-actions">
                            <button class="btn btn-primary" onclick="saveSettings()">
                                <i class="fas fa-save"></i> Guardar Configuración
                            </button>
                            <button class="btn btn-secondary" onclick="loadSettings()">
                                <i class="fas fa-sync-alt"></i> Cargar Configuración
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Modal para descarga completada -->
    <div id="downloadModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-check-circle"></i> ¡Proceso Completado!</h2>
                <button class="btn-icon" onclick="closeModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="file-info">
                    <div class="file-info-item">
                        <span class="file-info-label"><i class="fas fa-file-alt"></i> Nombre:</span>
                        <span id="modal-filename" class="file-info-value"></span>
                    </div>
                    <div class="file-info-item">
                        <span class="file-info-label"><i class="fas fa-weight-hanging"></i> Tamaño:</span>
                        <span id="modal-filesize" class="file-info-value"></span>
                    </div>
                    <div class="file-info-item">
                        <span class="file-info-label"><i class="fas fa-map-marker-alt"></i> Ubicación:</span>
                        <span id="modal-location" class="file-info-value"></span>
                    </div>
                </div>
                
                <a id="fileDownloadLink" href="#" class="download-link">
                    <span id="link-text">Preparando enlace...</span>
                    <i class="fas fa-external-link-alt"></i>
                </a>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="closeModal()">
                    <i class="fas fa-check"></i> Cerrar
                </button>
            </div>
        </div>
    </div>

    <!-- Modal de limpieza -->
    <div id="cleanModal" class="modal">
        <div class="modal-content">
            <div class="modal-body cleaning">
                <div class="cleaning-animation">
                    <i class="fas fa-trash-alt"></i>
                    <div class="cleaning-progress">
                        <div class="cleaning-bar" id="cleaningBar"></div>
                    </div>
                </div>
                <h3 id="cleaningText">Limpiando archivos...</h3>
            </div>
        </div>
    </div>

    <script>
       // Configuración
const EXTERNAL_LINK = "https://ejemplo.com/soporte";
const ADMIN_PASSWORD = "obi123";
let downloadId = null;
let updateInterval = null;
let isAuthenticated = false;
let currentTab = 'transfer';
let cleaningInterval = null;

// Inicialización
function init() {
    initTheme();
    setupEventListeners();
    
    // Mostrar solo el overlay de autenticación al inicio
    document.getElementById('mainContainer').style.display = 'none';
    document.getElementById('authOverlay').style.display = 'flex';
}

// Inicialización del tema
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

// Cambiar tema
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

// Actualizar icono del tema
function updateThemeIcon(theme) {
    const icon = document.querySelector('#themeToggle i');
    if (theme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}

// Configurar event listeners
function setupEventListeners() {
    // Botón de tema
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            changeTab(tabId);
        });
    });
    
    // Input de URL
    document.getElementById('url-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleDownload();
        }
    });
    
    // Cerrar modal haciendo click fuera
    window.addEventListener('click', function(event) {
        if (event.target === document.getElementById('downloadModal')) {
            closeModal();
        }
    });
}

// Cambiar pestaña
function changeTab(tabId) {
    // Ocultar todas las pestañas
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Desactivar todos los botones de pestaña
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar la pestaña seleccionada
    document.getElementById(`${tabId}-tab`).classList.add('active');
    
    // Activar el botón de la pestaña seleccionada
    document.querySelector(`.tab-btn[data-tab="${tabId}"]`).classList.add('active');
    
    currentTab = tabId;
    
    // Si es la pestaña de archivos, cargar el historial
    if (tabId === 'files') {
        loadHistory();
    }
}

// Actualizar información de almacenamiento
function updateStorageInfo() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            const totalSize = data.total_size || 0;
            const maxSize = data.max_size || 10 * 1024 * 1024 * 1024; // 10GB por defecto
            
            const usedGB = (totalSize / (1024 * 1024 * 1024)).toFixed(2);
            const maxGB = (maxSize / (1024 * 1024 * 1024)).toFixed(2);
            const percent = Math.min((totalSize / maxSize) * 100, 100);
            
            document.getElementById('storageText').textContent = `${usedGB} GB / ${maxGB} GB`;
            
            const storageBar = document.getElementById('storageBar');
            storageBar.style.width = `${percent}%`;
            
            // Cambiar color según el porcentaje de uso
            if (percent > 90) {
                storageBar.style.backgroundColor = 'var(--color-storage-danger)';
            } else if (percent > 70) {
                storageBar.style.backgroundColor = 'var(--color-storage-warning)';
            } else {
                storageBar.style.backgroundColor = 'var(--color-storage)';
            }
        })
        .catch(error => {
            console.error('Error al cargar información de almacenamiento:', error);
        });
}

// Autenticación
function checkAuth() {
    const password = document.getElementById('authPassword').value;
    const errorElement = document.getElementById('authError');
    
    if (!password) {
        errorElement.textContent = 'Por favor ingrese una contraseña';
        errorElement.classList.add('show');
        return;
    }

    fetch(`/api/auth/${encodeURIComponent(password)}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.loged) {
            isAuthenticated = true;
            document.getElementById('authOverlay').style.display = 'none';
            document.getElementById('mainContainer').style.display = 'flex';
        
            // Cargar configuración y actualizar información
            if(!data.is_admin){
                document.getElementById('settings-tab').style.display = 'none';
                document.getElementById('btn-settings').style.display = 'none';
            }
            loadSettings();
            updateStorageInfo();
            loadHistory();
        } else {
            errorElement.textContent = data.message || 'Contraseña incorrecta';
            errorElement.classList.add('show');
            document.getElementById('authPassword').value = '';
            setTimeout(() => {
                errorElement.classList.remove('show');
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error en autenticación:', error);
        errorElement.textContent = 'Error de conexión con el servidor';
        errorElement.classList.add('show');
        setTimeout(() => {
            errorElement.classList.remove('show');
        }, 3000);
    });
}

// Cargar configuración
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
            document.getElementById('downLimit').value = data.settings.downLimit || 10;
            document.getElementById('masterPassword').value = data.settings.masterPassword || '';
            
            // Actualizar la información de almacenamiento después de cargar la configuración
            updateStorageInfo();
        } else {
            console.error('Error:', data.message || 'Error al cargar configuración');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Guardar configuración
function saveSettings() {
    if (!isAuthenticated) return;
    
    const settings = {
        cloudHost: document.getElementById('cloudHost').value,
        username: document.getElementById('cloudUsername').value,
        password: document.getElementById('cloudPassword').value,
        authType: document.getElementById('authType').value,
        downLimit: parseInt(document.getElementById('downLimit').value) || 10,
        masterPassword: document.getElementById('masterPassword').value
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
            showAlert('Configuración guardada correctamente', 'success');
            updateStorageInfo();
        } else {
            showAlert('Error: ' + (data.message || 'Error al guardar configuración'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al conectar con el servidor', 'error');
    });
}

// Mostrar alerta
function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
    `;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 300);
    }, 3000);
}

// Cargar historial
function loadHistory() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            const historyList = document.getElementById('history-list');
            const emptyState = document.getElementById('emptyState');
            
            // Limpiar el contenido actual
            historyList.innerHTML = '';
            
            if (data.history && data.history.length > 0) {
                // Ocultar emptyState si existe
                if (emptyState) {
                    emptyState.style.display = 'none';
                }
                
                // Mostrar items del historial
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
                            <button onclick="window.open('${item.url}', '_blank')">
                                <i class="fas fa-download"></i> Descargar
                            </button>
                        </div>
                    `;
                    historyList.appendChild(historyItem);
                });
            } else {
                // Mostrar emptyState si existe
                if (emptyState) {
                    emptyState.style.display = 'flex';
                } else {
                    // Crear emptyState si no existe
                    const emptyDiv = document.createElement('div');
                    emptyDiv.id = 'emptyState';
                    emptyDiv.className = 'empty-state';
                    emptyDiv.innerHTML = `
                        <i class="fas fa-cloud-upload-alt"></i>
                        <p>No hay archivos en el historial</p>
                    `;
                    historyList.appendChild(emptyDiv);
                }
            }
            
            // Actualizar la información de almacenamiento
            updateStorageInfo();
        })
        .catch(error => {
            console.error('Error al cargar historial:', error);
            showAlert('Error al cargar el historial de archivos', 'error');
        });
}

// Limpiar historial con animación
function clearHistory() {
    if (!confirm('¿Estás seguro de que deseas borrar todo el historial de descargas?')) {
        return;
    }
    
    const cleanModal = document.getElementById('cleanModal');
    const cleaningBar = document.getElementById('cleaningBar');
    const cleaningText = document.getElementById('cleaningText');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    
    // Mostrar modal de limpieza
    cleanModal.style.display = 'flex';
    clearHistoryBtn.disabled = true;
    
    // Animación de progreso
    let progress = 0;
    cleaningInterval = setInterval(() => {
        progress += 5;
        cleaningBar.style.width = `${progress}%`;
        
        if (progress >= 100) {
            clearInterval(cleaningInterval);
            cleaningText.textContent = '¡Limpieza completada!';
            
            // Realizar la limpieza real
            fetch('/api/history', {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setTimeout(() => {
                        cleanModal.style.display = 'none';
                        clearHistoryBtn.disabled = false;
                        loadHistory();
                        showAlert('Historial borrado correctamente', 'success');
                    }, 1000);
                }
            })
            .catch(error => {
                console.error('Error al borrar historial:', error);
                cleanModal.style.display = 'none';
                clearHistoryBtn.disabled = false;
                showAlert('Error al borrar el historial', 'error');
            });
        }
    }, 100);
}

// Manejar descarga
function handleDownload() {
    const url = document.getElementById('url-input').value.trim();
    if (!url) {
        showAlert('Por favor ingresa una URL válida', 'error');
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
            showAlert('Error: ' + data.message, 'error');
            resetDownloadButton();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al iniciar la descarga', 'error');
        resetDownloadButton();
    });
}

function resetDownloadButton() {
    const downloadBtn = document.getElementById('download-btn');
    const btnText = document.getElementById('btn-text');
    downloadBtn.disabled = false;
    btnText.textContent = 'Descargar';
}

function showProgress(show = true) {
    document.getElementById('progress-container').style.display = show ? 'block' : 'none';
}

// Actualizar progreso
function updateProgress() {
    if (!downloadId) return;
    
    fetch(`/progress/${downloadId}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            clearInterval(updateInterval);
            document.getElementById('status').innerHTML = `<i class="fas fa-exclamation-circle"></i> Error: ${data.error}`;
            document.getElementById('status').className = 'status error';
            resetDownloadButton();
            return;
        }
        
        // Actualizar información de descarga
        document.getElementById('filename').textContent = data.filename || 'Desconocido';
        document.getElementById('file-size').textContent = `${formatFileSize(data.downloaded)} / ${formatFileSize(data.total_size)}`;
        document.getElementById('download-progress').style.width = data.download_progress + '%';
        document.getElementById('download-progress-percent').textContent = data.download_progress + '%';
        document.getElementById('download-speed').innerHTML = `<i class="fas fa-tachometer-alt"></i> ${formatSpeed(data.download_speed)}`;
        document.getElementById('download-eta').innerHTML = `<i class="far fa-clock"></i> ${data.download_eta || '--:--:--'}`;
        
        // Actualizar información de subida
        document.getElementById('upload-progress').style.width = data.upload_progress + '%';
        document.getElementById('upload-progress-percent').textContent = data.upload_progress + '%';
        document.getElementById('upload-speed').innerHTML = `<i class="fas fa-tachometer-alt"></i> ${formatSpeed(data.upload_speed || 0)}`;
        document.getElementById('upload-status').innerHTML = `<i class="fas fa-info-circle"></i> ${getUploadStatusText(data.upload_status)}`;
        
        // Actualizar estado general
        const statusElement = document.getElementById('status');
        if (data.status === 'completed') {
            statusElement.innerHTML = `<i class="fas fa-check-circle"></i> ¡Proceso completado con éxito!`;
            statusElement.className = 'status completed';
            clearInterval(updateInterval);
            resetDownloadButton();
            document.getElementById('btn-text').textContent = 'Nueva descarga';
            showDownloadModal(data);
            updateStorageInfo();
        } else if (data.status === 'downloading') {
            statusElement.innerHTML = `<i class="fas fa-sync-alt fa-spin"></i> Descargando...`;
            statusElement.className = 'status downloading';
        } else if (data.status === 'uploading') {
            statusElement.innerHTML = `<i class="fas fa-sync-alt fa-spin"></i> Subiendo archivo...`;
            statusElement.className = 'status uploading';
        } else if (data.status === 'canceled') {
            statusElement.innerHTML = `<i class="fas fa-times-circle"></i> Proceso cancelado`;
            statusElement.className = 'status canceled';
            clearInterval(updateInterval);
            resetDownloadButton();
        } else if (data.status === 'error') {
            statusElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> Error: ${data.message || 'Error desconocido'}`;
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

// Mostrar modal de descarga completada
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

// Cerrar modal
function closeModal() {
    const modalContent = document.querySelector('.modal-content');
    modalContent.style.transform = 'translateY(20px)';
    modalContent.style.opacity = '0';
    
    setTimeout(() => {
        document.getElementById('downloadModal').style.display = 'none';
        showProgress(false);
    }, 300);
}

// Cancelar descarga
function cancelDownload() {
    if (!downloadId) return;
    
    document.getElementById('cancel-btn').disabled = true;
    document.getElementById('status').innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Cancelando...';
    
    fetch(`/cancel-download/${downloadId}`)
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            document.getElementById('cancel-btn').disabled = false;
        }
        showProgress(false);
    })
    .catch(error => {
        console.error('Error al cancelar:', error);
        document.getElementById('cancel-btn').disabled = false;
    });
}

// Formatear tamaño de archivo
function formatFileSize(bytes) {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Formatear velocidad
function formatSpeed(bytesPerSecond) {
    if (!bytesPerSecond) return '0 KB/s';
    const k = 1024;
    const sizes = ['Bytes/s', 'KB/s', 'MB/s', 'GB/s'];
    const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
    return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""

# Estructura para almacenar el historial
download_history = []

def get_history_file():
    return 'download_history.json'

def load_history():
    try:
        history_file = get_history_file()
        with open('auth.json', 'r') as f:
                Cloud_Auth = json.load(f)
        with open(history_file, 'r') as f:
                return json.load(f)
    except:pass
    return []

def save_history():
    history_file = get_history_file()
    with open(history_file, 'w') as f:
        json.dump(download_history, f)
    with open('auth.json', 'w') as f:
        json.dump(Cloud_Auth, f)

def limited(size):
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    # Calcular tamaño total actual
    total_size = sum(item['size'] for item in download_history)
    if total_size + int(size) > settings['downLimit'] * 1024**3:
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
    cli = RevCli(host=Cloud_Auth['host'],type=Cloud_Auth['type'])
    cli.session.cookies.update(Cloud_Auth['cookies'])
    for item in download_history:
        cli.delete_sid(item['cloud_sid'])
    download_history = []
    save_history()
    return True

@app.route('/api/history', methods=['GET', 'DELETE'])
def handle_history():
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    if len(download_history)<=0:
        cli = RevCli(settings['username'],settings['password'],host=settings['cloudHost'],type=settings['authType'])
        if cli.login():
            cli.delete_all_sid()
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

@app.route('/api/auth', methods=['GET', 'DELETE'])
def handle_auth():

    return jsonify({'success': False}), 500

def upload_file(filepath, download_id):
    try:
        settings = {}
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
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
            Cloud_Auth['host'] = revCli.host
            Cloud_Auth['type'] = revCli.type
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

@app.route('/api/auth/<password>', methods=['GET'])
def auth(password):
    try:
        # Verificar la contraseña
        if password == ADMIN_PASSWORD:
            return jsonify({
                'success': True,
                'loged': True,
                'message': 'Autenticación exitosa',
                'is_admin':True
            })
        elif password == CLIENT_PASSWORD:
            return jsonify({
                'success': False,
                'loged': True,
                'message': 'Contraseña incorrecta',
                'is_admin':False
            })
        else:
            return jsonify({
                'success': False,
                'loged': False,
                'message': 'Contraseña incorrecta',
                'is_admin':False
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'loged': False,
            'message': f'Error en la autenticación: {str(e)}',
            'is_admin':False
        }), 500


if __name__ == '__main__':
    download_history = load_history()

    app.run(debug=True, threaded=True,port=443)

