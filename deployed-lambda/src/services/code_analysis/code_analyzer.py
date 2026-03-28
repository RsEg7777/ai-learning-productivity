"""Code analysis service using Amazon Bedrock."""

import logging
import time
import uuid
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.models.code import (
    CodeAnalysis,
    CodeExplanation,
    LineAnalysis,
    CodeIssue,
    Improvement,
    ComplexityMetrics,
    ProgrammingLanguage,
    IssueSeverity,
)
from ...shared.utils.errors import ContentProcessingError, ProcessingTimeoutError

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Service for analyzing code with Amazon Bedrock."""

    # Processing time limit (in seconds) - Requirement 3.1
    CODE_ANALYSIS_TIMEOUT = 15

    # Maximum lines for detailed line-by-line analysis
    MAX_LINES_FOR_DETAILED_ANALYSIS = 100

    def __init__(self, bedrock_client: BedrockClient) -> None:
        """
        Initialize code analyzer.

        Args:
            bedrock_client: Bedrock client for LLM operations
        """
        self.bedrock_client = bedrock_client
        logger.info("Initialized CodeAnalyzer")

    def analyze_code(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> CodeAnalysis:
        """
        Analyze code and provide comprehensive analysis.

        This method provides:
        1. Line-by-line explanations (Requirement 3.1)
        2. Improvement suggestions and best practices (Requirement 3.2)
        3. Issue detection with corrective suggestions (Requirement 3.3)
        4. Documentation links and examples (Requirement 3.4)
        5. Complexity metrics

        All within 15 seconds as per Requirement 3.1.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            CodeAnalysis with complete analysis

        Raises:
            ContentProcessingError: If analysis fails
            ProcessingTimeoutError: If analysis exceeds 15 seconds
        """
        start_time = time.time()

        try:
            # Validate input
            if not code or not code.strip():
                raise ContentProcessingError(
                    message="Code cannot be empty",
                    content_type="code",
                )

            logger.info(f"Analyzing {language.value} code ({len(code)} characters)")

            # Count lines
            lines = code.split('\n')
            line_count = len(lines)

            # Generate overall explanation
            explanation = self._generate_explanation(code, language)

            # Check timeout after explanation
            elapsed = time.time() - start_time
            if elapsed > self.CODE_ANALYSIS_TIMEOUT:
                raise ProcessingTimeoutError(
                    content_type="code",
                    time_limit=self.CODE_ANALYSIS_TIMEOUT,
                    time_elapsed=int(elapsed),
                )

            # Generate line-by-line analysis (Requirement 3.1)
            line_by_line = self._generate_line_by_line_analysis(
                code, language, line_count
            )

            # Check timeout after line-by-line analysis
            elapsed = time.time() - start_time
            if elapsed > self.CODE_ANALYSIS_TIMEOUT:
                raise ProcessingTimeoutError(
                    content_type="code",
                    time_limit=self.CODE_ANALYSIS_TIMEOUT,
                    time_elapsed=int(elapsed),
                )

            # Detect issues and generate suggestions (Requirement 3.3)
            issues = self._detect_issues(code, language)

            # Generate improvements and best practices (Requirement 3.2)
            improvements = self._suggest_improvements(code, language)

            # Get documentation links (Requirement 3.4)
            doc_links = self._get_documentation_links(code, language)

            # Extract best practices
            best_practices = self._extract_best_practices(code, language)

            # Calculate complexity metrics
            complexity = self._calculate_complexity(code, language)

            # Final timeout check
            processing_time = time.time() - start_time
            if processing_time > self.CODE_ANALYSIS_TIMEOUT:
                raise ProcessingTimeoutError(
                    content_type="code",
                    time_limit=self.CODE_ANALYSIS_TIMEOUT,
                    time_elapsed=int(processing_time),
                )

            analysis = CodeAnalysis(
                explanation=explanation,
                line_by_line_analysis=line_by_line,
                improvements=improvements,
                issues=issues,
                complexity=complexity,
                documentation_links=doc_links,
                best_practices=best_practices,
            )

            logger.info(
                f"Successfully analyzed code in {processing_time:.2f}s "
                f"({line_count} lines, {len(issues)} issues, {len(improvements)} improvements)"
            )

            return analysis

        except ProcessingTimeoutError:
            raise
        except ContentProcessingError:
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error analyzing code: {e}")
            raise ContentProcessingError(
                message=f"Failed to analyze code: {str(e)}",
                content_type="code",
                details={"elapsed_time": elapsed_time},
            )

    def explain_code(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> CodeExplanation:
        """
        Generate detailed explanation of code.

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            CodeExplanation with detailed breakdown

        Raises:
            ContentProcessingError: If explanation fails
        """
        try:
            logger.info(f"Generating explanation for {language.value} code")

            # Generate summary
            summary = self._generate_summary(code, language)

            # Generate detailed explanation
            detailed = self._generate_detailed_explanation(code, language)

            # Generate line-by-line analysis
            lines = code.split('\n')
            line_by_line = self._generate_line_by_line_analysis(
                code, language, len(lines)
            )

            # Extract key concepts
            key_concepts = self._extract_key_concepts(code, language)

            # For complex algorithms, generate step-by-step breakdown
            algorithm_steps = None
            if self._is_complex_algorithm(code, language):
                algorithm_steps = self._generate_algorithm_steps(code, language)

            explanation = CodeExplanation(
                summary=summary,
                detailed_explanation=detailed,
                line_by_line=line_by_line,
                key_concepts=key_concepts,
                algorithm_steps=algorithm_steps,
            )

            logger.info("Successfully generated code explanation")
            return explanation

        except Exception as e:
            logger.error(f"Error explaining code: {e}")
            raise ContentProcessingError(
                message=f"Failed to explain code: {str(e)}",
                content_type="code",
            )

    def suggest_improvements(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[Improvement]:
        """
        Suggest improvements for code.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            List of Improvement suggestions

        Raises:
            ContentProcessingError: If suggestion generation fails
        """
        try:
            logger.info(f"Generating improvements for {language.value} code")
            return self._suggest_improvements(code, language)

        except Exception as e:
            logger.error(f"Error suggesting improvements: {e}")
            raise ContentProcessingError(
                message=f"Failed to suggest improvements: {str(e)}",
                content_type="code",
            )

    def detect_issues(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[CodeIssue]:
        """
        Detect issues in code.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            List of CodeIssue objects

        Raises:
            ContentProcessingError: If issue detection fails
        """
        try:
            logger.info(f"Detecting issues in {language.value} code")
            return self._detect_issues(code, language)

        except Exception as e:
            logger.error(f"Error detecting issues: {e}")
            raise ContentProcessingError(
                message=f"Failed to detect issues: {str(e)}",
                content_type="code",
            )

    def _generate_explanation(self, code: str, language: ProgrammingLanguage) -> str:
        """Generate overall code explanation."""
        prompt = f"""Provide a clear, concise explanation of what this {language.value} code does.
