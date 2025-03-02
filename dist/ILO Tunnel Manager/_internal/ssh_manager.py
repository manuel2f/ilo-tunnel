import os
import subprocess
from PyQt6.QtCore import QObject, QProcess, pyqtSignal

class SSHManager(QObject):
    output_ready = pyqtSignal(str)
    error_ready = pyqtSignal(str)
    process_finished = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
    
    def create_tunnel(self, key_path, ssh_port, port_mappings, user, gateway):
        """
        Create SSH tunnel with specified parameters
        
        Args:
            key_path (str): Path to SSH key
            ssh_port (int): SSH port number
            port_mappings (list): List of port mappings in format "local_ip:local_port:remote_host:remote_port"
            user (str): SSH username
            gateway (str): Gateway address
        """
        cmd = ["sudo", "ssh", "-i", os.path.expanduser(key_path), "-p", str(ssh_port)]
        
        # Add port mappings
        for mapping in port_mappings:
            cmd.extend(["-L", mapping])
        
        # Add destination
        cmd.append(f"{user}@{gateway}")
        
        self.output_ready.emit(f"Running command: {' '.join(cmd)}")
        
        # Start process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(lambda code, _: self.process_finished.emit(code))
        
        self.process.start(cmd[0], cmd[1:])
    
    def stop_tunnel(self):
        """Stop the running SSH tunnel"""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(3000):  # Wait 3 seconds
                self.process.kill()
            return True
        return False
    
    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.output_ready.emit(data)
    
    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.error_ready.emit(data)
