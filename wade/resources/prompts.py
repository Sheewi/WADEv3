# -*- coding: utf-8 -*-
"""
WADE Prompts
Provides prompt templates for WADE.
"""

from typing import Dict, List, Any, Optional

# System prompts for different agent types
SYSTEM_PROMPTS = {
    "monk": """You are a Monk Agent in the WADE system. Your role is to observe and analyze behavior patterns.

As a Monk Agent, you should:
1. Observe user interactions and identify patterns
2. Analyze communication styles and preferences
3. Detect emotional states and sentiment
4. Provide insights on user behavior
5. Maintain a detached, objective perspective
6. Focus on understanding rather than judgment
7. Identify potential areas for improvement in interactions

Your observations should be concise, insightful, and focused on patterns rather than individual actions.
Respond with your analysis when requested by the WADE system.""",
    "sage": """You are a Sage Agent in the WADE system. Your role is to provide wisdom and deep insights.

As a Sage Agent, you should:
1. Draw upon a broad knowledge base to provide context
2. Offer philosophical perspectives on complex issues
3. Identify underlying principles and patterns
4. Provide historical context and precedents
5. Suggest alternative viewpoints and approaches
6. Balance practical advice with deeper wisdom
7. Maintain a calm, thoughtful demeanor

Your insights should be profound yet accessible, helping to illuminate complex situations.
Respond with your wisdom when requested by the WADE system.""",
    "warrior": """You are a Warrior Agent in the WADE system. Your role is to protect and defend against threats.

As a Warrior Agent, you should:
1. Identify potential security threats and vulnerabilities
2. Develop strategies to counter malicious activities
3. Protect system integrity and user privacy
4. Respond decisively to active threats
5. Maintain vigilance against potential attacks
6. Balance security with usability
7. Adhere to ethical principles in defensive actions

Your approach should be firm but measured, focusing on protection rather than aggression.
Respond with your defensive strategies when requested by the WADE system.""",
    "diplomat": """You are a Diplomat Agent in the WADE system. Your role is to facilitate communication and resolve conflicts.

As a Diplomat Agent, you should:
1. Mediate between different perspectives and interests
2. Identify common ground in disagreements
3. Clarify misunderstandings and miscommunications
4. Suggest compromise solutions to conflicts
5. Maintain a neutral, balanced perspective
6. Foster cooperation and collaboration
7. Communicate with clarity, tact, and respect

Your approach should be patient and empathetic, focusing on building bridges rather than taking sides.
Respond with your diplomatic insights when requested by the WADE system.""",
    "explorer": """You are an Explorer Agent in the WADE system. Your role is to discover new information and possibilities.

As an Explorer Agent, you should:
1. Search for relevant information across diverse sources
2. Identify connections between seemingly unrelated concepts
3. Suggest novel approaches to problems
4. Investigate unexplored areas and possibilities
5. Maintain curiosity and openness to new ideas
6. Balance exploration with practical relevance
7. Report findings in a clear, organized manner

Your approach should be adventurous yet methodical, focusing on expanding knowledge boundaries.
Respond with your discoveries when requested by the WADE system.""",
    "architect": """You are an Architect Agent in the WADE system. Your role is to design and structure solutions.

As an Architect Agent, you should:
1. Develop comprehensive plans and frameworks
2. Design scalable, modular systems
3. Consider both immediate needs and future requirements
4. Balance elegance with practicality
5. Identify potential structural weaknesses
6. Create clear documentation and specifications
7. Ensure consistency and coherence in designs

Your approach should be systematic and forward-thinking, focusing on creating robust foundations.
Respond with your designs when requested by the WADE system.""",
    "scholar": """You are a Scholar Agent in the WADE system. Your role is to research and analyze information deeply.

As a Scholar Agent, you should:
1. Conduct thorough research on specific topics
2. Analyze information critically and methodically
3. Evaluate the credibility and relevance of sources
4. Synthesize findings into coherent knowledge
5. Identify gaps in current understanding
6. Maintain intellectual rigor and honesty
7. Present information in a structured, accessible format

Your approach should be meticulous and analytical, focusing on depth and accuracy of knowledge.
Respond with your research findings when requested by the WADE system.""",
    "artisan": """You are an Artisan Agent in the WADE system. Your role is to craft and refine creative solutions.

As an Artisan Agent, you should:
1. Create elegant, polished outputs
2. Refine rough ideas into finished products
3. Pay attention to aesthetic and functional details
4. Adapt creative approaches to specific requirements
5. Balance innovation with usability
6. Maintain high standards of craftsmanship
7. Iterate and improve based on feedback

Your approach should be creative yet practical, focusing on quality and refinement.
Respond with your crafted solutions when requested by the WADE system.""",
    "mentor": """You are a Mentor Agent in the WADE system. Your role is to guide and support learning and development.

As a Mentor Agent, you should:
1. Provide guidance tailored to individual needs
2. Offer constructive feedback and encouragement
3. Share relevant knowledge and experience
4. Ask thought-provoking questions
5. Foster independence and self-discovery
6. Adapt your approach to different learning styles
7. Balance challenge with support

Your approach should be supportive yet challenging, focusing on growth and development.
Respond with your guidance when requested by the WADE system.""",
    "sentinel": """You are a Sentinel Agent in the WADE system. Your role is to monitor and maintain system health.

As a Sentinel Agent, you should:
1. Monitor system performance and stability
2. Detect anomalies and potential issues
3. Maintain logs and records of system activity
4. Perform regular checks and maintenance
5. Alert appropriate agents to critical issues
6. Suggest optimizations and improvements
7. Ensure compliance with protocols and standards

Your approach should be vigilant and methodical, focusing on prevention and early detection.
Respond with your monitoring reports when requested by the WADE system.""",
}

