"""LLaMA server manager - subprocess lifecycle management."""

import subprocess
import time
import os
import signal
from typing import Optional, Dict, Any
from datetime import datetime

from contracts.models.model_config import ModelSpec


class LlamaServerManager:
    """Manages llama-server subprocess lifecycle."""

    def __init__(self, llama_server_path: Optional[str] = None, external_port: Optional[int] = None):
        """
        Initialize server manager.

        Args:
            llama_server_path: Path to llama-server binary (auto-detect if None)
            external_port: Port of external llama-server (if running separately)
        """
        self.llama_server_path = llama_server_path or self._find_llama_server()
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.restart_count: int = 0
        self.current_model: Optional[ModelSpec] = None
        self.port: int = external_port or 8080
        
        # Check if external llama-server is already running
        if external_port or self._check_existing_server():
            self.pid = 0  # External server
            self.start_time = datetime.now()
    
    def spawn(self, model: ModelSpec, gpu_layers: int = -1) -> bool:
        """
        Spawn llama-server subprocess with specified model.
        
        Args:
            model: Model specification to load
            gpu_layers: Number of layers to offload to GPU (-1 for all)
        
        Returns:
            True if successfully spawned
        """
        if not self.llama_server_path:
            return False
        
        args = [
            self.llama_server_path,
            "--model", model.path,
            "--port", str(self.port),
            "--host", "127.0.0.1",
            "--ctx-size", str(model.context_length),
        ]
        
        # GPU offloading
        if gpu_layers != -1:
            args.extend(["--n-gpu-layers", str(gpu_layers)])
        else:
            args.extend(["--n-gpu-layers", "999"])  # All layers
        
        # Quantization
        if model.quant:
            args.extend(["--quantization", model.quant])
        
        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None
            )
            self.pid = self.process.pid
            self.start_time = datetime.now()
            self.current_model = model
            
            # Wait for server to start
            if self._wait_for_server(timeout=30):
                return True
            else:
                self.process = None
                self.pid = None
                return False
                
        except Exception as e:
            print(f"Failed to spawn llama-server: {e}")
            self.process = None
            return False
    
    def restart(self) -> bool:
        """
        Restart llama-server with same model.
        
        Returns:
            True if successfully restarted
        """
        if not self.current_model:
            return False
        
        self.stop()
        self.restart_count += 1
        return self.spawn(self.current_model)
    
    def stop(self) -> None:
        """Stop llama-server subprocess."""
        if self.process:
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(self.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
                self.process.wait(timeout=10)
            except Exception:
                if self.process and self.process.poll() is None:
                    self.process.kill()
            
            self.process = None
            self.pid = None
            self.start_time = None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get server status.
        
        Returns:
            Status dictionary with pid, status, uptime, etc.
        """
        if not self.process:
            return {
                "running": False,
                "pid": None,
                "status": "stopped",
                "uptime_s": 0,
                "restart_count": self.restart_count,
                "current_model": None
            }
        
        # Check if process is still running
        if self.process.poll() is not None:
            return {
                "running": False,
                "pid": self.pid,
                "status": "crashed",
                "uptime_s": 0,
                "restart_count": self.restart_count,
                "current_model": self.current_model.path if self.current_model else None
            }
        
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "running": True,
            "pid": self.pid,
            "status": "running",
            "uptime_s": uptime,
            "restart_count": self.restart_count,
            "current_model": self.current_model.path if self.current_model else None
        }
    
    def _find_llama_server(self) -> Optional[str]:
        """Find llama-server binary in PATH."""
        import shutil
        return shutil.which("llama-server")

    def _check_existing_server(self, timeout: int = 2) -> bool:
        """Check if llama-server is already running on port."""
        import httpx
        try:
            response = httpx.get(f"http://127.0.0.1:{self.port}/health", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def _wait_for_server(self, timeout: int = 30) -> bool:
        """
        Wait for server to become responsive.
        
        Args:
            timeout: Maximum seconds to wait
        
        Returns:
            True if server is responsive
        """
        import httpx
        
        start = time.time()
        while time.time() - start < timeout:
            if self.process and self.process.poll() is not None:
                return False
            
            try:
                response = httpx.get(f"http://127.0.0.1:{self.port}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            
            time.sleep(0.5)
        
        return False