Focus on the overall purpose and functionality.

```{language.value}
{code}
```

Explanation:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=512,
            temperature=0.3,
        )

        return response.strip()

    def _generate_line_by_line_analysis(
        self,
        code: str,
        language: ProgrammingLanguage,
        line_count: int,
    ) -> List[LineAnalysis]:
        """
        Generate line-by-line analysis of code.

        For large files, analyzes key sections rather than every line.
        """
        lines = code.split('\n')

        # For very large files, analyze only key sections
        if line_count > self.MAX_LINES_FOR_DETAILED_ANALYSIS:
            logger.info(
                f"Code has {line_count} lines, analyzing key sections only"
            )
            return self._analyze_key_sections(code, language)

        # For smaller files, analyze line by line
        prompt = f"""Analyze this {language.value} code line by line.
For each non-empty, non-comment line, provide a brief explanation of what it does.

Format your response as JSON array:
[
  {{"line": 1, "code": "...", "explanation": "..."}},
  ...
]

```{language.value}
{code}
```

Analysis:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.2,
        )

        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return [
                    LineAnalysis(
                        line_number=item.get('line', 0),
                        code=item.get('code', ''),
                        explanation=item.get('explanation', ''),
                    )
                    for item in data
                ]
        except Exception as e:
            logger.warning(f"Failed to parse line-by-line JSON: {e}")

        # Fallback: parse text response
        return self._parse_line_analysis_text(response, lines)

    def _analyze_key_sections(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[LineAnalysis]:
        """Analyze key sections of large code files."""
        prompt = f"""This {language.value} code is large. Identify and explain the key sections:
- Function/method definitions
- Important logic blocks
- Complex operations

For each key section, provide line number and explanation.

```{language.value}
{code}
```

