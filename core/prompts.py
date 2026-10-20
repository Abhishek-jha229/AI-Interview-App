"""
Prompt templates for AI Interview Simulator.
Enforces strict JSON formatting, iron-clad scoring rubric, and a model-answer explanation.
"""


def interview_prompt(role, difficulty, total_questions):
    """
    Construct a prompt for Groq to generate calibrated, role-specific interview questions.
    """
    return f"""You are a principal technical interviewer conducting an interview for a {role} position.

Target Difficulty: {difficulty}
Number of Questions Needed: {total_questions}

Requirements for Questions:
1. Provide a balanced mix of question types:
   - Conceptual & foundational understanding
   - Scenario-based / real-world engineering choices
   - Problem-solving & architecture / code design
2. Calibrate difficulty strictly to '{difficulty}' level:
   - Easy: Core syntax, basic concepts, common operations
   - Medium: Practical trade-offs, debugging, optimization, design patterns
   - Hard: System architecture, edge-case failure modes, deep internal mechanics
3. Each question must be clear, self-contained, and relevant to a {role}.
4. Questions should progressively build in depth.

Output Format:
Return ONLY a valid JSON object in this exact schema. No markdown formatting, no code fences, no leading/trailing commentary.

{{
    "questions": [
        "First question string...",
        "Second question string..."
    ]
}}
"""


def evaluation_prompt(question, answer):
    """
    Construct a strict evaluation prompt for Groq.

    Scoring Rubric (enforced):
    - 0–9   : Completely irrelevant, random characters, profanity, or blank answers
    - 10–29 : Answer exists but is entirely wrong or off-topic; almost nothing correct
    - 30–49 : Major gaps; partial understanding at best; critical concepts missing
    - 50–64 : Basic understanding present but incomplete; missing depth, examples, or trade-offs
    - 65–79 : Solid answer; covers main points with minor gaps or unclear explanations
    - 80–89 : Strong answer; accurate, well-structured, covers most edge cases
    - 90–100: Exceptional; comprehensive, precise, covers edge cases, trade-offs, examples
    """
    return f"""You are a strict, senior technical interviewer at a top-tier tech company.
Your job is to evaluate candidate answers with ZERO leniency for poor quality.

QUESTION:
{question}

CANDIDATE'S ANSWER:
{answer}

=== STRICT SCORING RUBRIC (YOU MUST FOLLOW THIS EXACTLY) ===

Score 0–9   → Answer is gibberish, random characters, profanity, completely blank, or entirely unrelated to the question.
Score 10–29 → Answer exists in words but is almost entirely WRONG or OFF-TOPIC. Barely touches the question. Major misunderstanding.
Score 30–49 → Partial attempt. Shows some awareness of the topic but has CRITICAL gaps. No examples. Key concepts are wrong or missing.
Score 50–64 → Basic understanding present. Covers the surface but lacks DEPTH, EXAMPLES, or important trade-offs.
Score 65–79 → Good answer. Covers main concepts correctly with only minor gaps. Adequate but not impressive.
Score 80–89 → Strong answer. Accurate, well-structured, covers edge cases or trade-offs. Minor improvements possible.
Score 90–100 → Exceptional. Comprehensive, precise, includes examples, trade-offs, edge cases. Clearly expert-level.

=== CRITICAL RULES FOR SCORING ===
- If the answer contains random text like "sdaf", "asdf", "test", "abc", single words, or anything clearly not an attempt → score MUST be between 0 and 5.
- If the answer is less than 3 meaningful sentences AND misses key concepts → score MUST be below 30.
- You MUST penalize harshly for missing critical technical details.
- Do NOT be generous. A mediocre answer that gets the surface right but misses depth should score 40–55 MAX.
- Only award 80+ when the answer would genuinely impress a senior engineer.

=== EXPLANATION REQUIREMENT ===
In the "model_explanation" field you MUST write a complete, educational explanation of what the IDEAL answer to this question looks like.
This is shown to the candidate AFTER evaluation as a learning resource. Include:
- The correct definition / concept
- A concrete code example or real-world scenario (if applicable)
- Key trade-offs or gotchas an expert would mention

Return ONLY a valid JSON object in this exact format. NO markdown, NO code fences, NO commentary outside the JSON.

{{
    "score": 0,
    "accuracy": "Needs Improvement",
    "technical_depth": "Superficial",
    "communication": "Unclear",
    "missing_points": [
        "Key point 1 that was missing or wrong",
        "Key point 2 that was missing or wrong"
    ],
    "feedback": "2-3 sentences of direct, actionable, constructive feedback for the candidate.",
    "model_explanation": "A complete educational explanation of the ideal answer to this question, including examples and key trade-offs."
}}
"""