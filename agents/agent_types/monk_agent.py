# -*- coding: utf-8 -*-
"""
WADE Monk Agent
Specializes in behavioral analysis and pattern recognition.
"""

from typing import Dict, List, Any, Optional
from ..base_agent import BaseAgent

class MonkAgent(BaseAgent):
    """
    Monk Agent - Behavioral Analysis Specialist
    
    Specializes in:
    - User behavior pattern recognition
    - Intent inference
    - Logical validation
    - Contextual understanding
    """
    
    def _initialize_impl(self):
        """Initialize the Monk agent."""
        self.state = {
            'behavioral_patterns': {},
            'intent_models': {},
            'context_history': []
        }
    
    def action_pattern_match_behavior(self, params: Dict[str, Any], wade_core) -> Dict[str, Any]:
        """
        Match behavioral patterns in user input.
        
        Args:
            params: Parameters including 'command', 'recent_commands', 'historical_goals'
            wade_core: Reference to WADE_OS_Core
            
        Returns:
            Dictionary with pattern matching results
        """
        command = params.get('command', '')
        recent_commands = params.get('recent_commands', [])
        historical_goals = params.get('historical_goals', [])
        
        # Simple pattern matching logic (placeholder for more sophisticated analysis)
        pattern = None
        confidence = 0.0
        
        # Check for recurring patterns in recent commands
        if recent_commands:
            recon_keywords = ['scan', 'network', 'reconnaissance', 'nmap', 'discover']
            security_keywords = ['exploit', 'vulnerability', 'attack', 'secure', 'protect']
            dev_keywords = ['build', 'develop', 'create', 'code', 'program']
            
            # Count keyword occurrences in recent commands
            recon_count = sum(1 for cmd in recent_commands if any(kw in cmd['data'].lower() for kw in recon_keywords))
            security_count = sum(1 for cmd in recent_commands if any(kw in cmd['data'].lower() for kw in security_keywords))
            dev_count = sum(1 for cmd in recent_commands if any(kw in cmd['data'].lower() for kw in dev_keywords))
            
            # Determine dominant pattern
            if recon_count >= 2 and any(kw in command.lower() for kw in recon_keywords):
                pattern = "recurring_recon"
                confidence = 0.7 + (recon_count * 0.05)  # Increase confidence with more matches
            elif security_count >= 2 and any(kw in command.lower() for kw in security_keywords):
                pattern = "prior_security_incident"
                confidence = 0.7 + (security_count * 0.05)
            elif dev_count >= 2 and any(kw in command.lower() for kw in dev_keywords):
                pattern = "development_pattern"
                confidence = 0.7 + (dev_count * 0.05)
        
        # Update state with new pattern
        if pattern:
            if pattern not in self.state['behavioral_patterns']:
                self.state['behavioral_patterns'][pattern] = {
                    'count': 1,
                    'confidence': confidence,
                    'examples': [command]
                }
            else:
                self.state['behavioral_patterns'][pattern]['count'] += 1
                self.state['behavioral_patterns'][pattern]['confidence'] = max(
                    self.state['behavioral_patterns'][pattern]['confidence'],
                    confidence
                )
                self.state['behavioral_patterns'][pattern]['examples'].append(command)
        
        return {
            'status': 'success',
            'data': {
                'pattern': pattern,
                'confidence': confidence,
                'behavioral_patterns': self.state['behavioral_patterns']
            }
        }
    
    def action_validate_user_logic(self, params: Dict[str, Any], wade_core) -> Dict[str, Any]:
        """
        Validate the logical consistency of user commands.
        
        Args:
            params: Parameters including 'command'
            wade_core: Reference to WADE_OS_Core
            
        Returns:
            Dictionary with validation results
        """
        command = params.get('command', '')
        
        # Simple logic validation (placeholder for more sophisticated analysis)
        is_valid = True
        reason = ""
        
        # Check for contradictory terms
        contradictions = [
            ('add', 'remove'),
            ('enable', 'disable'),
            ('start', 'stop'),
            ('create', 'delete'),
            ('increase', 'decrease')
        ]
        
        for term1, term2 in contradictions:
            if term1 in command.lower() and term2 in command.lower():
                is_valid = False
                reason = f"Command contains contradictory terms: '{term1}' and '{term2}'"
                break
        
        # Check for incomplete commands
        if command.lower().startswith(('if ', 'when ', 'while ')) and ' then ' not in command.lower():
            is_valid = False
            reason = "Conditional command is missing 'then' clause"
        
        # Check for vague commands
        vague_terms = ['something', 'somehow', 'whatever', 'anything', 'stuff']
        if any(term in command.lower() for term in vague_terms) and len(command.split()) < 10:
            is_valid = False
            reason = "Command is too vague or ambiguous"
        
        return {
            'status': 'success',
            'data': {
                'is_valid': is_valid,
                'reason': reason
            }
        }
    
    def action_analyze_context(self, params: Dict[str, Any], wade_core) -> Dict[str, Any]:
        """
        Analyze the current context to enhance understanding.
        
        Args:
            params: Parameters including 'current_context', 'recent_commands'
            wade_core: Reference to WADE_OS_Core
            
        Returns:
            Dictionary with context analysis results
        """
        current_context = params.get('current_context', {})
        recent_commands = params.get('recent_commands', [])
        
        # Update context history
        self.state['context_history'].append(current_context)
        if len(self.state['context_history']) > 10:
            self.state['context_history'] = self.state['context_history'][-10:]
        
        # Analyze context shifts
        context_shifts = []
        if len(self.state['context_history']) > 1:
            prev_context = self.state['context_history'][-2]
            for key in set(list(prev_context.keys()) + list(current_context.keys())):
                if key not in prev_context:
                    context_shifts.append(f"Added {key}")
                elif key not in current_context:
                    context_shifts.append(f"Removed {key}")
                elif prev_context[key] != current_context[key]:
                    context_shifts.append(f"Changed {key}")
        
        # Identify dominant themes in recent commands
        themes = {}
        for cmd in recent_commands:
            words = cmd['data'].lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    themes[word] = themes.get(word, 0) + 1
        
        # Sort themes by frequency
        dominant_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'status': 'success',
            'data': {
                'context_shifts': context_shifts,
                'dominant_themes': dominant_themes,
                'context_stability': len(context_shifts) < 3  # Context is stable if few shifts
            }
        }