Key sections:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2,
        )

        # Parse response into LineAnalysis objects
        return self._parse_key_sections(response, code)

    def _parse_line_analysis_text(
        self,
        response: str,
        lines: List[str],
    ) -> List[LineAnalysis]:
        """Parse line analysis from text response."""
        analysis_list = []

        # Look for patterns like "Line 1: explanation" or "1. explanation"
        pattern = r'(?:Line\s+)?(\d+)[\s:.-]+(.+?)(?=(?:Line\s+)?\d+[\s:.-]|$)'
        matches = re.findall(pattern, response, re.DOTALL)

        for line_num_str, explanation in matches:
            try:
                line_num = int(line_num_str)
                if 1 <= line_num <= len(lines):
                    analysis_list.append(
                        LineAnalysis(
                            line_number=line_num,
                            code=lines[line_num - 1].strip(),
                            explanation=explanation.strip(),
                        )
                    )
            except (ValueError, IndexError):
                continue

        return analysis_list

    def _parse_key_sections(
        self,
        response: str,
        code: str,
    ) -> List[LineAnalysis]:
        """Parse key sections from response."""
        analysis_list = []
        lines = code.split('\n')

        # Look for line numbers and explanations
        pattern = r'(?:Line\s+)?(\d+)[\s:.-]+(.+?)(?=(?:Line\s+)?\d+[\s:.-]|$)'
        matches = re.findall(pattern, response, re.DOTALL)

        for line_num_str, explanation in matches:
            try:
                line_num = int(line_num_str)
                if 1 <= line_num <= len(lines):
                    analysis_list.append(
                        LineAnalysis(
                            line_number=line_num,
                            code=lines[line_num - 1].strip(),
                            explanation=explanation.strip(),
                        )
                    )
            except (ValueError, IndexError):
                continue

        return analysis_list

    def _detect_issues(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[CodeIssue]:
        """
        Detect issues and anti-patterns in code.
        
        Implements Requirement 3.3: Detect errors and anti-patterns with corrective suggestions.
        Implements Requirement 3.4: Include relevant documentation links and examples.
        """
        prompt = f"""Analyze this {language.value} code for issues, errors, and anti-patterns.
Identify:
1. Potential bugs or errors
2. Security vulnerabilities
3. Performance issues
4. Code smells and anti-patterns
5. Style violations
6. Error handling issues
7. Resource management problems

For each issue, provide:
- Severity (critical/error/warning/info)
- Line number (if applicable)
- Clear description of the problem
- Detailed corrective suggestion with explanation of WHY the fix is needed
- Code example showing the fix (if applicable)
- Category (security/performance/error-handling/style/maintainability/etc)

Format as JSON array:
[
  {{
    "severity": "error",
    "line": 10,
    "message": "Clear description of the issue",
    "suggestion": "Detailed corrective suggestion with explanation. Example: Replace 'eval(user_input)' with 'ast.literal_eval(user_input)' to safely evaluate user input. The eval() function can execute arbitrary code, creating a security vulnerability. ast.literal_eval() only evaluates literals and is safe for untrusted input.",
    "category": "security",
    "example": "# Before:\\nresult = eval(user_input)\\n\\n# After:\\nimport ast\\nresult = ast.literal_eval(user_input)"
  }},
  ...
]

```{language.value}
{code}
```

Issues:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.2,
        )

        # Parse JSON response
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                issues = []
                for item in data:
                    # Build comprehensive suggestion with explanation and example
                    suggestion = item.get('suggestion', '')
                    example = item.get('example', '')
                    
                    # Combine suggestion with example if both exist
                    if suggestion and example:
                        full_suggestion = f"{suggestion}\n\nExample:\n{example}"
                    elif suggestion:
                        full_suggestion = suggestion
                    elif example:
                        full_suggestion = f"Example:\n{example}"
                    else:
                        full_suggestion = None
                    
                    # Get documentation link for this specific issue
                    doc_link = self._get_issue_documentation_link(
                        item.get('category', 'general'),
                        language
                    )
                    
                    # Append doc link to suggestion if available
                    if full_suggestion and doc_link:
                        full_suggestion += f"\n\nRelevant documentation: {doc_link}"
                    
                    issues.append(
                        CodeIssue(
                            severity=IssueSeverity(item.get('severity', 'info')),
                            line_number=item.get('line'),
                            message=item.get('message', ''),
                            suggestion=full_suggestion,
                            category=item.get('category', 'general'),
                        )
                    )
                return issues
        except Exception as e:
            logger.warning(f"Failed to parse issues JSON: {e}")

        # Fallback: parse text response
        return self._parse_issues_text(response)

    def _parse_issues_text(self, response: str) -> List[CodeIssue]:
        """Parse issues from text response with enhanced suggestion extraction."""
        issues = []

        # Split by issue markers
        issue_blocks = re.split(r'\n\s*(?=\d+\.|\-)', response)

        for block in issue_blocks:
            if not block.strip():
                continue

            try:
                # Extract severity
                severity = IssueSeverity.WARNING
                if any(word in block.lower() for word in ['critical', 'severe']):
                    severity = IssueSeverity.CRITICAL
                elif any(word in block.lower() for word in ['error', 'bug']):
                    severity = IssueSeverity.ERROR
                elif 'info' in block.lower():
                    severity = IssueSeverity.INFO

                # Extract line number
                line_match = re.search(r'line\s+(\d+)', block, re.IGNORECASE)
                line_number = int(line_match.group(1)) if line_match else None

                # Extract message (first sentence or line)
                message_match = re.search(r'[:\-]\s*(.+?)(?:\.|$)', block)
                message = message_match.group(1).strip() if message_match else block[:100]

                # Extract suggestion (look for keywords like "fix", "suggestion", "instead", "use")
                suggestion = None
                suggestion_patterns = [
                    r'(?:suggestion|fix|instead|use|replace|change):\s*(.+?)(?:\n\n|\Z)',
                    r'(?:should|recommend|consider)\s+(.+?)(?:\n\n|\Z)',
                ]
                for pattern in suggestion_patterns:
                    suggestion_match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
                    if suggestion_match:
                        suggestion = suggestion_match.group(1).strip()
                        break

                # Determine category
                category = 'general'
                if 'security' in block.lower():
                    category = 'security'
                elif 'performance' in block.lower():
                    category = 'performance'
                elif 'style' in block.lower():
                    category = 'style'
                elif any(word in block.lower() for word in ['error', 'exception', 'handling']):
                    category = 'error-handling'
                elif 'maintain' in block.lower():
                    category = 'maintainability'

                issues.append(
                    CodeIssue(
                        severity=severity,
                        line_number=line_number,
                        message=message,
                        suggestion=suggestion,
                        category=category,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse issue block: {e}")
                continue

        return issues

    def _suggest_improvements(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[Improvement]:
        """
        Generate improvement suggestions and best practices.
        
        Implements Requirement 3.2: Identify potential improvements and suggest best practices.
        Implements Requirement 3.4: Include relevant documentation links and examples.
        """
        prompt = f"""Analyze this {language.value} code and suggest improvements following best practices.
Focus on:
1. Code readability and maintainability
2. Performance optimizations
3. Design patterns and architecture
4. Error handling
5. Testing and documentation
6. Modern language features and idioms

For each improvement, provide:
- Title (brief, descriptive)
- Description (detailed explanation of WHY this improvement matters)
- Code before (current implementation if applicable)
- Code after (improved version with clear example)
- Benefit (specific benefits this improvement provides)
- Priority (high/medium/low)

Format as JSON array:
[
  {{
    "title": "Use list comprehension for better performance",
    "description": "List comprehensions are more Pythonic and typically faster than traditional for loops with append operations. They are optimized at the C level and create the list in a single pass.",
    "code_before": "result = []\\nfor item in data:\\n    result.append(item * 2)",
    "code_after": "result = [item * 2 for item in data]",
    "benefit": "Improves performance by 20-30% and makes code more readable and Pythonic",
    "priority": "medium"
  }},
  ...
]

```{language.value}
{code}
```

Improvements:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.3,
        )

        # Parse JSON response
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                improvements = []
                for item in data:
                    # Get documentation link for the improvement category
                    title = item.get('title', '')
                    category = self._categorize_improvement(title)
                    doc_link = self._get_issue_documentation_link(category, language)
                    
                    # Enhance benefit with documentation link
                    benefit = item.get('benefit', '')
                    if doc_link:
                        benefit += f"\n\nLearn more: {doc_link}"
                    
                    improvements.append(
                        Improvement(
                            title=item.get('title', ''),
                            description=item.get('description', ''),
                            code_before=item.get('code_before'),
                            code_after=item.get('code_after'),
                            benefit=benefit,
                            priority=item.get('priority', 'medium'),
                        )
                    )
                return improvements
        except Exception as e:
            logger.warning(f"Failed to parse improvements JSON: {e}")

        # Fallback: parse text response
        return self._parse_improvements_text(response)

    def _parse_improvements_text(self, response: str) -> List[Improvement]:
        """Parse improvements from text response."""
        improvements = []

        # Split by improvement markers
        improvement_blocks = re.split(r'\n\s*(?=\d+\.)', response)

        for block in improvement_blocks:
            if not block.strip() or len(block) < 20:
                continue

            try:
                # Extract title (first line or sentence)
                title_match = re.search(r'^[\d\.\-\s]*(.+?)(?:\n|:)', block)
                title = title_match.group(1).strip() if title_match else "Improvement"

                # Use block as description
                description = block.strip()

                # Determine priority
                priority = 'medium'
                if any(word in block.lower() for word in ['critical', 'important', 'must']):
                    priority = 'high'
                elif any(word in block.lower() for word in ['minor', 'optional', 'consider']):
                    priority = 'low'

                improvements.append(
                    Improvement(
                        title=title[:100],
                        description=description[:500],
                        code_before=None,
                        code_after=None,
                        benefit="Improves code quality",
                        priority=priority,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse improvement block: {e}")
                continue

        return improvements[:5]  # Limit to top 5

    def _get_documentation_links(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[str]:
        """Get relevant documentation links."""
        # Extract key libraries/frameworks from code
        libraries = self._extract_libraries(code, language)

        # Generate documentation links based on language and libraries
        doc_links = []

        # Language-specific documentation
        lang_docs = {
            ProgrammingLanguage.PYTHON: "https://docs.python.org/3/",
            ProgrammingLanguage.JAVASCRIPT: "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
            ProgrammingLanguage.TYPESCRIPT: "https://www.typescriptlang.org/docs/",
            ProgrammingLanguage.JAVA: "https://docs.oracle.com/en/java/",
            ProgrammingLanguage.CPP: "https://en.cppreference.com/",
            ProgrammingLanguage.CSHARP: "https://docs.microsoft.com/en-us/dotnet/csharp/",
            ProgrammingLanguage.GO: "https://golang.org/doc/",
            ProgrammingLanguage.RUST: "https://doc.rust-lang.org/",
        }

        if language in lang_docs:
            doc_links.append(lang_docs[language])

        # Add library-specific links (simplified)
        for lib in libraries[:3]:  # Top 3 libraries
            doc_links.append(f"https://www.google.com/search?q={lib}+{language.value}+documentation")

        return doc_links

    def _get_issue_documentation_link(
        self,
        category: str,
        language: ProgrammingLanguage,
    ) -> Optional[str]:
        """
        Get relevant documentation link for a specific issue category.
        
        Implements Requirement 3.4: Include relevant documentation links.
        """
        # Category-specific documentation links by language
        category_docs = {
            ProgrammingLanguage.PYTHON: {
                'security': 'https://docs.python.org/3/library/security_warnings.html',
                'performance': 'https://docs.python.org/3/library/profile.html',
                'error-handling': 'https://docs.python.org/3/tutorial/errors.html',
                'style': 'https://peps.python.org/pep-0008/',
                'maintainability': 'https://docs.python.org/3/tutorial/modules.html',
                'testing': 'https://docs.python.org/3/library/unittest.html',
                'concurrency': 'https://docs.python.org/3/library/asyncio.html',
                'type-safety': 'https://docs.python.org/3/library/typing.html',
            },
            ProgrammingLanguage.JAVASCRIPT: {
                'security': 'https://developer.mozilla.org/en-US/docs/Web/Security',
                'performance': 'https://developer.mozilla.org/en-US/docs/Web/Performance',
                'error-handling': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Control_flow_and_error_handling',
                'style': 'https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Writing_style_guide/Code_style_guide/JavaScript',
                'async': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function',
                'promises': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise',
            },
            ProgrammingLanguage.TYPESCRIPT: {
                'type-safety': 'https://www.typescriptlang.org/docs/handbook/2/everyday-types.html',
                'error-handling': 'https://www.typescriptlang.org/docs/handbook/2/narrowing.html',
                'style': 'https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html',
                'generics': 'https://www.typescriptlang.org/docs/handbook/2/generics.html',
            },
            ProgrammingLanguage.JAVA: {
                'security': 'https://docs.oracle.com/en/java/javase/17/security/',
                'performance': 'https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/doc-files/threadPrimitiveDeprecation.html',
                'error-handling': 'https://docs.oracle.com/javase/tutorial/essential/exceptions/',
                'style': 'https://www.oracle.com/java/technologies/javase/codeconventions-contents.html',
                'concurrency': 'https://docs.oracle.com/javase/tutorial/essential/concurrency/',
            },
            ProgrammingLanguage.CPP: {
                'security': 'https://en.cppreference.com/w/cpp/language/memory_model',
                'performance': 'https://en.cppreference.com/w/cpp/language/optimization',
                'error-handling': 'https://en.cppreference.com/w/cpp/error',
                'memory': 'https://en.cppreference.com/w/cpp/memory',
                'smart-pointers': 'https://en.cppreference.com/w/cpp/memory/unique_ptr',
            },
            ProgrammingLanguage.GO: {
                'error-handling': 'https://go.dev/blog/error-handling-and-go',
                'concurrency': 'https://go.dev/tour/concurrency/1',
                'style': 'https://go.dev/doc/effective_go',
                'performance': 'https://go.dev/doc/diagnostics',
            },
            ProgrammingLanguage.RUST: {
                'error-handling': 'https://doc.rust-lang.org/book/ch09-00-error-handling.html',
                'memory': 'https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html',
                'concurrency': 'https://doc.rust-lang.org/book/ch16-00-concurrency.html',
                'safety': 'https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html',
            },
        }
        
        # Get language-specific category docs
        if language in category_docs:
            lang_category_docs = category_docs[language]
            if category in lang_category_docs:
                return lang_category_docs[category]
        
        # Fallback to general language documentation
        general_docs = {
            ProgrammingLanguage.PYTHON: 'https://docs.python.org/3/',
            ProgrammingLanguage.JAVASCRIPT: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
            ProgrammingLanguage.TYPESCRIPT: 'https://www.typescriptlang.org/docs/',
            ProgrammingLanguage.JAVA: 'https://docs.oracle.com/en/java/',
            ProgrammingLanguage.CPP: 'https://en.cppreference.com/',
            ProgrammingLanguage.CSHARP: 'https://docs.microsoft.com/en-us/dotnet/csharp/',
            ProgrammingLanguage.GO: 'https://golang.org/doc/',
            ProgrammingLanguage.RUST: 'https://doc.rust-lang.org/',
        }
        
        return general_docs.get(language)

    def _categorize_improvement(self, title: str) -> str:
        """
        Categorize an improvement based on its title.
        
        Returns a category string that can be used to find relevant documentation.
        """
        title_lower = title.lower()
        
        # Map keywords to categories
        if any(word in title_lower for word in ['type', 'typing', 'annotation', 'hint']):
            return 'type-safety'
        elif any(word in title_lower for word in ['error', 'exception', 'handling', 'try', 'catch']):
            return 'error-handling'
        elif any(word in title_lower for word in ['performance', 'optimize', 'speed', 'efficient']):
            return 'performance'
        elif any(word in title_lower for word in ['security', 'safe', 'vulnerability', 'injection']):
            return 'security'
        elif any(word in title_lower for word in ['async', 'await', 'promise', 'concurrent']):
            return 'concurrency'
        elif any(word in title_lower for word in ['test', 'testing', 'unit test']):
            return 'testing'
        elif any(word in title_lower for word in ['style', 'format', 'convention', 'naming']):
            return 'style'
        elif any(word in title_lower for word in ['memory', 'pointer', 'leak', 'allocation']):
            return 'memory'
        else:
            return 'maintainability'

    def _extract_libraries(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[str]:
        """Extract libraries/frameworks used in code."""
        libraries = []

        if language == ProgrammingLanguage.PYTHON:
            # Look for import statements
            import_pattern = r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            matches = re.findall(import_pattern, code)
            libraries.extend(matches)

        elif language in [ProgrammingLanguage.JAVASCRIPT, ProgrammingLanguage.TYPESCRIPT]:
            # Look for require/import statements
            import_pattern = r'(?:require|import)\s*\(?[\'"]([a-zA-Z_][a-zA-Z0-9_\-]*)[\'"]'
            matches = re.findall(import_pattern, code)
            libraries.extend(matches)

        elif language == ProgrammingLanguage.JAVA:
            # Look for import statements
            import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
            matches = re.findall(import_pattern, code)
            # Extract package names
            libraries.extend([m.split('.')[0] for m in matches])

        # Remove duplicates and common standard libraries
        common_libs = {'sys', 'os', 'time', 'math', 'json', 'std', 'util'}
        libraries = list(set(lib for lib in libraries if lib not in common_libs))

        return libraries[:5]

    def _extract_best_practices(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[str]:
        """Extract best practices recommendations."""
        prompt = f"""List 3-5 best practices that apply to this {language.value} code.
Focus on industry-standard practices and conventions.

```{language.value}
{code}
```

Best practices:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=512,
            temperature=0.3,
        )

        # Parse best practices from response
        practices = []
        lines = response.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering and bullet points
            cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line)
            if cleaned and len(cleaned) > 10:
                practices.append(cleaned)

        return practices[:5]

    def _calculate_complexity(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> ComplexityMetrics:
        """Calculate code complexity metrics."""
        lines = code.split('\n')
        total_lines = len(lines)

        # Count non-empty, non-comment lines
        code_lines = 0
        comment_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Simple comment detection
            if language == ProgrammingLanguage.PYTHON:
                if stripped.startswith('#'):
                    comment_lines += 1
                else:
                    code_lines += 1
            elif language in [ProgrammingLanguage.JAVASCRIPT, ProgrammingLanguage.TYPESCRIPT,
                             ProgrammingLanguage.JAVA, ProgrammingLanguage.CPP,
                             ProgrammingLanguage.CSHARP, ProgrammingLanguage.GO,
                             ProgrammingLanguage.RUST]:
                if stripped.startswith('//') or stripped.startswith('/*'):
                    comment_lines += 1
                else:
                    code_lines += 1
            else:
                code_lines += 1

        # Calculate comment ratio
        comment_ratio = comment_lines / total_lines if total_lines > 0 else 0.0

        # Estimate cyclomatic complexity (simplified)
        # Count decision points: if, for, while, case, catch, etc.
        decision_keywords = ['if', 'for', 'while', 'case', 'catch', '&&', '||', '?']
        cyclomatic = 1  # Base complexity

        for keyword in decision_keywords:
            # Use word boundaries for keywords
            if keyword in ['&&', '||', '?']:
                cyclomatic += code.count(keyword)
            else:
                pattern = r'\b' + keyword + r'\b'
                cyclomatic += len(re.findall(pattern, code, re.IGNORECASE))

        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=None,  # Would require more sophisticated analysis
            lines_of_code=code_lines,
            comment_ratio=comment_ratio,
        )

    def _generate_summary(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> str:
        """Generate high-level summary of code."""
        prompt = f"""Provide a brief, high-level summary (2-3 sentences) of what this {language.value} code does.

```{language.value}
{code}
```

Summary:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=256,
            temperature=0.3,
        )

        return response.strip()

    def _generate_detailed_explanation(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> str:
        """Generate detailed explanation of code."""
        prompt = f"""Provide a detailed explanation of this {language.value} code.
Explain:
1. What the code does
2. How it works
3. Key components and their roles
4. Important design decisions

```{language.value}
{code}
```

Detailed explanation:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3,
        )

        return response.strip()

    def _extract_key_concepts(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[str]:
        """Extract key programming concepts used in code."""
        prompt = f"""List the key programming concepts, patterns, and techniques used in this {language.value} code.

```{language.value}
{code}
```

Key concepts:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=512,
            temperature=0.3,
        )

        # Parse concepts from response
        concepts = []
        lines = response.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering and bullet points
            cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line)
            if cleaned and len(cleaned) > 5:
                concepts.append(cleaned)

        return concepts[:10]

    def _is_complex_algorithm(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> bool:
        """Determine if code contains a complex algorithm."""
        # Simple heuristics for complexity
        lines = code.split('\n')

        # Check for nested loops
        loop_keywords = ['for', 'while']
        loop_count = sum(
            1 for line in lines
            if any(keyword in line.lower() for keyword in loop_keywords)
        )

        # Check for recursion (function calling itself)
        has_recursion = False
        func_names = re.findall(r'def\s+(\w+)', code)
        for func_name in func_names:
            # Look for the function name being called within its own definition
            func_def_match = re.search(rf'def\s+{func_name}\s*\([^)]*\):(.*?)(?=\ndef\s|\Z)', code, re.DOTALL)
            if func_def_match:
                func_body = func_def_match.group(1)
                # Check if function name appears in its own body (recursion)
                if re.search(rf'\b{func_name}\s*\(', func_body):
                    has_recursion = True
                    break

        # Check for sorting/searching keywords
        algorithm_keywords = ['sort', 'search', 'binary', 'tree', 'graph', 'dynamic']
        has_algorithm_keywords = any(
            keyword in code.lower() for keyword in algorithm_keywords
        )

        return loop_count >= 2 or has_recursion or has_algorithm_keywords

    def _generate_algorithm_steps(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[str]:
        """Generate step-by-step algorithm breakdown for complex code."""
        prompt = f"""Break down this {language.value} algorithm into clear, step-by-step explanations.
Number each step and explain what happens at each stage.

```{language.value}
{code}
```

Algorithm steps:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3,
        )

        # Parse steps from response
        steps = []
        lines = response.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove step numbering
            cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line)
            if cleaned and len(cleaned) > 10:
                steps.append(cleaned)

        return steps

    def explain_complex_algorithm(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> Dict[str, Any]:
        """
        Provide comprehensive explanation of complex algorithms.
        
        Implements Requirement 3.5: Break down complex algorithms into step-by-step explanations.
        
        This method provides:
        1. Step-by-step algorithm breakdown
        2. Visual representation of algorithm flow (Mermaid diagram)
        3. Time and space complexity analysis
        4. Optimization suggestions
        
        Args:
            code: Algorithm code to explain
            language: Programming language
            
        Returns:
            Dictionary containing:
                - algorithm_steps: List of step-by-step explanations
                - flow_diagram: Mermaid diagram representing algorithm flow
                - complexity_analysis: Time and space complexity analysis
                - optimization_suggestions: List of optimization recommendations
                
        Raises:
            ContentProcessingError: If explanation fails
        """
        try:
            logger.info(f"Generating complex algorithm explanation for {language.value} code")
            
            # Generate step-by-step breakdown
            algorithm_steps = self._generate_detailed_algorithm_steps(code, language)
            
            # Generate visual flow diagram
            flow_diagram = self._generate_algorithm_flow_diagram(code, language)
            
            # Analyze complexity
            complexity_analysis = self._analyze_algorithm_complexity(code, language)
            
            # Generate optimization suggestions
            optimization_suggestions = self._generate_optimization_suggestions(
                code, language, complexity_analysis
            )
            
            result = {
                'algorithm_steps': algorithm_steps,
                'flow_diagram': flow_diagram,
                'complexity_analysis': complexity_analysis,
                'optimization_suggestions': optimization_suggestions,
            }
            
            logger.info("Successfully generated complex algorithm explanation")
            return result
            
        except Exception as e:
            logger.error(f"Error explaining complex algorithm: {e}")
            raise ContentProcessingError(
                message=f"Failed to explain complex algorithm: {str(e)}",
                content_type="code",
            )

    def _generate_detailed_algorithm_steps(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> List[Dict[str, str]]:
        """
        Generate detailed step-by-step algorithm breakdown.
        
        Returns a list of steps with title, description, and code snippet.
        """
        prompt = f"""Analyze this {language.value} algorithm and break it down into detailed steps.

For each step, provide:
1. A brief title
2. A detailed description of what happens
3. The relevant code snippet (if applicable)

Format as JSON array:
[
  {{
    "step_number": 1,
    "title": "Initialize variables",
    "description": "Set up initial variables and data structures needed for the algorithm",
    "code_snippet": "n = len(arr)\\nresult = []"
  }},
  ...
]

```{language.value}
{code}
```

Algorithm steps:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.3,
        )

        # Parse JSON response
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data
        except Exception as e:
            logger.warning(f"Failed to parse algorithm steps JSON: {e}")

        # Fallback: parse text response
        return self._parse_algorithm_steps_text(response)

    def _parse_algorithm_steps_text(self, response: str) -> List[Dict[str, str]]:
        """Parse algorithm steps from text response."""
        steps = []
        step_blocks = re.split(r'\n\s*(?=\d+\.)', response)
        
        for i, block in enumerate(step_blocks, 1):
            if not block.strip():
                continue
                
            # Extract title (first line)
            lines = block.strip().split('\n')
            title = re.sub(r'^[\d\.\-\*\s]+', '', lines[0]).strip()
            
            # Rest is description
            description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else title
            
            steps.append({
                'step_number': i,
                'title': title[:100],
                'description': description[:500],
                'code_snippet': None,
            })
        
        return steps

    def _generate_algorithm_flow_diagram(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> str:
        """
        Generate a Mermaid flowchart diagram representing the algorithm flow.
        
        Returns a Mermaid diagram string that can be rendered visually.
        """
        prompt = f"""Create a Mermaid flowchart diagram that represents the flow of this {language.value} algorithm.

Use Mermaid syntax with these node types:
- Start/End: Use stadium shape (([text]))
- Process: Use rectangle ([text])
- Decision: Use diamond {{text}}
- Input/Output: Use parallelogram [/text/]

Example format:
```mermaid
graph TD
    A([Start]) --> B[Initialize variables]
    B --> C{{Check condition}}
    C -->|Yes| D[Process data]
    C -->|No| E([End])
    D --> C
```

Analyze this code and create a clear, logical flowchart:

```{language.value}
{code}
```

Mermaid diagram:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3,
        )

        # Extract Mermaid diagram from response
        mermaid_match = re.search(r'```mermaid\s*(.*?)\s*```', response, re.DOTALL)
        if mermaid_match:
            return mermaid_match.group(1).strip()
        
        # If no code block, try to extract graph definition
        graph_match = re.search(r'(graph\s+(?:TD|LR|TB).*?)(?:\n\n|\Z)', response, re.DOTALL)
        if graph_match:
            return graph_match.group(1).strip()
        
        # Fallback: return a simple diagram
        return self._generate_simple_flow_diagram(code, language)

    def _generate_simple_flow_diagram(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> str:
        """Generate a simple fallback flow diagram."""
        lines = code.split('\n')
        has_loop = any(keyword in code.lower() for keyword in ['for', 'while'])
        has_condition = any(keyword in code.lower() for keyword in ['if', 'elif', 'else'])
        
        diagram = "graph TD\n"
        diagram += "    A([Start]) --> B[Initialize]\n"
        
        if has_condition:
            diagram += "    B --> C{{Check condition}}\n"
            diagram += "    C -->|True| D[Process]\n"
            diagram += "    C -->|False| E[Alternative]\n"
            if has_loop:
                diagram += "    D --> C\n"
                diagram += "    E --> F([End])\n"
            else:
                diagram += "    D --> F([End])\n"
                diagram += "    E --> F\n"
        elif has_loop:
            diagram += "    B --> C{{Loop condition}}\n"
            diagram += "    C -->|Continue| D[Process iteration]\n"
            diagram += "    D --> C\n"
            diagram += "    C -->|Done| E([End])\n"
        else:
            diagram += "    B --> C[Process]\n"
            diagram += "    C --> D([End])\n"
        
        return diagram

    def _analyze_algorithm_complexity(
        self,
        code: str,
        language: ProgrammingLanguage,
    ) -> Dict[str, Any]:
        """
        Analyze time and space complexity of the algorithm.
        
        Returns complexity analysis with Big O notation and explanation.
        """
        prompt = f"""Analyze the time and space complexity of this {language.value} algorithm.

Provide:
1. Time complexity in Big O notation
2. Detailed explanation of why this is the time complexity
3. Space complexity in Big O notation
4. Detailed explanation of space usage
5. Best case, average case, and worst case scenarios (if applicable)

Format as JSON:
{{
  "time_complexity": "O(n log n)",
  "time_explanation": "The algorithm uses a divide-and-conquer approach...",
  "space_complexity": "O(n)",
  "space_explanation": "Additional space is needed for...",
  "best_case": "O(n)",
  "average_case": "O(n log n)",
  "worst_case": "O(n^2)",
  "complexity_factors": ["Input size", "Data distribution", "..."]
}}

```{language.value}
{code}
```

Complexity analysis:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2,
        )

        # Parse JSON response
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data
        except Exception as e:
            logger.warning(f"Failed to parse complexity analysis JSON: {e}")

        # Fallback: parse text response
        return self._parse_complexity_text(response)

    def _parse_complexity_text(self, response: str) -> Dict[str, Any]:
        """Parse complexity analysis from text response."""
        # Extract time complexity
        time_match = re.search(r'time\s+complexity[:\s]+O\(([^)]+)\)', response, re.IGNORECASE)
        time_complexity = f"O({time_match.group(1)})" if time_match else "O(n)"
        
        # Extract space complexity
        space_match = re.search(r'space\s+complexity[:\s]+O\(([^)]+)\)', response, re.IGNORECASE)
        space_complexity = f"O({space_match.group(1)})" if space_match else "O(1)"
        
        return {
            'time_complexity': time_complexity,
            'time_explanation': 'Analysis based on algorithm structure',
            'space_complexity': space_complexity,
            'space_explanation': 'Analysis based on memory usage',
            'best_case': time_complexity,
            'average_case': time_complexity,
            'worst_case': time_complexity,
            'complexity_factors': ['Input size', 'Algorithm structure'],
        }

    def _generate_optimization_suggestions(
        self,
        code: str,
        language: ProgrammingLanguage,
        complexity_analysis: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Generate optimization suggestions based on complexity analysis.
        
        Returns a list of optimization recommendations with explanations.
        """
        current_complexity = complexity_analysis.get('time_complexity', 'Unknown')
        
        prompt = f"""Given this {language.value} algorithm with time complexity {current_complexity}, 
suggest specific optimizations to improve performance.

For each optimization, provide:
1. Title: Brief description of the optimization
2. Description: Detailed explanation of the optimization technique
3. Expected improvement: What complexity or performance gain to expect
4. Implementation approach: How to implement this optimization
5. Trade-offs: Any downsides or considerations

Format as JSON array:
[
  {{
    "title": "Use hash table for lookups",
    "description": "Replace linear search with hash table to reduce lookup time",
    "expected_improvement": "Reduce time complexity from O(n^2) to O(n)",
    "implementation": "Create a dictionary/map to store values for O(1) lookup",
    "tradeoffs": "Increases space complexity by O(n)"
  }},
  ...
]

```{language.value}
{code}
```

Current complexity: {current_complexity}

Optimization suggestions:"""

        response = self.bedrock_client.invoke_claude(
            prompt=prompt,
            max_tokens=1536,
            temperature=0.3,
        )

        # Parse JSON response
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data
        except Exception as e:
            logger.warning(f"Failed to parse optimization suggestions JSON: {e}")

        # Fallback: parse text response
        return self._parse_optimization_text(response)

    def _parse_optimization_text(self, response: str) -> List[Dict[str, str]]:
        """Parse optimization suggestions from text response."""
        suggestions = []
        suggestion_blocks = re.split(r'\n\s*(?=\d+\.)', response)
        
        for block in suggestion_blocks:
            if not block.strip() or len(block) < 20:
                continue
                
            # Extract title (first line)
            lines = block.strip().split('\n')
            title = re.sub(r'^[\d\.\-\*\s]+', '', lines[0]).strip()
            
            # Rest is description
            description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else title
            
            suggestions.append({
                'title': title[:100],
                'description': description[:500],
                'expected_improvement': 'Improved performance',
                'implementation': 'See description for details',
                'tradeoffs': 'Consider memory and complexity trade-offs',
            })
        
        return suggestions[:5]  # Limit to top 5
