import docker
import json
import subprocess
import sys
import tempfile
import os
import platform
import logging
from typing import Dict, Any

logger = logging.getLogger("codeguard.dynamic")

# Imports that indicate dangerous system-level code — skip subprocess execution
_DANGEROUS_IMPORTS = {
    "os", "subprocess", "shutil", "socket", "ctypes", "multiprocessing",
    "threading", "signal", "pty", "tty", "termios", "resource",
}


class DynamicAnalyzer:
    def __init__(self, code: str, timeout: int = 5):
        self.code = code
        self.timeout = timeout
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialised")
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
            self.client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self) -> Dict[str, Any]:
        """Execute code and capture runtime errors.

        Priority:
          1. Docker sandbox  (full isolation)
          2. Subprocess fallback  (when Docker unavailable, e.g. Render)
          3. Skip  (code contains dangerous imports)
        """
        if self.client:
            try:
                result = self._execute_in_sandbox()
                return self._classify_runtime_errors(result)
            except Exception as e:
                logger.error(f"Docker dynamic analysis error: {e}")
                # Fall through to subprocess

        # Subprocess fallback
        if self._is_safe_for_subprocess():
            logger.info("Docker unavailable — using subprocess fallback")
            try:
                result = self._execute_in_subprocess()
                return self._classify_runtime_errors(result)
            except Exception as e:
                logger.error(f"Subprocess dynamic analysis error: {e}")

        return {
            "execution_error": False,
            "error_message": "Dynamic analysis skipped (Docker unavailable and code contains system imports)",
            "wrong_attribute": {"found": False},
            "wrong_input_type": {"found": False},
            "name_error": {"found": False},
            "other_error": {"found": False},
        }

    # ------------------------------------------------------------------
    # Subprocess fallback (runs on Render where Docker daemon is absent)
    # ------------------------------------------------------------------

    def _is_safe_for_subprocess(self) -> bool:
        """Rough safety check: refuse execution if dangerous imports present."""
        import re
        for imp in _DANGEROUS_IMPORTS:
            if re.search(rf'\bimport\s+{imp}\b|\bfrom\s+{imp}\b', self.code):
                logger.warning(f"Skipping subprocess execution — dangerous import '{imp}' detected")
                return False
        return True

    def _execute_in_subprocess(self) -> Dict[str, Any]:
        """Execute the wrapped code in a child subprocess with a timeout."""
        wrapper_code = self._build_wrapper()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(wrapper_code)
            temp_file = f.name

        try:
            proc = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            output = proc.stdout.strip()
            if not output:
                output = proc.stderr.strip()
            try:
                return json.loads(output)
            except Exception:
                return {
                    "success": False,
                    "output": output,
                    "error": "Failed to parse subprocess output",
                    "error_type": "ParseError",
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timed out",
                "error_type": "TimeoutError",
            }
        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass
    
    # ------------------------------------------------------------------
    # Shared wrapper builder
    # ------------------------------------------------------------------

    def _build_wrapper(self) -> str:
        """Build a self-contained Python script that executes self.code and
        prints a JSON result dict.  Used by both Docker and subprocess paths."""
        # Use repr() so any string content is safely escaped
        code_repr = repr(self.code)
        return f'''import sys, json, traceback
code_to_run = {code_repr}
result = {{"success": False, "output": "", "error": None, "error_type": None, "traceback": None}}
try:
    exec(compile(code_to_run, "<codeguard>", "exec"))
    result["success"] = True
    result["output"] = "Code executed successfully"
except ZeroDivisionError as e:
    result["error_type"] = "ZeroDivisionError"
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()
except AttributeError as e:
    result["error_type"] = "AttributeError"
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()
except TypeError as e:
    result["error_type"] = "TypeError"
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()
except NameError as e:
    result["error_type"] = "NameError"
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()
except Exception as e:
    result["error_type"] = type(e).__name__
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()
print(json.dumps(result))
'''

    def _execute_in_sandbox(self) -> Dict[str, Any]:
        """Execute code in isolated Docker container"""
        wrapper_code = self._build_wrapper()

        # Create temporary file with wrapper code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(wrapper_code)
            temp_file = f.name
        
        try:
            # Get the directory and filename separately
            temp_dir = os.path.dirname(temp_file)
            temp_filename = os.path.basename(temp_file)
            
            # For Windows, convert path format
            if platform.system() == 'Windows':
                # Convert Windows path to Docker volume format
                temp_dir = temp_dir.replace('\\', '/')
                if ':' in temp_dir:
                    # Convert C:\path to /c/path
                    drive, path = temp_dir.split(':', 1)
                    temp_dir = f'/{drive.lower()}{path}'
            
            print(f"Mounting: {temp_dir} -> /code")
            print(f"Executing: {temp_filename}")
            
            # Run in Docker container
            container = self.client.containers.run(
                'python:3.10-slim',
                f'python /code/{temp_filename}',
                volumes={temp_dir: {'bind': '/code', 'mode': 'ro'}},
                working_dir='/code',
                network_disabled=True,
                mem_limit='128m',
                cpu_quota=50000,
                remove=True,
                detach=True
            )
            
            # Wait for execution with timeout
            try:
                exit_code = container.wait(timeout=self.timeout)
                output = container.logs().decode('utf-8')
            except Exception as timeout_error:
                # Container timed out
                try:
                    container.stop(timeout=1)
                    container.remove()
                except:
                    pass
                return {
                    "success": False,
                    "error": "Execution timed out",
                    "error_type": "TimeoutError"
                }
            
            # Parse JSON result
            try:
                result = json.loads(output)
            except:
                result = {
                    "success": False,
                    "output": output,
                    "error": "Failed to parse execution result",
                    "error_type": "ParseError"
                }
            
            return result
            
        except docker.errors.ContainerError as e:
            print(f"Container error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "ContainerError"
            }
        except docker.errors.ImageNotFound:
            print("Docker image not found. Please build it first.")
            return {
                "success": False,
                "error": "Docker image 'python:3.10-slim' not found. Please run: docker pull python:3.10-slim",
                "error_type": "ImageNotFound"
            }
        except Exception as e:
            print(f"Execution error: {e}")
            import traceback
            print(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "error_type": "ExecutionError"
            }
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _classify_runtime_errors(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Classify runtime errors into bug patterns"""
        classification = {
            "execution_success": result.get("success", False),
            "wrong_attribute": {"found": False},
            "wrong_input_type": {"found": False},
            "name_error": {"found": False},
            "missing_corner_case": {"found": False},
            "other_error": {"found": False}
        }

        if not result.get("success"):
            error_type = result.get("error_type")
            error_msg = result.get("error", "")
            tb = result.get("traceback", "")

            if error_type == "ZeroDivisionError":
                classification["missing_corner_case"] = {
                    "found": True,
                    "error": error_msg,
                    "description": "ZeroDivisionError at runtime — division by zero not guarded",
                    "traceback": tb,
                }
            elif error_type == "AttributeError":
                classification["wrong_attribute"] = {
                    "found": True,
                    "error": error_msg,
                    "traceback": tb
                }
            elif error_type == "TypeError":
                classification["wrong_input_type"] = {
                    "found": True,
                    "error": error_msg,
                    "traceback": tb
                }
            elif error_type == "NameError":
                classification["name_error"] = {
                    "found": True,
                    "error": error_msg,
                    "traceback": tb
                }
            else:
                classification["other_error"] = {
                    "found": True,
                    "error_type": error_type,
                    "error": error_msg,
                    "traceback": tb
                }
        
        return classification
