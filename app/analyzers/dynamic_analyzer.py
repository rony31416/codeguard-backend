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
        prints a JSON result dict.  Used by both Docker and subprocess paths.

        The wrapper uses an isolated execution namespace (_cg_ns) so that
        variables defined in the user's code (e.g. `result = ...`) cannot
        overwrite the wrapper's own bookkeeping variable `_cg_result`.
        """
        # Use repr() so any string content is safely escaped
        code_repr = repr(self.code)
        return f'''import sys, json, traceback
_cg_code = {code_repr}
_cg_result = {{"success": False, "output": "", "error": None, "error_type": None, "traceback": None}}
_cg_ns = {{}}
try:
    exec(compile(_cg_code, "<codeguard>", "exec"), _cg_ns)
    _cg_result["success"] = True
    _cg_result["output"] = "Code executed successfully"
except ZeroDivisionError as _cg_e:
    _cg_result["error_type"] = "ZeroDivisionError"
    _cg_result["error"] = str(_cg_e)
    _cg_result["traceback"] = traceback.format_exc()
except AttributeError as _cg_e:
    _cg_result["error_type"] = "AttributeError"
    _cg_result["error"] = str(_cg_e)
    _cg_result["traceback"] = traceback.format_exc()
except TypeError as _cg_e:
    _cg_result["error_type"] = "TypeError"
    _cg_result["error"] = str(_cg_e)
    _cg_result["traceback"] = traceback.format_exc()
except NameError as _cg_e:
    _cg_result["error_type"] = "NameError"
    _cg_result["error"] = str(_cg_e)
    _cg_result["traceback"] = traceback.format_exc()
except Exception as _cg_e:
    _cg_result["error_type"] = type(_cg_e).__name__
    _cg_result["error"] = str(_cg_e)
    _cg_result["traceback"] = traceback.format_exc()
print(json.dumps(_cg_result))
'''

    def _execute_in_sandbox(self) -> Dict[str, Any]:
        """Execute code in isolated Docker container."""
        wrapper_code = self._build_wrapper()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(wrapper_code)
            temp_file = f.name

        try:
            temp_filename = os.path.basename(temp_file)
            temp_dir = os.path.dirname(temp_file)

            # Convert Windows path to Docker-for-Windows format: C:\path -> /c/path
            if platform.system() == 'Windows':
                temp_dir = temp_dir.replace('\\', '/')   # backslash → forward slash
                if len(temp_dir) >= 2 and temp_dir[1] == ':':
                    temp_dir = '/' + temp_dir[0].lower() + temp_dir[2:]

            logger.info(f"Docker sandbox: mounting {temp_dir} -> /code, running {temp_filename}")

            container = self.client.containers.run(
                'python:3.10-slim',
                f'python /code/{temp_filename}',
                volumes={temp_dir: {'bind': '/code', 'mode': 'ro'}},
                working_dir='/code',
                network_disabled=True,
                mem_limit='128m',
                cpu_quota=50000,
                remove=False,   # keep briefly so we can read logs
                detach=True,
            )

            # Wait with timeout
            try:
                container.wait(timeout=self.timeout)
                raw_output = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            except Exception:
                try:
                    container.stop(timeout=1)
                except Exception:
                    pass
                return {"success": False, "error": "Execution timed out", "error_type": "TimeoutError"}
            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

            # Extract last JSON line from output (ignore any prior print/debug lines)
            result = self._parse_json_output(raw_output)
            return result

        except docker.errors.ContainerError as e:
            logger.error(f"Container error: {e}")
            return {"success": False, "error": str(e), "error_type": "ContainerError"}
        except docker.errors.ImageNotFound:
            logger.error("Docker image python:3.10-slim not found")
            return {
                "success": False,
                "error": "Docker image 'python:3.10-slim' not found. Run: docker pull python:3.10-slim",
                "error_type": "ImageNotFound",
            }
        except Exception as e:
            logger.error(f"Docker sandbox error: {e}")
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
    
    @staticmethod
    def _parse_json_output(raw_output: str) -> dict:
        """Find the last JSON object in container stdout.

        The wrapper always prints a single JSON line, but the container may
        also emit Python warnings or other lines beforehand.  We scan from
        the end of the output and return the first line that parses cleanly.
        """
        for line in reversed(raw_output.splitlines()):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    return json.loads(line)
                except Exception:
                    continue
        # Fallback — return raw output for debugging
        return {
            "success": False,
            "output": raw_output,
            "error": "No JSON result found in container output",
            "error_type": "ParseError",
        }

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
