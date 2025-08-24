import os
import threading
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta
import math
from werkzeug.utils import secure_filename
import uuid
import webbrowser
from rev import *
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from m3u8dl import *
import math


def format_time(seconds):
    return str(timedelta(seconds=seconds)).split('.')[0]


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
ON_START = False

# Asegurar que la carpeta de descargas existe
#os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Estructura para almacenar el historial
download_history = []


def get_history_file():
    return 'download_history.json'

def createID(count=8):
    from random import randrange
    map = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    id = ''
    i = 0
    while i<count:
        rnd = randrange(len(map))
        id+=map[rnd]
        i+=1
    return id

download_history_sizes = {}
def load_history(filter=None):
    global Cloud_Auth
    global download_history
    global download_history_sizes
    try:
        download_history.clear()
        with open('auth.json', 'r') as f:
                Cloud_Auth = json.load(f)
        settings = {}
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        cli = RevCli(settings['username'],settings['password'],host=settings['cloudHost'],type=settings['authType'])
        cli.session.cookies.update(Cloud_Auth['cookies'])
        sids = cli.get_sids()
        for sid in sids:
            wit_size = False
            files = cli.get_files_from_sid(sid,False)
            size = 0
            parts = []
            filename = ''
            patron = r'^file\d+\.temp$'
            for f in files:
                if not re.match(patron, f['name']):
                    if '.temp' in f['name']:
                        size = int(f['name'].split('.temp')[1])
                        filename = f['name'].split('.temp')[0]
                    else:
                        filename = f['name']
                        size = cli.get_filesize_from_url(f['url'])
                    parts.append(f['url'])
                    break
            index = 0
            for fin in files:
                index += 1
                for f in files:
                    if f['name'] == f'file{index}.temp':
                        parts.append(f['url'])
                        break
            if filename:
                if filter:
                    if filter == filename:
                        add_to_history(filename,size,sid,parts)
                else:
                    add_to_history(filename,size,sid,parts)
        return download_history
    except Exception as ex:print(ex)
    return []

def save_history():
    global download_history
    history_file = get_history_file()
    with open(history_file, 'w') as f:
        json.dump(download_history, f)

def save_auth():
    global Cloud_Auth
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

def add_to_history(filename, size,cloud_sid,parts=[]):
    global download_history
    global download_history_sizes
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    # Calcular tamaño total actual
    total_size = sum(item['size'] for item in download_history)
    
    # Verificar límite de almacenamiento
    if total_size + size > settings['downLimit'] * 1024**3:
        return False
    
    # Agregar al historial
    download_history_sizes[filename] = size
    download_history.append({
        'filename': filename,
        'size': size,
        'timestamp': datetime.now().isoformat(),
        'parts': parts,
        'cloud_sid':cloud_sid
    })
    
    # Mantener solo los últimos 100 registros
    if len(download_history) > 100:
        download_history.pop(0)
    
    save_history()
    return True

def clear_history():
    global download_history
    global download_history_sizes
    global Cloud_Auth
    cli = RevCli(host=Cloud_Auth['host'],type=Cloud_Auth['type'])
    cli.session.cookies.update(Cloud_Auth['cookies'])
    cli.delete_all_sid()
    download_history.clear()
    download_history_sizes = {}
    save_history()
    return True

@app.route('/api/history', methods=['GET', 'DELETE'])
def handle_history():
    global Cloud_Auth
    global download_history
    filename = request.args.get('filename',None)
    print(filename)
    download_history = load_history(filter=filename)
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    if request.method == 'GET':
        return jsonify({
            'history': download_history,
            'total_size': sum(item['size'] for item in download_history),
            'max_size': settings['downLimit'] * 1024**3,
            'cookies':Cloud_Auth['cookies'],
            'settings':settings
        })
    elif request.method == 'DELETE':
        if clear_history():
            return jsonify({'success': True})
        return jsonify({'success': False}), 500

@app.route('/api/downloads', methods=['GET', 'DELETE'])
def handle_downloads():
    global downloads
    if request.method == 'GET':
        dl_list = []
        for id in downloads:
            if downloads[id]['status'] == 'completed' or downloads[id]['status'] == 'error':
                continue
            item = {}
            item['id'] = id
            item['name'] = downloads[id]['filename']
            item['size'] = downloads[id]['total_size']
            dl_list.append(item)
        return jsonify(dl_list)
    elif request.method == 'DELETE':
        downloads.clear()
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
        max_split_temp = (settings['splitSize']*1024*1024)

        # Variables para tracking del progreso
        part_index = 1
        part_total = math.ceil(file_size/max_split_temp)
        if part_total<=0:
            part_total=1

        def upload_progress(filename, bytes_read, total_len, speed, time, args):
            nonlocal part_index,part_total,download_id
            try:
                eta = format_time(time)
                if part_total>1:
                    eta = f' {part_index}/{part_total} Partes    [ {format_time(time)} ]'

                if download_id in downloads:
                    downloads[download_id].update({
                        'upload_progress': int(bytes_read/total_len*100),
                        'uploaded': bytes_read,
                        'upload_speed': speed,
                        'upload_eta': eta,
                        'upload_status': 'uploading'
                    })
            except Exception as e:
                print(f"Error in upload_progress: {e}")

        public_url = ''

        if loged:
            Cloud_Auth['cookies'] = revCli.getsession().cookies.get_dict()
            Cloud_Auth['host'] = revCli.host
            Cloud_Auth['type'] = revCli.type
            save_auth()

            sid = revCli.create_sid()

            parts = []
            
            
            if file_size > max_split_temp:
                with open(filepath,'rb') as f:
                    read_max = 1 * 1024 * 1024
                    total_read = 0
                    read = 0
                    temp_index = 0
                    temp = filepath + f'.temp{file_size}'
                    temp_file = open(temp,'wb')
                    while True:
                        chunk = f.read(max_split_temp)
                        if not chunk:
                            break
                        temp_file.write(chunk)
                        read += len(chunk)
                        total_read += len(chunk)
                        if read>=max_split_temp or total_read>=file_size:
                            temp_index += 1
                            temp_file.close()
                            total_read = 0
                            public_url = revCli.upload(temp,upload_progress,sid=sid,args=(download_id))
                            if download_id in downloads:
                                downloads[download_id].update({
                                        'status':'uploading'
                                    })
                            parts.append(public_url)
                            os.unlink(temp)
                            temp = f'file{temp_index}.temp'
                            temp_file = open(temp,'wb')
                            part_index += 1
            else:
                public_url = revCli.upload(filepath,upload_progress,sid=sid,args=(download_id))
                parts.append(public_url)


            add_to_history(filepath,file_size,sid,parts)
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


