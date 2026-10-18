"""
Configurable AI service with LLM API support (Gemini / OpenAI)
and a built-in deterministic pedagogical engine when no API keys are provided.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from ..config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self._openai_client = None
        
        if self.openai_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.openai_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def analyze_goal_and_plan(
        self,
        goal: str,
        starting_level: str,
        weekly_hours: float,
        duration_weeks: int,
        preferred_format: str
    ) -> Dict[str, Any]:
        """
        Uses configured LLM or fallback deterministic engine to produce
        prerequisite-aware modules, weekly breakdown, and learning outcomes.
        """
        if self._openai_client and self.provider == "openai":
            try:
                return self._call_openai(goal, starting_level, weekly_hours, duration_weeks, preferred_format)
            except Exception as e:
                logger.error(f"OpenAI call failed, falling back to deterministic engine: {e}")

        # Deterministic Fallback Engine (Fast, robust, perfectly tailored)
        return self._deterministic_curriculum(goal, starting_level, weekly_hours, duration_weeks, preferred_format)

    def _call_openai(
        self,
        goal: str,
        starting_level: str,
        weekly_hours: float,
        duration_weeks: int,
        preferred_format: str
    ) -> Dict[str, Any]:
        prompt = f"""
        You are a senior curriculum architect. Generate a structured prerequisite-aware learning roadmap for:
        Goal: {goal}
        Level: {starting_level}
        Weekly Hours: {weekly_hours}
        Duration: {duration_weeks} weeks
        Total Budget: {weekly_hours * duration_weeks} hours
        Format Preference: {preferred_format}

        Return strictly valid JSON with keys:
        - "feasibility": {{"status": "feasible"|"constrained_scope", "notes": "..."}}
        - "modules": list of objects {{"title": "...", "description": "...", "skills_covered": [...], "prerequisites": [...], "learning_outcomes": [...], "estimated_hours": float}}
        - "weekly_focus": list of objects {{"week_number": int, "focus_topic": "...", "allocated_hours": float, "module_index": int, "exercises": [...], "milestone_assessment": "..."}}
        """
        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _deterministic_curriculum(
        self,
        goal: str,
        starting_level: str,
        weekly_hours: float,
        duration_weeks: int,
        preferred_format: str
    ) -> Dict[str, Any]:
        """
        Deterministic, high-quality curriculum generator ensuring strict mathematical
        invariants: weekly allocation <= weekly_hours, foundational prerequisites first.
        """
        goal_lower = goal.lower()
        total_hours = weekly_hours * duration_weeks

        # Determine domain
        if any(term in goal_lower for term in ["data", "analyst", "analytics", "bi", "sql", "excel"]):
            return self._build_data_analyst_curriculum(starting_level, weekly_hours, duration_weeks, total_hours)
        elif any(term in goal_lower for term in ["web", "frontend", "fullstack", "react", "javascript", "developer"]):
            return self._build_web_dev_curriculum(starting_level, weekly_hours, duration_weeks, total_hours)
        elif any(term in goal_lower for term in ["ml", "machine learning", "ai", "artificial intelligence", "deep learning"]):
            return self._build_ml_curriculum(starting_level, weekly_hours, duration_weeks, total_hours)
        else:
            return self._build_general_tech_curriculum(goal, starting_level, weekly_hours, duration_weeks, total_hours)

    def _build_data_analyst_curriculum(
        self,
        starting_level: str,
        weekly_hours: float,
        duration_weeks: int,
        total_hours: float
    ) -> Dict[str, Any]:
        modules = [
            {
                "title": "Module 1: Spreadsheets & Data Cleaning Foundations",
                "description": "Master data manipulation, pivot tables, lookup formulas, and data hygiene in Excel/Google Sheets.",
                "subdomain": "spreadsheets",
                "skills_covered": ["Excel", "Google Sheets", "VLOOKUP/XLOOKUP", "Pivot Tables", "Data Cleaning"],
                "prerequisites": [],
                "learning_outcomes": [
                    "Perform multi-criteria aggregations using SUMIFS, COUNTIFS",
                    "Audit and normalize dirty CSV records with formulaic cleaning",
                    "Build an executive summary dashboard with dynamic pivot charts"
                ],
                "estimated_hours": 20.0
            },
            {
                "title": "Module 2: Relational Databases & SQL Querying",
                "description": "Extract, filter, aggregate, and join complex relational business data using SQL.",
                "subdomain": "sql",
                "skills_covered": ["SQL", "SELECT", "WHERE", "JOINs", "GROUP BY", "Window Functions"],
                "prerequisites": ["Spreadsheets & Data Cleaning Foundations"],
                "learning_outcomes": [
                    "Formulate multi-table INNER and LEFT JOIN queries",
                    "Compute running totals and rankings using SQL Window functions",
                    "Optimize relational queries for large analytical tables"
                ],
                "estimated_hours": 25.0
            },
            {
                "title": "Module 3: Python for Data Analysis & Pandas",
                "description": "Programmatic data analysis using Python, Jupyter notebooks, and Pandas DataFrames.",
                "subdomain": "python",
                "skills_covered": ["Python", "Pandas", "NumPy", "DataFrames", "Missing Data Handling"],
                "prerequisites": ["Relational Databases & SQL Querying"],
                "learning_outcomes": [
                    "Read, filter, and transform complex JSON and CSV datasets in Pandas",
                    "Perform group-by operations, lambda transformations, and datetime parsing",
                    "Automate ETL pipelines for repetitive analytical tasks"
                ],
                "estimated_hours": 30.0
            },
            {
                "title": "Module 4: Exploratory Data Visualization & BI Tools",
                "description": "Tell compelling stories with data using Seaborn, Matplotlib, and Tableau Public dashboards.",
                "subdomain": "visualization",
                "skills_covered": ["Tableau", "Power BI", "Seaborn", "Matplotlib", "Data Storytelling"],
                "prerequisites": ["Python for Data Analysis & Pandas"],
                "learning_outcomes": [
                    "Design interactive Tableau dashboards with filters and parameters",
                    "Create publication-ready statistical distributions and heatmaps",
                    "Translate technical metrics into executive insights"
                ],
                "estimated_hours": 25.0
            },
            {
                "title": "Module 5: Applied Business Statistics & A/B Testing",
                "description": "Essential probability, statistical hypothesis testing, and confidence intervals for data decisions.",
                "subdomain": "statistics",
                "skills_covered": ["Statistics", "Hypothesis Testing", "A/B Testing", "Distributions", "p-values"],
                "prerequisites": ["Python for Data Analysis & Pandas"],
                "learning_outcomes": [
                    "Formulate null and alternative hypotheses for business experiments",
                    "Compute p-values and confidence intervals to evaluate campaign impact",
                    "Avoid common statistical fallacies like survivorship and selection bias"
                ],
                "estimated_hours": 15.0
            },
            {
                "title": "Module 6: Capstone Portfolio Projects & Real-World Datasets",
                "description": "End-to-end data analysis projects demonstrating end-to-end problem solving for employers.",
                "subdomain": "capstone",
                "skills_covered": ["Portfolio Building", "Kaggle EDA", "GitHub Documentation", "Business Presentation"],
                "prerequisites": [
                    "Relational Databases & SQL Querying",
                    "Python for Data Analysis & Pandas",
                    "Exploratory Data Visualization & BI Tools"
                ],
                "learning_outcomes": [
                    "Complete 2 end-to-end analytical case studies published on GitHub",
                    "Deliver an executive slide deck summarizing findings and ROI",
                    "Conduct peer code review and reproducible documentation"
                ],
                "estimated_hours": 20.0
            }
        ]

        total_module_hours = sum(m["estimated_hours"] for m in modules)
        
        # Check feasibility against budget
        if total_hours < 50:
            feasibility = {
                "status": "constrained_scope",
                "notes": f"Total time budget ({total_hours:.0f} hrs) is tight for complete professional mastery. Scope prioritized to core Foundations (Excel + SQL + Essential Python)."
            }
        elif total_hours < total_module_hours:
            feasibility = {
                "status": "constrained_scope",
                "notes": f"Available {total_hours:.0f} hours covers core competencies. Advanced capstone will focus on lean MVP projects."
            }
        else:
            feasibility = {
                "status": "feasible",
                "notes": f"Goal is completely feasible! Total budget of {total_hours:.0f} hours across {duration_weeks} weeks ({weekly_hours:.1f} hrs/week) allows full mastery of spreadsheets, SQL, Python, visualization, and portfolio capstones."
            }

        # Build week-by-week plan
        weekly_focus = []
        weeks_per_module = max(1, duration_weeks // len(modules))
        
        for w in range(1, duration_weeks + 1):
            mod_idx = min(len(modules) - 1, (w - 1) // weeks_per_module)
            cur_mod = modules[mod_idx]
            
            # Allocation must NEVER exceed weekly_hours
            allocated = min(weekly_hours, round(cur_mod["estimated_hours"] / weeks_per_module, 1))
            if allocated <= 0 or allocated > weekly_hours:
                allocated = weekly_hours

            exercises = [
                f"Hands-on practice: Apply {cur_mod['skills_covered'][0]} exercises on practice dataset",
                f"Coding challenge: Complete 3 interactive problems covering {cur_mod['skills_covered'][-1]}"
            ]
            assessment = f"Week {w} Milestone: Code submission and mini-quiz on {cur_mod['title']}"

            weekly_focus.append({
                "week_number": w,
                "focus_topic": f"{cur_mod['title']} (Part {((w - 1) % weeks_per_module) + 1})",
                "allocated_hours": float(allocated),
                "module_index": mod_idx,
                "exercises": exercises,
                "milestone_assessment": assessment
            })

        return {
            "feasibility": feasibility,
            "modules": modules,
            "weekly_focus": weekly_focus
        }

    def _build_web_dev_curriculum(
        self,
        starting_level: str,
        weekly_hours: float,
        duration_weeks: int,
        total_hours: float
    ) -> Dict[str, Any]:
        modules = [
            {
                "title": "Module 1: Semantic HTML5, Modern CSS3 & Responsive Layouts",
                "description": "Building accessible, mobile-responsive page layouts with Flexbox and CSS Grid.",
                "subdomain": "frontend",
                "skills_covered": ["HTML5", "CSS3", "Flexbox", "CSS Grid", "Responsive Design"],
                "prerequisites": [],
                "learning_outcomes": ["Build responsive page", "Implement semantic structure"],
                "estimated_hours": 20.0
            },
            {
                "title": "Module 2: JavaScript Fundamentals & DOM Manipulation",
                "description": "Core programming, functions, loops, async/await, and browser DOM events.",
                "subdomain": "frontend",
                "skills_covered": ["JavaScript", "ES6+", "DOM", "Async/Await", "Fetch API"],
                "prerequisites": ["Semantic HTML5, Modern CSS3 & Responsive Layouts"],
                "learning_outcomes": ["Manipulate DOM", "Fetch REST APIs asynchronously"],
                "estimated_hours": 30.0
            },
            {
                "title": "Module 3: React.js & Modern Component Architecture",
                "description": "Hooks, state management, component lifecycle, and reactive client interfaces.",
                "subdomain": "frontend",
                "skills_covered": ["React", "JSX", "useState", "useEffect", "Tailwind CSS"],
                "prerequisites": ["JavaScript Fundamentals & DOM Manipulation"],
                "learning_outcomes": ["Create dynamic single-page web applications", "Manage client state"],
                "estimated_hours": 35.0
            }
        ]
        return self._package_curriculum("Web Developer", modules, weekly_hours, duration_weeks, total_hours)

    def _build_ml_curriculum(
        self,
        starting_level: str,
        weekly_hours: float,
        duration_weeks: int,
        total_hours: float
    ) -> Dict[str, Any]:
        modules = [
            {
                "title": "Module 1: Python & Numerical Computing (NumPy & Pandas)",
                "description": "Vectorized computations, matrix math, and data wrangling for machine learning.",
                "subdomain": "python",
                "skills_covered": ["Python", "NumPy", "Pandas", "Linear Algebra"],
                "prerequisites": [],
                "learning_outcomes": ["Vectorized array operations", "Data cleansing for ML"],
                "estimated_hours": 25.0
            },
            {
                "title": "Module 2: Classical Machine Learning & Scikit-Learn",
                "description": "Supervised and unsupervised models: regression, classification, random forests, clustering.",
                "subdomain": "ml_basics",
                "skills_covered": ["Scikit-Learn", "Regression", "Classification", "Model Evaluation"],
                "prerequisites": ["Python & Numerical Computing (NumPy & Pandas)"],
                "learning_outcomes": ["Train supervised classifiers", "Evaluate with precision, recall, and ROC-AUC"],
                "estimated_hours": 30.0
            },
            {
                "title": "Module 3: Deep Learning & Neural Architectures",
                "description": "Neural networks, PyTorch fundamentals, computer vision, and transformers.",
                "subdomain": "deep_learning",
                "skills_covered": ["PyTorch", "Neural Networks", "Backpropagation", "Transfer Learning"],
                "prerequisites": ["Classical Machine Learning & Scikit-Learn"],
                "learning_outcomes": ["Fine-tune pre-trained models", "Build CNN/Transformer pipelines"],
                "estimated_hours": 35.0
            }
        ]
        return self._package_curriculum("Machine Learning Engineer", modules, weekly_hours, duration_weeks, total_hours)

    def _build_general_tech_curriculum(
        self,
        goal: str,
        starting_level: str,
        weekly_hours: float,
        duration_weeks: int,
        total_hours: float
    ) -> Dict[str, Any]:
        modules = [
            {
                "title": f"Module 1: Foundations of {goal}",
                "description": f"Core principles, terminology, and foundational tooling for {goal}.",
                "subdomain": "general",
                "skills_covered": ["Foundational Theory", "Tooling Setup", "Core Syntax"],
                "prerequisites": [],
                "learning_outcomes": ["Master basic setup and concepts", "Execute baseline workflows"],
                "estimated_hours": 20.0
            },
            {
                "title": f"Module 2: Practical Implementation & Intermediate Techniques",
                "description": f"Hands-on problem solving and applied workflows in {goal}.",
                "subdomain": "general",
                "skills_covered": ["Applied Workflows", "Debugging", "Optimization"],
                "prerequisites": [f"Foundations of {goal}"],
                "learning_outcomes": ["Implement complex features", "Debug common failure modes"],
                "estimated_hours": 30.0
            },
            {
                "title": f"Module 3: Advanced Projects & Real-World Capstone",
                "description": f"Demonstration projects, portfolio deliverables, and capstone assessment.",
                "subdomain": "general",
                "skills_covered": ["Portfolio Project", "Documentation", "Production Readiness"],
                "prerequisites": [f"Practical Implementation & Intermediate Techniques"],
                "learning_outcomes": ["Publish capstone artifact", "Conduct self-directed analysis"],
                "estimated_hours": 30.0
            }
        ]
        return self._package_curriculum(goal, modules, weekly_hours, duration_weeks, total_hours)

    def _package_curriculum(self, goal_name: str, modules: List[Dict[str, Any]], weekly_hours: float, duration_weeks: int, total_hours: float) -> Dict[str, Any]:
        feasibility = {
            "status": "feasible",
            "notes": f"Goal '{goal_name}' has a {total_hours:.0f}-hour total budget across {duration_weeks} weeks. Successfully planned within weekly time budget."
        }
        weekly_focus = []
        weeks_per_module = max(1, duration_weeks // len(modules))
        for w in range(1, duration_weeks + 1):
            mod_idx = min(len(modules) - 1, (w - 1) // weeks_per_module)
            cur_mod = modules[mod_idx]
            weekly_focus.append({
                "week_number": w,
                "focus_topic": f"{cur_mod['title']} (Part {((w - 1) % weeks_per_module) + 1})",
                "allocated_hours": float(min(weekly_hours, round(cur_mod['estimated_hours'] / weeks_per_module, 1) or weekly_hours)),
                "module_index": mod_idx,
                "exercises": [f"Complete weekly practical exercise on {cur_mod['skills_covered'][0]}"],
                "milestone_assessment": f"Week {w} Knowledge Check & Implementation Task"
            })
        return {
            "feasibility": feasibility,
            "modules": modules,
            "weekly_focus": weekly_focus
        }

llm_service = LLMService()
