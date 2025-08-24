import os
import time
import requests
import threading
import queue
from urllib.parse import urljoin
from typing import List, Dict, Optional, Callable, Tuple

class M3U8Downloader:
    def __init__(self, max_workers=3, timeout=30, retries=2,app=None):
        self.max_workers = max_workers
        self.timeout = timeout
        self.retries = retries
        self.progress_callback = None
        self.is_downloading = False
        self.cancel_requested = False
        self.lock = threading.Lock()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.example.com/',
        }
        
        # Estadísticas de descarga
        self.downloaded_count = 0
        self.total_segments = 0
        self.download_speeds = []
        self.start_time = 0
        self.segment_queue = queue.Queue()
        self.workers = []
    
    def set_progress_callback(self, callback: Callable):
        self.progress_callback = callback

    def estimate_m3u8_size(self, m3u8_url: str, sample_segments: int = 3) -> Dict:
        """Estima el tamaño total del stream"""
        try:
            response = requests.get(m3u8_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.text
            segments = self._parse_m3u8(m3u8_url, content)
            
            if not segments:
                return {'error': 'No se encontraron segmentos'}
            
            total_segments = len(segments)
            
            # Seleccionar segmentos de muestra
            if total_segments <= sample_segments:
                sample_indices = list(range(total_segments))
            else:
                sample_indices = [0, total_segments // 2, total_segments - 1]
                if sample_segments > 3:
                    step = total_segments // sample_segments
                    sample_indices = [i * step for i in range(sample_segments)]
            
            total_sample_size = 0
            successful_samples = 0
            segment_sizes = []
            
            # Obtener tamaños de segmentos de muestra
            for i in sample_indices:
                try:
                    response = requests.head(segments[i], headers=self.headers, timeout=10)
                    if response.status_code == 200 and 'Content-Length' in response.headers:
                        size = int(response.headers['Content-Length'])
                        total_sample_size += size
                        segment_sizes.append(size)
                        successful_samples += 1
                    else:
                        # Intentar con GET si HEAD falla
                        response = requests.get(segments[i], headers=self.headers, timeout=10, stream=True)
                        if response.status_code == 200 and 'Content-Length' in response.headers:
                            size = int(response.headers['Content-Length'])
                            total_sample_size += size
                            segment_sizes.append(size)
                            successful_samples += 1
                except:
                    continue
            
            if successful_samples == 0:
                return {'error': 'No se pudieron obtener tamaños de segmentos'}
            
            # Calcular estimaciones
            avg_segment_size = total_sample_size / successful_samples
            estimated_total_size = avg_segment_size * total_segments
            
            return {
                'success': True,
                'total_segments': total_segments,
                'sampled_segments': successful_samples,
                'estimated_total_bytes': int(estimated_total_size),
                'estimated_total_mb': round(estimated_total_size / (1024 * 1024), 2),
                'estimated_total_gb': round(estimated_total_size / (1024 * 1024 * 1024), 2),
                'avg_segment_size_bytes': int(avg_segment_size),
                'segment_sizes': segment_sizes,
                'confidence': f"{(successful_samples / len(sample_indices)) * 100:.1f}%"
            }
            
        except Exception as e:
            return {'error': f'Error al estimar tamaño: {str(e)}'}
    
    def _download_segment_worker(self):
        """Worker que procesa segmentos de la cola"""
        while not self.cancel_requested:
            try:
                # Obtener segmento de la cola con timeout
                segment_data = self.segment_queue.get(timeout=1)
                if segment_data is None:  # Señal de finalización
                    break
                    
                segment_index, segment_url, segment_file = segment_data
                
                success, speed = self._download_with_retry(segment_url, segment_file, segment_index)
                
                if success:
                    with self.lock:
                        self.downloaded_count += 1
                        if speed > 0:
                            self.download_speeds.append(speed)
                    self._update_progress(speed)
                else:
                    print(f"Error en segmento {segment_index + 1}")
                    
                self.segment_queue.task_done()
                
            except queue.Empty:
                if self.cancel_requested:
                    break
                continue
            except Exception as e:
                print(f"Error en worker: {e}")
                break
    
    def _download_with_retry(self, url: str, output_path: str, segment_index: int) -> Tuple[bool, float]:
        """Descarga un segmento con reintentos"""
        for attempt in range(self.retries + 1):
            if self.cancel_requested:
                return False, 0.0
                
            try:
                start_time = time.time()
                
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=self.timeout,
                    stream=True
                )
                response.raise_for_status()
                
                # Descargar contenido
                content = b''
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancel_requested:
                        return False, 0.0
                    if chunk:
                        content += chunk
                
                download_time = time.time() - start_time
                speed = len(content) / download_time / 1024 if download_time > 0 else 0
                
                # Guardar archivo
                with open(output_path, 'wb') as f:
                    f.write(content)
                
                return True, speed
                
            except requests.exceptions.RequestException as e:
                if attempt == self.retries:
                    print(f"Error en segmento {segment_index} después de {self.retries} intentos: {e}")
                    return False, 0.0
                time.sleep(1)
        
        return False, 0.0
    
    def _parse_m3u8(self, m3u8_url: str, content: str) -> List[str]:
        """Parsea el contenido m3u8 y devuelve la lista de segmentos"""
        segments = []
        lines = content.strip().split('\n')
        
        if 'manifest.m3u8' in m3u8_url:
            base_url = '/'.join(m3u8_url.split('/')[:-1]) + '/'
        else:
            base_url = m3u8_url.rsplit('/', 1)[0] + '/' if '/' in m3u8_url else m3u8_url
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('http'):
                    segments.append(line)
                else:
                    segments.append(urljoin(base_url, line))
        
        return segments
    
    def _update_progress(self, speed: float = 0):
        """Actualiza el progreso de la descarga"""
        if self.progress_callback and self.total_segments > 0:
            with self.lock:
                percentage = (self.downloaded_count / self.total_segments) * 100
                
                elapsed_time = time.time() - self.start_time
                if self.downloaded_count > 0 and elapsed_time > 0:
                    segments_per_second = self.downloaded_count / elapsed_time
                    remaining_segments = self.total_segments - self.downloaded_count
                    eta = remaining_segments / segments_per_second if segments_per_second > 0 else 0
                    avg_speed = sum(self.download_speeds) / len(self.download_speeds) if self.download_speeds else 0
                else:
                    eta = 0
                    avg_speed = 0
                
                # Llamar al callback dentro del contexto de Flask si es necesario
                try:
                    self.progress_callback(
                        self.downloaded_count,
                        self.total_segments,
                        percentage,
                        speed,
                        avg_speed,
                        eta,
                        elapsed_time
                        )
                except Exception as e:
                    print(f"Error en callback de progreso: {e}")
    
    def get_stream_info(self, m3u8_url: str) -> Optional[Dict]:
        """Obtiene información sobre el stream"""
        try:
            response = requests.get(m3u8_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.text
            segments = self._parse_m3u8(m3u8_url, content)
            
            return {
                'total_segments': len(segments),
                'first_segments': segments[:3] if segments else [],
                'content_preview': content[:200] + "..." if len(content) > 200 else content
            }
            
        except Exception as e:
            print(f"Error obteniendo información del stream: {e}")
            return None
    
    def cancel_download(self):
        """Cancela la descarga en curso"""
        self.cancel_requested = True
        # Limpiar la cola
        while not self.segment_queue.empty():
            try:
                self.segment_queue.get_nowait()
                self.segment_queue.task_done()
            except queue.Empty:
                break
        
        # Esperar a que los workers terminen
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=1)
    
    def download(self, m3u8_url: str, output_file: str = "video_output.ts", 
                temp_dir: str = "temp_segments") -> Dict:
        """Descarga el stream m3u8 usando threading nativo"""
        if self.is_downloading:
            return {'success': False, 'error': 'Ya hay una descarga en progreso'}
        
        # Reiniciar estado
        self.is_downloading = True
        self.cancel_requested = False
        self.downloaded_count = 0
        self.download_speeds = []
        self.start_time = time.time()
        self.workers = []
        
        result = {
            'success': False,
            'downloaded_segments': 0,
            'total_segments': 0,
            'failed_segments': [],
            'output_file': output_file,
            'time_elapsed': 0,
            'average_speed': 0
        }
        
        try:
            print("Obteniendo lista de segmentos...")
            response = requests.get(m3u8_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.text
            segments = self._parse_m3u8(m3u8_url, content)
            
            if not segments:
                result['error'] = "No se encontraron segmentos en el archivo m3u8"
                return result
            
            self.total_segments = len(segments)
            result['total_segments'] = self.total_segments
            print(f"Encontrados {len(segments)} segmentos")
            
            # Crear directorio temporal
            os.makedirs(temp_dir, exist_ok=True)
            
            failed_segments = []
            segment_files = []
            
            # Iniciar workers
            for i in range(self.max_workers):
                worker = threading.Thread(target=self._download_segment_worker)
                worker.daemon = True
                worker.start()
                self.workers.append(worker)
            
            # Agregar segmentos a la cola
            for i, segment_url in enumerate(segments):
                if self.cancel_requested:
                    break
                    
                segment_file = os.path.join(temp_dir, f"segment_{i:06d}.ts")
                segment_files.append((i, segment_file))
                self.segment_queue.put((i, segment_url, segment_file))
            
            # Esperar a que se procesen todos los segmentos
            self.segment_queue.join()
            
            # Verificar si se canceló
            if self.cancel_requested:
                result['error'] = "Descarga cancelada por el usuario"
                return result
            
            # Combinar segmentos si se descargaron algunos
            if self.downloaded_count > 0:
                print("Combinando segmentos...")
                with open(output_file, 'wb') as output:
                    for i, segment_file in sorted(segment_files, key=lambda x: x[0]):
                        if os.path.exists(segment_file):
                            try:
                                with open(segment_file, 'rb') as seg:
                                    output.write(seg.read())
                                os.remove(segment_file)
                            except Exception as e:
                                print(f"Error combinando segmento {i}: {e}")
                                failed_segments.append(i)
                
                # Limpiar directorio temporal
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
                
                # Calcular resultados finales
                time_elapsed = time.time() - self.start_time
                avg_speed = (sum(self.download_speeds) / len(self.download_speeds)) if self.download_speeds else 0
                
                result.update({
                    'success': True,
                    'downloaded_segments': self.downloaded_count,
                    'failed_segments': failed_segments,
                    'success_rate': (self.downloaded_count / len(segments)) * 100,
                    'time_elapsed': time_elapsed,
                    'average_speed': avg_speed,
                    'total_size_mb': (os.path.getsize(output_file) / (1024 * 1024)) if os.path.exists(output_file) else 0
                })
                
            else:
                result['error'] = "No se pudieron descargar segmentos"
            
        except Exception as e:
            result['error'] = f"Error general: {e}"
            import traceback
            traceback.print_exc()
        
        finally:
            # Señalizar a los workers que terminen
            for _ in range(self.max_workers):
                self.segment_queue.put(None)
            
            # Esperar a que los workers terminen
            for worker in self.workers:
                if worker.is_alive():
                    worker.join(timeout=2)
            
            # Limpiar y finalizar
            time_elapsed = time.time() - self.start_time
            result['time_elapsed'] = time_elapsed
            self.is_downloading = False
            
            # Última actualización de progreso
            if self.progress_callback:
                try:
                    self.progress_callback(
                        downloaded=self.downloaded_count,
                        total=self.total_segments,
                        percentage=(self.downloaded_count / self.total_segments * 100) if self.total_segments > 0 else 0,
                        current_speed=0,
                        average_speed=result.get('average_speed', 0),
                        eta=0,
                        elapsed_time=time_elapsed
                    )
                except Exception as e:
                    print(f"Error en callback final: {e}")
            
            print(f"\nTiempo total: {time_elapsed:.2f} segundos")
            if result.get('success', False):
                print(f"Descarga completada: {result['downloaded_segments']}/{result['total_segments']} segmentos")
                print(f"Tasa de éxito: {result['success_rate']:.1f}%")
            else:
                print(f"Error: {result.get('error', 'Desconocido')}")
            
            return result