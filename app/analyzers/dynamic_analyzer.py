import docker
import json
import tempfile
import os
import platform
from typing import Dict, Any

class DynamicAnalyzer:
    def __init__(self, code: str, timeout: int = 5):
        self.code = code
        self.timeout = timeout
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"Docker client initialization failed: {e}")
            self.client = None
    
    def analyze(self) -> Dict[str, Any]:
        """Execute code in Docker sandbox and capture runtime errors"""
        # If Docker is not available, skip dynamic analysis
        if not self.client:
            return {
                "execution_error": False,
                "error_message": "Docker not available - skipping dynamic analysis",
                "wrong_attribute": {"found": False},
                "wrong_input_type": {"found": False},
                "name_error": {"found": False},
                "other_error": {"found": False}
            }
        
        try:
            result = self._execute_in_sandbox()
            return self._classify_runtime_errors(result)
        except Exception as e:
            print(f"Dynamic analysis error: {e}")
            return {
                "execution_error": True,
                "error_message": str(e),
                "wrong_attribute": {"found": False},
                "wrong_input_type": {"found": False},
                "name_error": {"found": False},
                "other_error": {"found": False}
            }
    
    def _execute_in_sandbox(self) -> Dict[str, Any]:
        """Execute code in isolated Docker container"""
        # Escape the code properly for JSON
        escaped_code = self.code.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '').replace('\t', '\\t')
        
        # Create a wrapper script that captures exceptions
        wrapper_code = f'''import sys
import json
import traceback

code_to_run = """{escaped_code}"""

result = {{
    "success": False,
    "output": "",
    "error": None,
    "error_type": None,
    "traceback": None
}}

try:
    exec(code_to_run)
    result["success"] = True
    result["output"] = "Code executed successfully"
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
            "other_error": {"found": False}
        }
        
        if not result.get("success"):
            error_type = result.get("error_type")
            error_msg = result.get("error", "")
            traceback = result.get("traceback", "")
            
            if error_type == "AttributeError":
                classification["wrong_attribute"] = {
                    "found": True,
                    "error": error_msg,
                    "traceback": traceback
                }
            elif error_type == "TypeError":
                classification["wrong_input_type"] = {
                    "found": True,
                    "error": error_msg,
                    "traceback": traceback
                }
            elif error_type == "NameError":
                classification["name_error"] = {
                    "found": True,
                    "error": error_msg,
                    "traceback": traceback
                }
            else:
                classification["other_error"] = {
                    "found": True,
                    "error_type": error_type,
                    "error": error_msg,
                    "traceback": traceback
                }
        
        return classification