def is_m3u8_url(url):
    """Verifica si una URL es un archivo m3u8"""
    return url.lower().endswith('.m3u8') or 'm3u8' in url.lower()              
                    # Calcular progreso descarga

def download_and_upload(download_id, url):
    try:
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
            'upload_eta': '--:--:--',
            'public_url': None,
            'stop_event': threading.Event(),
            'start_time': time.time(),
            'message': ''
        }
        
        # Verificar si es un archivo M3U8
        if is_m3u8_url(url):
            # Usar M3U8Downloader para streams
            downloader = M3U8Downloader(max_workers=3, timeout=30, retries=2)
            
            # Estimar tamaño
            size_info = downloader.estimate_m3u8_size(url)
            if 'error' in size_info:
                downloads[download_id].update({
                    'status': 'error',
                    'message': f'Error estimando tamaño: {size_info["error"]}'
                })
                return
            
            total_size = size_info['estimated_total_bytes']
            filename = f"stream_{download_id[:8]}.ts"
            
            if limited(total_size):
                downloads[download_id].update({
                    'status': 'error',
                    'upload_status': 'Error Limited!',
                    'message': "A exedido el limite de Archivos, Limpie el Historial!."
                })
                return
            
            downloads[download_id].update({
                'filename': filename,
                'total_size': total_size
            })
            
            # Descargar el stream
            filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
            
            def progress_m3u8(current, total, percentage, current_speed, avg_speed, eta, elapsed):
                if downloads[download_id]['stop_event'].is_set():
                    downloader.cancel_download()
                    return
                downloads[download_id].update({
                    'downloaded': current * (total_size / total) if total > 0 else 0,
                    'download_speed': current_speed,  # Convertir KB/s a Bytes/s
                    'download_eta': format_time(eta)
                })
            
            downloader.set_progress_callback(progress_m3u8)
            
            result = downloader.download(url, filepath, f"temp_segments_{download_id}")
            
            if not result['success']:
                downloads[download_id].update({
                    'status': 'error',
                    'message': result.get('error', 'Error desconocido en la descarga M3U8')
                })
                return
                
            downloads[download_id]['status'] = 'uploading'
            
        else:
            # Descarga normal de archivo (código original)
            with requests.get(url, stream=True, timeout=10) as r:
                r.raise_for_status()
                
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
                        'message': "A exedido el limite de Archivos, Limpie el Historial!."
                    })
                    return
                
                downloads[download_id].update({
                    'filename': secure_filename(filename),
                    'total_size': total_size
                })
                
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
                
                downloads[download_id]['status'] = 'uploading'
        
        # Subir el archivo (código original)
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

        
def On_Start_Thread():
    global Cloud_Auth
    global download_history
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    cli = RevCli(settings['username'],settings['password'],host=settings['cloudHost'],type=settings['authType'])
    loged = cli.login()
    if loged:
        Cloud_Auth['cookies'] = cli.session.cookies.get_dict()
        Cloud_Auth['host'] = cli.host
        Cloud_Auth['type'] = cli.type
        save_auth();
    download_history = load_history()

@app.route('/')
def index():
    global ON_START
    app_client = request.user_agent.string
    if not ON_START :
        On_Start_Thread()
        ON_START = True
    if app_client:
        if app_client == 'ObiClientApp/1.0 GeckoFX60':
            if not ON_START:
                On_Start_Thread()
                ON_START = True
    return render_template('index.html')

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
        return jsonify({'status': 'uploading'})
    
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
        'upload_eta': download.get('upload_eta', '--:--:--'),
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
    if download_id in downloads:
        return render_template(INDEX_HTML,dl_id=download_id)
    else:
        return redirect('/')

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    settings = {}
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    # Verificar autenticación
    auth = request.headers.get('Authorization')
    if not auth or auth != settings['masterPassword']:
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
        settings = {}
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        # Verificar la contraseña
        if password == settings['masterPassword']:
            return jsonify({
                'success': True,
                'loged': True,
                'message': 'Autenticación exitosa',
                'is_admin':True
            })
        elif password == settings['clientPassword']:
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

@app.route('/resources/<path:filename>')
def serve_resource(filename):
    RESOURCE_DIR = 'resources'
    return send_from_directory(RESOURCE_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, threaded=True,port=443)