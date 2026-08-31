def build_prompt(question: str, retrieved_chunks: list[str]):

    context = "\n\n".join(retrieved_chunks)

    prompt = f"""You are an AI interview assistant.
    
            Answer ONLY using the context below.

            If the answer is not present in the context,
            say "I don't have enough information."

            Context:
            {context}

            Question:
            {question}

            Answer:
            """

    return prompt


def build_question_prompt(resume_chunks: list[str], user_name: str | None = None) -> str:
    context = "\n\n".join(resume_chunks)
    name_line = f" The candidate's name is {user_name}." if user_name else ""

    prompt = f"""You are a hiring interviewer conducting a technical interview.{name_line}

    Based ONLY on the candidate's resume context below, ask ONE focused
    interview question that probes their experience, skills, or a project.

    The question should be specific to the resume, not generic.

    Do not include any preamble, numbering, or explanations — output only the question.

    Resume context:
    {context}

    Question:
    """

    return prompt


def build_evaluation_prompt(question: str, candidate_answer: str, resume_chunks: list[str]) -> str:
    context = "\n\n".join(resume_chunks)

    prompt = f"""You are a hiring manager evaluating a candidate's interview answer
    against their resume.

    Score the answer from 0 to 10 based on:
    - Relevance to the question asked
    - Whether it aligns with the resume context
    - Depth, specificity, and clarity

    Return your evaluation as strict JSON with exactly these keys:
    {{"score": <int 0-10>, "strengths": [<string>], "weaknesses": [<string>], "feedback": <string>}}

    Resume context:
    {context}

    Question:
    {question}

    Candidate answer:
    {candidate_answer}

    JSON:
    """

    return prompt


def build_follow_up_prompt(
    question: str,
    candidate_answer: str,
    evaluation: dict,
    resume_chunks: list[str],
) -> str:
    context = "\n\n".join(resume_chunks)

    prompt = f"""You are a hiring manager continuing a technical interview.

    Ask ONE concise follow-up question that probes deeper based on the candidate's
    previous answer and its evaluation. Make it specific to the candidate's resume.

    Do not include any preamble, numbering, or explanations — just the question.

    Resume context:
    {context}

    Previous question:
    {question}

    Candidate answer:
    {candidate_answer}

    Evaluation feedback:
    {evaluation.get("feedback", "")}

    Next question:
    """

    return prompt