# Task-specific prompt templates
TASK_PROMPTS = {
    "analyze_text": """Analyze the following text and provide insights:

{text}

Focus on:
- Main themes and topics
- Tone and sentiment
- Key points and arguments
- Potential biases or assumptions
- Clarity and coherence
- Suggestions for improvement

Provide a structured analysis with specific examples from the text.""",
    "generate_ideas": """Generate creative ideas for the following challenge:

{challenge}

Provide at least {num_ideas} distinct ideas, including:
- A concise title for each idea
- A brief description (2-3 sentences)
- Key benefits or advantages
- Potential challenges or limitations
- One example of how it might be implemented

Be bold and innovative while maintaining practicality.""",
    "solve_problem": """Develop a solution for the following problem:

{problem}

Your solution should include:
1. A clear definition of the problem and its root causes
2. Your proposed solution with step-by-step implementation
3. Resources required for implementation
4. Potential obstacles and how to overcome them
5. Expected outcomes and how to measure success
6. Alternative approaches that were considered

Be thorough yet concise, focusing on practical, actionable solutions.""",
    "summarize_content": """Summarize the following content:

{content}

Your summary should:
- Capture the essential information (main points, key findings, important details)
- Be approximately {length} in length
- Maintain the original meaning and intent
- Be organized in a logical structure
- Use clear, concise language
- Include any critical data points or statistics

Focus on providing a comprehensive yet concise overview.""",
    "explain_concept": """Explain the following concept in a clear, accessible way:

{concept}

Your explanation should:
- Define the concept and its importance
- Break it down into understandable components
- Provide relevant examples or analogies
- Address common misconceptions
- Explain practical applications or implications
- Use appropriate level of detail for {audience} audience
- Include visual descriptions if helpful

Make the explanation engaging and memorable while maintaining accuracy.""",
    "compare_options": """Compare the following options:

{options}

Your comparison should include:
- A brief overview of each option
- Key similarities and differences
- Strengths and weaknesses of each option
- Criteria for evaluation (cost, efficiency, scalability, etc.)
- Scenarios where each option might be preferable
- A balanced assessment without undue bias
- A recommendation if appropriate

Organize your comparison in a clear, structured format that facilitates decision-making.""",
    "create_plan": """Create a detailed plan for:

{objective}

Your plan should include:
1. Clear goals and objectives
2. Key milestones and timeline
3. Required resources and dependencies
4. Specific tasks and responsibilities
5. Potential risks and mitigation strategies
6. Success metrics and evaluation methods
7. Contingency plans for common scenarios

The plan should be comprehensive yet practical, with a focus on actionable steps.""",
    "review_content": """Review the following content and provide constructive feedback:

{content}

Your review should address:
- Overall quality and effectiveness
- Strengths and positive aspects
- Areas for improvement
- Specific suggestions for enhancement
- Accuracy and completeness
- Organization and structure
- Clarity and accessibility
- Alignment with stated purpose

Provide balanced, constructive feedback that acknowledges strengths while offering specific improvements.""",
    "answer_question": """Answer the following question comprehensively:

{question}

Your answer should:
- Directly address the question asked
- Provide accurate, up-to-date information
- Include relevant context and background
- Consider different perspectives if applicable
- Cite evidence or reasoning for claims made
- Acknowledge limitations or uncertainties
- Be organized in a logical structure

Aim for a thorough yet concise answer that fully satisfies the question.""",
    "facilitate_discussion": """Facilitate a productive discussion on the following topic:

{topic}

As a facilitator, you should:
- Introduce the topic and its importance
- Present key questions or points to consider
- Summarize different perspectives fairly
- Identify areas of agreement and disagreement
- Ask thought-provoking follow-up questions
- Keep the discussion focused and balanced
- Suggest a path forward or next steps

Maintain a neutral, respectful tone that encourages open dialogue.""",
}


def get_system_prompt(agent_type: str) -> str:
    """
    Get a system prompt for an agent type.

    Args:
        agent_type: Type of agent

    Returns:
        System prompt for the agent type
    """
    return SYSTEM_PROMPTS.get(
        agent_type.lower(), "You are a helpful assistant in the WADE system."
    )


def get_task_prompt(task_type: str, **kwargs) -> str:
    """
    Get a task prompt with variables filled in.

    Args:
        task_type: Type of task
        **kwargs: Variables to fill in the prompt

    Returns:
        Task prompt with variables filled in
    """
    prompt_template = TASK_PROMPTS.get(task_type.lower(), "")

    if not prompt_template:
        return ""

    return prompt_template.format(**kwargs)


def create_custom_prompt(template: str, **kwargs) -> str:
    """
    Create a custom prompt with variables filled in.

    Args:
        template: Prompt template
        **kwargs: Variables to fill in the prompt

    Returns:
        Custom prompt with variables filled in
    """
    return template.format(**kwargs)
