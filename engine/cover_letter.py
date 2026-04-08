"""Cover letter generation based on job-skill matching."""

from .profile import Profile
from .job_model import JobListing


SKILL_TO_ACHIEVEMENT = {
    "llm": "Built multi-agent LLM orchestration for automated decision-making, increasing accuracy from 60% to 90%+",
    "agent": "Built multi-agent LLM orchestration for automated decision-making, increasing accuracy from 60% to 90%+",
    "rag": "Rebuilt decision engine using RAG-based architectures, improving accuracy from ~40% to 85% and reducing hallucination from 12% to <2%",
    "nlp": "Rebuilt decision engine using RAG-based architectures, improving accuracy from ~40% to 85% and reducing hallucination from 12% to <2%",
    "computer vision": "Re-architected diagnostic scanning pipeline with custom YOLOX-tiny models, slashing processing time by 70%+",
    "yolo": "Re-architected diagnostic scanning pipeline with custom YOLOX-tiny models, slashing processing time by 70%+",
    "opencv": "Re-architected diagnostic scanning pipeline with custom YOLOX-tiny models, slashing processing time by 70%+",
    "object detection": "Re-architected diagnostic scanning pipeline with custom YOLOX-tiny models, slashing processing time by 70%+",
    "machine learning": "Owned the architecture and scale-up of autonomous ML systems processing 1500+ transactions/day with 85% accuracy",
    "deep learning": "Owned the architecture and scale-up of autonomous ML systems processing 1500+ transactions/day with 85% accuracy",
    "production": "Scaled ML systems from 0 to 1500+ daily transactions across multiple enterprise clients",
    "mlops": "Scaled ML systems from 0 to 1500+ daily transactions across multiple enterprise clients",
    "deploy": "Scaled ML systems from 0 to 1500+ daily transactions across multiple enterprise clients",
    "scale": "Scaled ML systems from 0 to 1500+ daily transactions across multiple enterprise clients",
    "pyspark": "Led a team delivering production recommendation systems for global clients, scaling data processing via PySpark",
    "spark": "Led a team delivering production recommendation systems for global clients, scaling data processing via PySpark",
    "recommendation": "Led a team delivering production recommendation systems for global clients, scaling data processing via PySpark",
    "data pipeline": "Engineered highly scalable ETL pipelines reducing data processing time by 80%",
    "etl": "Engineered highly scalable ETL pipelines reducing data processing time by 80%",
    "pytorch": "Designed and deployed custom PyTorch models including object detection and neural networks in production",
    "tensorflow": "Built and deployed models using TensorFlow and PyTorch in production environments",
    "aws": "Production deployment on AWS (S3, ECR, RDS) with Docker-based CI/CD pipelines",
    "docker": "Production deployment on AWS (S3, ECR, RDS) with Docker-based CI/CD pipelines",
    "healthcare": "Built compliance-critical decision systems for healthcare, with deep domain expertise",
    "medical": "Built compliance-critical decision systems for healthcare, with deep domain expertise",
    "team lead": "Led engineering teams delivering production ML systems on aggressive timelines",
    "leadership": "Led engineering teams delivering production ML systems on aggressive timelines",
    "genai": "Built multi-agent LLM orchestration for automated decision-making, increasing accuracy from 60% to 90%+",
    "search": "Built ML-powered search and retrieval systems using vector search and semantic matching",
    "vector": "Built ML-powered search and retrieval systems using vector search and semantic matching",
}


class CoverLetterGenerator:
    def __init__(self, profile: Profile):
        self.profile = profile

    def extract_keywords(self, job: JobListing) -> list[str]:
        text = f"{job.title} {job.description}".lower()
        return list({kw for kw in SKILL_TO_ACHIEVEMENT if kw in text})

    def select_achievements(self, job: JobListing, max_bullets: int = 3) -> list[str]:
        keywords = self.extract_keywords(job)
        seen = set()
        selected = []
        for kw in keywords:
            ach = SKILL_TO_ACHIEVEMENT.get(kw)
            if ach and ach not in seen:
                seen.add(ach)
                selected.append(ach)
                if len(selected) >= max_bullets:
                    break
        if not selected:
            selected = self.profile.key_achievements[:max_bullets]
        return selected

    def determine_focus(self, keywords: list[str]) -> str:
        kset = set(keywords)
        if kset & {"llm", "agent", "rag", "nlp", "genai"}:
            return "LLM systems, multi-agent orchestration, and RAG pipelines"
        if kset & {"computer vision", "yolo", "opencv", "object detection"}:
            return "computer vision and real-time object detection"
        if kset & {"pyspark", "spark", "recommendation", "etl", "data pipeline"}:
            return "scalable data pipelines and ML systems"
        if kset & {"healthcare", "medical"}:
            return "healthcare AI and compliance-critical decision systems"
        if kset & {"production", "mlops", "deploy", "scale"}:
            return "production ML engineering and MLOps"
        return "production ML systems and AI architecture"

    def generate(self, job: JobListing) -> str:
        achievements = self.select_achievements(job)
        keywords = self.extract_keywords(job)
        focus = self.determine_focus(keywords)
        bullets = "\n".join(f"- {a}" for a in achievements)
        p = self.profile
        exp = p.years_experience or 5

        return f"""Dear Hiring Team,

I'm writing to express my strong interest in the {job.title} position at {job.company}. With {exp}+ years of experience building and scaling production ML systems — from multi-agent LLM architectures to real-time computer vision pipelines — I'm excited about the opportunity to bring my expertise in {focus} to your team.

What I bring:

{p.summary or f"I have {exp}+ years of experience in ML engineering and AI systems."}

Relevant highlights:

{bullets}

I thrive in environments where I can take systems from prototype to production scale while balancing accuracy, latency, and cost constraints. I'd welcome the opportunity to discuss how my experience can contribute to {job.company}'s goals.

Best regards,
{p.name}
{p.email}{' | ' + p.phone if p.phone else ''}"""
