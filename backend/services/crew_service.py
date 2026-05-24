from textwrap import dedent
from typing import List
from crewai import Agent, Task, Crew, Process, LLM
from backend.core.config import settings
from backend.domain.schemas.models import AngleOutput
from backend.domain.schemas.ai_schemas import CrewOutput

class CrewService:
    def __init__(self):
        pass

    def generate_angles(self, notes: str) -> List[AngleOutput]:
        """Orchestrates the 3-agent CrewAI workflow to generate marketing angles."""
        
        gemini_llm = LLM(
            model="gemini/gemini-3.1-flash-lite",
            api_key=settings.gemini_api_key.get_secret_value()
        )
        
        # 1. The Strategist
        strategist = Agent(
            role="Expert Marketing Strategist",
            goal="Extract the core value proposition, target audience, and key features from raw, unstructured product notes.",
            backstory="You are a seasoned marketing strategist who excels at finding the signal in the noise. You turn messy founder brain-dumps into clear, actionable product briefs.",
            verbose=True,
            allow_delegation=False,
            llm=gemini_llm
        )

        # 2. The Copywriter
        copywriter = Agent(
            role="Direct Response Copywriter",
            goal="Write exactly 3 distinct marketing one-liners using proven frameworks: Benefit-Driven, Problem/Solution, and FOMO/Urgency.",
            backstory="You are a world-class copywriter. You write punchy, engaging, and high-converting copy. You hate fluff and jargon.",
            verbose=True,
            allow_delegation=False,
            llm=gemini_llm
        )

        # 3. The Editor
        editor = Agent(
            role="Strict QA Editor",
            goal="Cross-reference the copy against the original input to ensure accuracy, eliminate hallucinations, and format strictly to JSON.",
            backstory="You are a meticulous editor. You ensure that marketing copy never promises features that don't exist in the product brief. You are also a stickler for formatting rules.",
            verbose=True,
            allow_delegation=False,
            llm=gemini_llm
        )

        # Tasks
        task_extract = Task(
            description=dedent(f"""
                Analyze the following raw product notes:
                ---
                {notes}
                ---
                Extract the core value proposition, target audience, and key features.
                Create a structured brief for the copywriter. Do NOT hallucinate features.
            """),
            expected_output="A structured strategic brief containing core value prop, target audience, and key features.",
            agent=strategist
        )

        task_write = Task(
            description=dedent("""
                Using the strategic brief provided by the Strategist, write exactly 3 distinct marketing one-liners.
                Each one-liner must follow one of these frameworks:
                1. Benefit-Driven (Focus on the positive outcome)
                2. Problem/Solution (Highlight the pain point, then the product as the cure)
                3. FOMO/Urgency (Why they need to act now or what they are missing out on)
                
                Keep each one-liner under 3 sentences. Be punchy.
            """),
            expected_output="Three distinct marketing one-liners labeled by their framework.",
            agent=copywriter
        )

        task_edit = Task(
            description=dedent(f"""
                Review the 3 marketing one-liners provided by the Copywriter.
                Cross-reference them with the original notes:
                ---
                {notes}
                ---
                Ensure no features or claims were invented.
                Format the final output strictly matching the required JSON schema.
                The angle_type MUST exactly match: "Benefit-Driven", "Problem/Solution", or "FOMO/Urgency".
            """),
            expected_output="A JSON object containing the 3 verified angles, matching the CrewOutput Pydantic schema.",
            agent=editor,
            output_pydantic=CrewOutput
        )

        # Crew
        crew = Crew(
            agents=[strategist, copywriter, editor],
            tasks=[task_extract, task_write, task_edit],
            process=Process.sequential,
            verbose=True
        )

        # Kickoff
        result = crew.kickoff()
        
        # CrewAI returns the pydantic object if output_pydantic is set on the final task
        # If it returns a CrewOutput instance, we extract the angles
        if isinstance(result.pydantic, CrewOutput):
            return result.pydantic.angles
        else:
            # Fallback if CrewAI fails to map it to the pydantic object natively
            # This handles older versions or edge cases
            import json
            try:
                data = json.loads(result.raw)
                parsed = CrewOutput.model_validate(data)
                return parsed.angles
            except Exception:
                raise ValueError("Failed to parse CrewAI output into AngleOutput list.")

    def refine_angle(self, original_text: str, refinement_type: str) -> str:
        """Uses a single agent to quickly refine a text."""
        
        gemini_llm = LLM(
            model="gemini/gemini-3.1-flash-lite",
            api_key=settings.gemini_api_key.get_secret_value()
        )
        
        editor = Agent(
            role="Copy Editor",
            goal=f"Refine the provided marketing copy to make it {refinement_type}.",
            backstory="You are a precise copy editor. You adjust the tone or length of marketing copy without losing the core message.",
            verbose=False,
            allow_delegation=False,
            llm=gemini_llm
        )

        instructions = ""
        if refinement_type == "shorter":
            instructions = "Make the copy significantly more concise. Cut fluff. Keep the punchline."
        elif refinement_type == "casual":
            instructions = "Make the tone more conversational, relaxed, and approachable. Speak like a friendly human on social media."

        task = Task(
            description=dedent(f"""
                Refine the following marketing copy:
                ---
                {original_text}
                ---
                Instructions: {instructions}
                
                Return ONLY the refined text. No introductory phrases or quotes.
            """),
            expected_output="The refined marketing copy text.",
            agent=editor
        )

        crew = Crew(
            agents=[editor],
            tasks=[task],
            process=Process.sequential
        )

        result = crew.kickoff()
        return result.raw.strip(' "\'')
