# -*- coding: utf-8 -*-
"""
WADE Skill Updater
Modifies agent logic and core functions based on feedback.
"""

import os
import time
import re
from typing import Dict, List, Any, Optional


class SkillUpdater:
    """
    Skill Updater for WADE.
    Analyzes and modifies code to improve system performance.
    """

    def __init__(self, elite_few):
        """
        Initialize the skill updater.

        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.modification_history = []

    def analyze_module(
        self,
        module_path: str,
        trigger_reason: str,
        recent_feedback: List[Dict[str, Any]],
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a module for potential improvements.

        Args:
            module_path: Path to the module to analyze
            trigger_reason: Reason for analysis
            recent_feedback: Recent feedback events
            additional_context: Additional context for analysis

        Returns:
            Dictionary with analysis results
        """
        self.elite_few.log_and_respond(
            f"Analyzing module: {module_path}", level="INFO", component="SKILL_UPDATER"
        )

        # Check if module exists
        full_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), module_path
        )
        if not os.path.exists(full_path):
            return {
                "improvements_needed": False,
                "error": f"Module not found: {module_path}",
            }

        # Read module content
        try:
            with open(full_path, "r") as f:
                content = f.read()
        except Exception as e:
            return {
                "improvements_needed": False,
                "error": f"Error reading module: {str(e)}",
            }

        # Analyze module content
        improvements = []

        # Check for common issues
        issues = self._identify_issues(content, module_path, recent_feedback)

        # Generate improvements for each issue
        for issue in issues:
            improvement = self._generate_improvement(issue, content, module_path)
            if improvement:
                improvements.append(improvement)

        return {
            "improvements_needed": len(improvements) > 0,
            "improvements": improvements,
            "issues_found": issues,
            "module_path": module_path,
            "trigger_reason": trigger_reason,
        }

    def _identify_issues(
        self, content: str, module_path: str, recent_feedback: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify issues in module content.

        Args:
            content: Module content
            module_path: Path to the module
            recent_feedback: Recent feedback events

        Returns:
            List of identified issues
        """
        issues = []

        # Check for error handling issues
        if "except:" in content and "except Exception as e:" not in content:
            issues.append(
                {
                    "type": "error_handling",
                    "description": "Bare except clause found",
                    "severity": "medium",
                    "line_number": self._find_line_number(content, "except:"),
                }
            )

        # Check for hardcoded values
        hardcoded_pattern = r"(\d+\.\d+|\d+)"
        hardcoded_matches = re.findall(hardcoded_pattern, content)
        if len(hardcoded_matches) > 10:  # Arbitrary threshold
            issues.append(
                {
                    "type": "hardcoded_values",
                    "description": "Multiple hardcoded values found",
                    "severity": "low",
                    "count": len(hardcoded_matches),
                }
            )

        # Check for long functions
        functions = re.findall(r"def\s+(\w+)\s*\(", content)
        for func in functions:
            func_pattern = r"def\s+" + func + r"\s*\([^)]*\):[^\n]*\n((?:\s+[^\n]*\n)+)"
            func_match = re.search(func_pattern, content)
            if func_match:
                func_body = func_match.group(1)
                lines = func_body.count("\n")
                if lines > 50:  # Arbitrary threshold
                    issues.append(
                        {
                            "type": "long_function",
                            "description": f"Long function found: {func}",
                            "severity": "medium",
                            "function": func,
                            "lines": lines,
                        }
                    )

        # Check for issues related to recent failures
        for feedback in recent_feedback:
            if feedback.get("type") == "failure":
                message = feedback.get("message", "")
                if module_path in message:
                    issues.append(
                        {
                            "type": "feedback_failure",
                            "description": f"Recent failure related to this module: {message}",
                            "severity": "high",
                            "feedback": feedback,
                        }
                    )

        return issues

    def _generate_improvement(
        self, issue: Dict[str, Any], content: str, module_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an improvement for an issue.

        Args:
            issue: Issue to generate improvement for
            content: Module content
            module_path: Path to the module

        Returns:
            Dictionary with improvement details or None if no improvement is possible
        """
        if issue["type"] == "error_handling":
            # Find the line with the bare except
            lines = content.split("\n")
            line_number = issue.get("line_number", 0)

            if line_number > 0 and line_number < len(lines):
                line = lines[line_number]
                indentation = len(line) - len(line.lstrip())
                improved_line = line.replace("except:", "except Exception as e:")

                # Add logging in the except block
                next_line = (
                    lines[line_number + 1] if line_number + 1 < len(lines) else ""
                )
                if "log" not in next_line.lower() and "print" not in next_line.lower():
                    log_line = (
                        " " * indentation
                        + '    self.elite_few.log_and_respond(f"Error: {str(e)}", level="ERROR")'
                    )

                    return {
                        "type": "code_modification",
                        "description": "Improve error handling",
                        "original_code": line,
                        "improved_code": improved_line + "\n" + log_line,
                        "line_number": line_number,
                        "severity": issue["severity"],
                    }

        elif issue["type"] == "long_function":
            # Suggest refactoring long function
            return {
                "type": "refactoring_suggestion",
                "description": f'Refactor long function: {issue["function"]}',
                "function": issue["function"],
                "lines": issue["lines"],
                "suggestion": f'Consider breaking down function {issue["function"]} into smaller, more focused functions',
                "severity": issue["severity"],
            }

        elif issue["type"] == "feedback_failure":
            # Suggest improvements based on feedback
            return {
                "type": "feedback_improvement",
                "description": f'Address feedback failure: {issue["description"]}',
                "feedback": issue["feedback"],
                "suggestion": "Review the module for issues related to this failure and implement appropriate error handling or validation",
                "severity": issue["severity"],
            }

        return None

    def _find_line_number(self, content: str, pattern: str) -> int:
        """
        Find the line number of a pattern in content.

        Args:
            content: Content to search in
            pattern: Pattern to search for

        Returns:
            Line number (0-based) or -1 if not found
        """
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if pattern in line:
                return i
        return -1

    def apply_improvements(
        self, module_path: str, improvements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply improvements to a module.

        Args:
            module_path: Path to the module
            improvements: List of improvements to apply

        Returns:
            Dictionary with application results
        """
        self.elite_few.log_and_respond(
            f"Applying improvements to module: {module_path}",
            level="INFO",
            component="SKILL_UPDATER",
        )

        # Check if module exists
        full_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), module_path
        )
        if not os.path.exists(full_path):
            return {"success": False, "error": f"Module not found: {module_path}"}

        # Read module content
        try:
            with open(full_path, "r") as f:
                content = f.read()
        except Exception as e:
            return {"success": False, "error": f"Error reading module: {str(e)}"}

        # Apply code modifications
        modified_content = content
        applied_improvements = []

        for improvement in improvements:
            if improvement["type"] == "code_modification":
                line_number = improvement.get("line_number", -1)
                if line_number >= 0:
                    lines = modified_content.split("\n")
                    if line_number < len(lines):
                        original_line = lines[line_number]
                        if original_line == improvement["original_code"]:
                            lines[line_number] = improvement["improved_code"]
                            modified_content = "\n".join(lines)
                            applied_improvements.append(improvement)

        # Write modified content back to file
        if modified_content != content:
            try:
                # Create backup
                backup_path = full_path + ".bak"
                with open(backup_path, "w") as f:
                    f.write(content)

                # Write modified content
                with open(full_path, "w") as f:
                    f.write(modified_content)

                # Record modification
                self.modification_history.append(
                    {
                        "module_path": module_path,
                        "timestamp": time.time(),
                        "improvements": applied_improvements,
                        "backup_path": backup_path,
                    }
                )

                return {
                    "success": True,
                    "applied_improvements": applied_improvements,
                    "backup_path": backup_path,
                }

            except Exception as e:
                return {"success": False, "error": f"Error writing module: {str(e)}"}

        return {"success": False, "error": "No improvements applied"}

    def get_modification_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the modification history.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of modification records
        """
        return sorted(
            self.modification_history, key=lambda x: x.get("timestamp", 0), reverse=True
        )[:limit]
