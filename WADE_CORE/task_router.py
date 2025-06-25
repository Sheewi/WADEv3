# -*- coding: utf-8 -*-
"""
WADE_CORE Task Router
Handles routing and execution of tasks to appropriate agents.
"""

import time
from typing import Dict, List, Any, Optional


class TaskRouter:
    """
    Routes tasks to appropriate agents and manages execution flow.
    Provides a layer of abstraction between the core logic and agent execution.
    """

    def __init__(self, elite_few):
        """Initialize the task router with reference to EliteFew."""
        self.elite_few = elite_few
        self.active_tasks = {}
        self.task_history = []

    def execute_plan(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete action plan by routing each step to appropriate agents.

        Args:
            action_plan: Dictionary containing plan description and steps

        Returns:
            Dictionary with execution results and status
        """
        if not action_plan or not action_plan.get("steps"):
            return {
                "status": "error",
                "message": "Invalid action plan: missing steps",
                "results": [],
            }

        plan_id = f"plan_{int(time.time())}"
        self.elite_few.log_and_respond(
            f"Executing plan: {action_plan['description']}", component="TASK_ROUTER"
        )

        results = []
        step_count = len(action_plan["steps"])

        for i, step in enumerate(action_plan["steps"]):
            step_id = f"{plan_id}_step_{i+1}"
            agent_name = step.get("agent")
            action = step.get("action")
            params = step.get("params", {})

            self.elite_few.log_and_respond(
                f"Executing step {i+1}/{step_count}: {agent_name} - {action}",
                level="INFO",
                component="TASK_EXECUTION",
            )

            # Track active task
            self.active_tasks[step_id] = {
                "plan_id": plan_id,
                "step_index": i,
                "agent": agent_name,
                "action": action,
                "params": params,
                "status": "running",
                "start_time": time.time(),
            }

            # Execute the step
            try:
                step_result = self._execute_step(agent_name, action, params)

                # Update task status
                self.active_tasks[step_id]["status"] = "completed"
                self.active_tasks[step_id]["end_time"] = time.time()
                self.active_tasks[step_id]["result"] = step_result

                # Add to results
                results.append(
                    {
                        "step_id": step_id,
                        "agent": agent_name,
                        "action": action,
                        "status": (
                            "success"
                            if step_result.get("status") == "success"
                            else "error"
                        ),
                        "data": step_result.get("data", {}),
                        "message": step_result.get("message", ""),
                    }
                )

                # If step failed, abort plan execution
                if step_result.get("status") != "success":
                    self.elite_few.log_and_respond(
                        f"Step {i+1} failed: {step_result.get('message', 'Unknown error')}. Aborting plan execution.",
                        level="ERROR",
                        component="TASK_EXECUTION",
                    )

                    # Archive completed task
                    self._archive_task(step_id)

                    return {
                        "status": "error",
                        "message": f"Plan execution failed at step {i+1}: {step_result.get('message', 'Unknown error')}",
                        "results": results,
                    }

            except Exception as e:
                # Handle exceptions during step execution
                error_message = f"Exception during step {i+1} execution: {str(e)}"
                self.elite_few.log_and_respond(
                    error_message, level="ERROR", component="TASK_EXECUTION"
                )

                # Update task status
                self.active_tasks[step_id]["status"] = "failed"
                self.active_tasks[step_id]["end_time"] = time.time()
                self.active_tasks[step_id]["error"] = str(e)

                # Add to results
                results.append(
                    {
                        "step_id": step_id,
                        "agent": agent_name,
                        "action": action,
                        "status": "error",
                        "message": error_message,
                    }
                )

                # Archive completed task
                self._archive_task(step_id)

                return {"status": "error", "message": error_message, "results": results}

            # Archive completed task
            self._archive_task(step_id)

        # All steps completed successfully
        self.elite_few.log_and_respond(
            f"Plan execution completed successfully: {action_plan['description']}",
            level="INFO",
            component="TASK_EXECUTION",
        )

        return {
            "status": "success",
            "message": "Plan execution completed successfully",
            "results": results,
        }

    def _execute_step(
        self, agent_name: str, action: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single step by routing to the appropriate agent.

        Args:
            agent_name: Name of the agent to execute the action
            action: Action to execute
            params: Parameters for the action

        Returns:
            Dictionary with execution results
        """
        # Get agent instance
        agent = self.elite_few.agent_manager.spawn_agent(agent_name)

        if not agent:
            return {
                "status": "error",
                "message": f"Agent '{agent_name}' not found or could not be spawned",
            }

        # Execute action
        result = agent.execute_action(action, params, self.elite_few.wade_core)

        return result

    def _archive_task(self, task_id: str):
        """
        Archive a completed task from active_tasks to task_history.

        Args:
            task_id: ID of the task to archive
        """
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            self.task_history.append(task)
            del self.active_tasks[task_id]

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active tasks."""
        return self.active_tasks

    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get task execution history.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of task execution records
        """
        return self.task_history[-limit:]
