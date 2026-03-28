"""Interactive code execution playground with AI assistance."""

import json
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import base64

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.aws_clients.s3_client import S3Client
from ...shared.utils.logger import get_logger
from ...shared.utils.errors import ServiceError

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: Optional[str]
    execution_time_ms: float
    memory_used_mb: Optional[float]
    exit_code: int


class CodePlayground:
    """
    Interactive code execution playground with multi-language support.
    
    Features:
    - Execute code in 10+ languages
    - Real-time syntax checking
    - AI-powered code completion
    - Inline error explanations
    - Step-by-step debugging
    - Code visualization
    - Share and collaborate
    """

    SUPPORTED_LANGUAGES = {
        "python": {
            "extension": ".py",
            "command": ["python3"],
            "timeout": 30,
        },
        "javascript": {
            "extension": ".js",
            "command": ["node"],
            "timeout": 30,
        },
        "java": {
            "extension": ".java",
            "command": ["java"],
            "timeout": 30,
            "compile": ["javac"],
        },
        "cpp": {
            "extension": ".cpp",
            "command": ["./a.out"],
            "timeout": 30,
            "compile": ["g++", "-o", "a.out"],
        },
        "c": {
            "extension": ".c",
            "command": ["./a.out"],
            "timeout": 30,
            "compile": ["gcc", "-o", "a.out"],
        },
        "go": {
            "extension": ".go",
            "command": ["go", "run"],
            "timeout": 30,
        },
        "rust": {
            "extension": ".rs",
            "command": ["./main"],
            "timeout": 30,
            "compile": ["rustc", "-o", "main"],
        },
        "ruby": {
            "extension": ".rb",
            "command": ["ruby"],
            "timeout": 30,
        },
        "php": {
            "extension": ".php",
            "command": ["php"],
            "timeout": 30,
        },
        "typescript": {
            "extension": ".ts",
            "command": ["ts-node"],
            "timeout": 30,
        },
    }

    def __init__(
        self,
        bedrock_client: Optional[BedrockClient] = None,
        s3_client: Optional[S3Client] = None,
    ):
        """Initialize code playground."""
        self.bedrock_client = bedrock_client or BedrockClient()
        self.s3_client = s3_client or S3Client()
        logger.info("CodePlayground initialized")

    def execute_code(
        self,
        code: str,
        language: str,
        stdin: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Execute code in specified language.
        
        Args:
            code: Source code to execute
            language: Programming language
            stdin: Standard input for the program
            timeout: Execution timeout in seconds
            
        Returns:
            ExecutionResult with output and metadata
        """
        try:
            if language not in self.SUPPORTED_LANGUAGES:
                raise ServiceError(f"Unsupported language: {language}")
            
            lang_config = self.SUPPORTED_LANGUAGES[language]
            timeout = timeout or lang_config["timeout"]
            
            start_time = datetime.now()
            
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code to file
                file_path = os.path.join(
                    temp_dir,
                    f"main{lang_config['extension']}"
                )
                
                with open(file_path, 'w') as f:
                    f.write(code)
                
                # Compile if needed
                if "compile" in lang_config:
                    compile_result = self._compile_code(
                        file_path,
                        lang_config["compile"],
                        temp_dir
                    )
                    
                    if not compile_result["success"]:
                        return ExecutionResult(
                            success=False,
                            output="",
                            error=compile_result["error"],
                            execution_time_ms=0,
                            memory_used_mb=None,
                            exit_code=compile_result["exit_code"],
                        )
                
                # Execute code
                result = self._execute_code(
                    file_path,
                    lang_config["command"],
                    temp_dir,
                    stdin,
                    timeout
                )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            return ExecutionResult(
                success=result["exit_code"] == 0,
                output=result["stdout"],
                error=result["stderr"] if result["stderr"] else None,
                execution_time_ms=execution_time,
                memory_used_mb=None,  # Would need system monitoring
                exit_code=result["exit_code"],
            )
            
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                execution_time_ms=0,
                memory_used_mb=None,
                exit_code=-1,
            )

    def get_code_completion(
        self,
        code: str,
        language: str,
        cursor_position: int,
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered code completion suggestions.
        
        Args:
            code: Current code
            language: Programming language
            cursor_position: Cursor position in code
            
        Returns:
            List of completion suggestions
        """
        try:
            # Extract context around cursor
            before_cursor = code[:cursor_position]
            after_cursor = code[cursor_position:]
            
            prompt = f"""Provide code completion suggestions for {language}.

Code before cursor:
```{language}
{before_cursor}
```

Code after cursor:
```{language}
{after_cursor}
```

Provide 3-5 intelligent completion suggestions in JSON format:
{{
    "suggestions": [
        {{
            "text": "completion text",
            "description": "what this completes",
            "type": "function|variable|keyword|snippet"
        }}
    ]
}}"""

            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3,
            )
            
            try:
                data = json.loads(response)
                return data.get("suggestions", [])
            except json.JSONDecodeError:
                return []
            
        except Exception as e:
            logger.error(f"Error getting code completion: {e}", exc_info=True)
            return []

    def explain_error(
        self,
        code: str,
        language: str,
        error_message: str,
    ) -> Dict[str, Any]:
        """
        Get AI explanation of error and fix suggestions.
        
        Args:
            code: Source code
            language: Programming language
            error_message: Error message from execution
            
        Returns:
            Dictionary with explanation and fixes
        """
        try:
            prompt = f"""Analyze this {language} code error and provide helpful explanation.

Code:
```{language}
{code}
```

Error:
```
{error_message}
```

Provide analysis in JSON format:
{{
    "error_type": "syntax|runtime|logic",
    "explanation": "Clear explanation of what went wrong",
    "cause": "Root cause of the error",
    "fix_suggestions": [
        {{
            "description": "How to fix",
            "code_snippet": "Fixed code snippet"
        }}
    ],
    "learning_tip": "Educational insight about this error"
}}"""

            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.5,
            )
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "error_type": "unknown",
                    "explanation": response,
                    "fix_suggestions": [],
                }
            
        except Exception as e:
            logger.error(f"Error explaining error: {e}", exc_info=True)
            raise ServiceError(f"Failed to explain error: {str(e)}")

    def visualize_code(
        self,
        code: str,
        language: str,
    ) -> Dict[str, Any]:
        """
        Generate code visualization (flowchart, call graph, etc.).
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Dictionary with visualization data
        """
        try:
            prompt = f"""Analyze this {language} code and create a visualization description.

Code:
```{language}
{code}
```

Provide visualization data in JSON format:
{{
    "flowchart": {{
        "nodes": [
            {{"id": "1", "label": "Start", "type": "start"}},
            {{"id": "2", "label": "Process", "type": "process"}}
        ],
        "edges": [
            {{"from": "1", "to": "2"}}
        ]
    }},
    "complexity": {{
        "cyclomatic": 3,
        "cognitive": 5
    }},
    "call_graph": [
        {{"function": "main", "calls": ["helper1", "helper2"]}}
    ],
    "data_flow": "Description of data flow"
}}"""

            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3,
            )
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"error": "Failed to parse visualization data"}
            
        except Exception as e:
            logger.error(f"Error visualizing code: {e}", exc_info=True)
            raise ServiceError(f"Failed to visualize code: {str(e)}")

    def share_code(
        self,
        code: str,
        language: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Share code snippet with unique URL.
        
        Args:
            code: Source code
            language: Programming language
            user_id: User identifier
            title: Optional title
            
        Returns:
            Dictionary with share URL and metadata
        """
        try:
            # Generate unique ID
            share_id = f"code_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create share data
            share_data = {
                "share_id": share_id,
                "code": code,
                "language": language,
                "user_id": user_id,
                "title": title or f"{language} snippet",
                "created_at": datetime.now().isoformat(),
            }
            
            # Save to S3
            key = f"shared-code/{share_id}.json"
            self.s3_client.put_object(
                key=key,
                data=json.dumps(share_data).encode(),
                content_type="application/json",
            )
            
            # Generate presigned URL (valid for 7 days)
            share_url = self.s3_client.generate_presigned_url(
                key=key,
                expiration=604800,  # 7 days
            )
            
            logger.info(f"Shared code: {share_id}")
            
            return {
                "share_id": share_id,
                "share_url": share_url,
                "expires_in_days": 7,
            }
            
        except Exception as e:
            logger.error(f"Error sharing code: {e}", exc_info=True)
            raise ServiceError(f"Failed to share code: {str(e)}")

    def _compile_code(
        self,
        file_path: str,
        compile_command: List[str],
        working_dir: str,
    ) -> Dict[str, Any]:
        """Compile code if needed."""
        try:
            command = compile_command + [file_path]
            
            result = subprocess.run(
                command,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Compilation timeout",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
            }

    def _execute_code(
        self,
        file_path: str,
        execute_command: List[str],
        working_dir: str,
        stdin: Optional[str],
        timeout: int,
    ) -> Dict[str, Any]:
        """Execute code."""
        try:
            command = execute_command + [file_path]
            
            result = subprocess.run(
                command,
                cwd=working_dir,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
            
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timeout ({timeout}s)",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
            }
