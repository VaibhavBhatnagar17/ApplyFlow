"""User profile and job preference dataclasses."""

from dataclasses import dataclass, field


ALL_SKILLS = [
    "Python", "PyTorch", "TensorFlow", "scikit-learn", "JAX",
    "LLM", "RAG", "Agents", "LangChain", "LangGraph", "CrewAI",
    "NLP", "Computer Vision", "OpenCV", "YOLO",
    "Deep Learning", "Machine Learning", "GenAI", "Prompt Engineering",
    "PySpark", "SQL", "Elasticsearch", "MongoDB", "PostgreSQL",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
    "CI/CD", "MLOps", "Flask", "FastAPI", "Django",
    "Pandas", "NumPy", "Spark", "Hadoop", "Airflow",
    "Recommendation Systems", "Search", "Ranking",
    "Data Science", "Statistics", "A/B Testing",
    "Reinforcement Learning", "GANs", "Diffusion Models",
    "Vector Search", "FAISS", "Pinecone",
    "Healthcare", "Fintech", "E-commerce",
    "Data Engineering", "ETL", "DBT", "Kafka", "Snowflake",
    "Power BI", "Tableau", "Business Analysis", "VLSI", "RTL",
    "SystemVerilog", "STA", "Synthesis", "Physical Design",
]

TARGET_ROLES = [
    # AI/ML
    "Machine Learning Engineer", "Senior Machine Learning Engineer", "ML Engineer", "Senior ML Engineer",
    "Data Scientist", "Senior Data Scientist", "AI Engineer", "Senior AI Engineer",
    "AI Architect", "GenAI Engineer", "LLM Engineer", "Applied Scientist",
    "Research Scientist", "MLOps Engineer", "NLP Engineer", "Computer Vision Engineer",
    "Agentic AI Engineer", "Prompt Engineer", "AI Product Engineer",
    # Data
    "Data Engineer", "Senior Data Engineer", "Analytics Engineer", "BI Engineer",
    "Data Analyst", "Business Analyst", "Product Analyst", "Research Analyst",
    # Software
    "Software Engineer", "Backend Engineer", "Platform Engineer", "Site Reliability Engineer",
    # VLSI / Hardware
    "VLSI Engineer", "STA Engineer", "RTL Design Engineer", "Physical Design Engineer",
    "Verification Engineer", "DFT Engineer", "SoC Engineer",
]

TARGET_LOCATIONS = [
    "Bangalore", "Bengaluru", "Hyderabad", "Mumbai",
    "Delhi", "Gurgaon", "Gurugram", "Noida", "Pune", "Chennai",
    "Remote", "San Francisco", "New York", "Seattle", "London", "Singapore",
]


@dataclass
class Profile:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""

    years_experience: int = 0
    current_title: str = ""
    current_company: str = ""
    summary: str = ""

    core_skills: list = field(default_factory=list)
    secondary_skills: list = field(default_factory=list)
    key_achievements: list = field(default_factory=list)
    domains: list = field(default_factory=list)
    education: str = ""
    certifications: str = ""

    career_goal: str = ""
    work_authorization: str = ""
    notice_period: str = "30 days"
    preferred_work_mode: str = "hybrid"
    willing_to_relocate: bool = True

    def is_complete(self) -> bool:
        return bool(self.name and self.core_skills and self.years_experience > 0)


@dataclass
class JobPreferences:
    target_titles: list = field(default_factory=lambda: TARGET_ROLES[:8])
    target_locations: list = field(default_factory=lambda: TARGET_LOCATIONS[:10])
    remote_preference: str = "remote_preferred"

    min_salary_inr: int = 0
    job_types: list = field(default_factory=lambda: ["Full-time"])
    industries: list = field(default_factory=list)

    excluded_companies: list = field(default_factory=list)
    preferred_companies: list = field(default_factory=list)

    must_have_keywords: list = field(default_factory=lambda: [
        "machine learning", "deep learning", "ML", "AI",
        "data science", "NLP", "computer vision", "LLM", "GenAI",
    ])
    nice_to_have_keywords: list = field(default_factory=lambda: [
        "PyTorch", "TensorFlow", "RAG", "agents",
        "production", "MLOps", "deployment",
    ])
    exclude_keywords: list = field(default_factory=lambda: [
        "intern", "internship", "junior", "entry level", "fresher",
    ])

    min_match_score: float = 0.3
