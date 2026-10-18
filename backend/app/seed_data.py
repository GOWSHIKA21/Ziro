"""
Curated catalog of authentic, publicly accessible, genuinely free courses and official documentation.
All links point to well-established, free educational platforms and documentation sites.
Includes backup replacement resources mapped by skill domain.
"""

from typing import List, Dict, Any

VERIFIED_FREE_CATALOG: List[Dict[str, Any]] = [
    # ------------------ SPREADSHEETS & DATA FOUNDATIONS ------------------
    {
        "id": "res_cat_excel_gcf",
        "domain": "data_analysis",
        "subdomain": "spreadsheets",
        "title": "Excel Basics & Formulas - Free Interactive Tutorials",
        "provider": "GCFGlobal",
        "original_url": "https://edu.gcfglobal.org/en/excel/",
        "skills_covered": ["Excel", "Formulas", "VLOOKUP", "Pivot Tables", "Data Cleaning"],
        "estimated_hours": 15.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Interactive courses",
        "verification_notes": "100% free educational platform supported by Goodwill Community Foundation. No login required to read and download practice workbooks."
    },
    {
        "id": "res_cat_excel_msft",
        "domain": "data_analysis",
        "subdomain": "spreadsheets",
        "title": "Microsoft Excel Official Video Training & Guides",
        "provider": "Microsoft Learn",
        "original_url": "https://support.microsoft.com/en-us/office/excel-video-training-9bc05390-e94c-46af-972e-aa76ec9d9f08",
        "skills_covered": ["Excel", "Functions", "Data Filtering", "Conditional Formatting"],
        "estimated_hours": 10.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Videos",
        "verification_notes": "Free official Microsoft training with step-by-step videos and templates."
    },

    # ------------------ SQL & RELATIONAL DATABASES ------------------
    {
        "id": "res_cat_sql_kaggle",
        "domain": "data_analysis",
        "subdomain": "sql",
        "title": "Intro to SQL: Querying Large Datasets with BigQuery",
        "provider": "Kaggle Learn",
        "original_url": "https://www.kaggle.com/learn/intro-to-sql",
        "skills_covered": ["SQL", "SELECT", "WHERE", "GROUP BY", "HAVING", "BigQuery"],
        "estimated_hours": 12.0,
        "prerequisites": ["Spreadsheets"],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Interactive courses",
        "verification_notes": "Free interactive notebook environment provided by Google's Kaggle. Free certificate upon completion."
    },
    {
        "id": "res_cat_sql_postgres_tut",
        "domain": "data_analysis",
        "subdomain": "sql",
        "title": "PostgreSQL Complete Tutorial & Schema Practice",
        "provider": "PostgreSQL Tutorial",
        "original_url": "https://www.postgresqltutorial.com/",
        "skills_covered": ["SQL", "JOINs", "Subqueries", "Aggregations", "Window Functions"],
        "estimated_hours": 18.0,
        "prerequisites": ["Intro to SQL"],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Documentation",
        "verification_notes": "Free community-supported documentation and practical exercises for PostgreSQL."
    },
    {
        "id": "res_cat_sql_khan",
        "domain": "data_analysis",
        "subdomain": "sql",
        "title": "Intro to SQL: Querying and Managing Data",
        "provider": "Khan Academy",
        "original_url": "https://www.khanacademy.org/computing/computer-programming/sql",
        "skills_covered": ["SQL", "Relational Databases", "JOINs", "Data Modification"],
        "estimated_hours": 10.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Interactive courses",
        "verification_notes": "Free non-profit interactive SQL course with live browser query execution."
    },

    # ------------------ PYTHON FOR DATA ANALYSIS ------------------
    {
        "id": "res_cat_py_kaggle",
        "domain": "data_analysis",
        "subdomain": "python",
        "title": "Python: Hands-on Data Science Primer",
        "provider": "Kaggle Learn",
        "original_url": "https://www.kaggle.com/learn/python",
        "skills_covered": ["Python", "Variables", "Functions", "Lists", "Loops", "Dictionaries"],
        "estimated_hours": 15.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Interactive courses",
        "verification_notes": "Interactive Jupyter notebooks running in the browser, completely free."
    },
    {
        "id": "res_cat_py_official",
        "domain": "data_analysis",
        "subdomain": "python",
        "title": "The Python Tutorial (Official Python 3 Documentation)",
        "provider": "Python Software Foundation",
        "original_url": "https://docs.python.org/3/tutorial/",
        "skills_covered": ["Python", "Data Structures", "Modules", "Exceptions", "Standard Library"],
        "estimated_hours": 20.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Documentation",
        "verification_notes": "Official free open-source Python documentation."
    },

    # ------------------ DATA WRANGLING & PANDAS / NUMPY ------------------
    {
        "id": "res_cat_pandas_kaggle",
        "domain": "data_analysis",
        "subdomain": "pandas",
        "title": "Pandas for Data Manipulation and Analysis",
        "provider": "Kaggle Learn",
        "original_url": "https://www.kaggle.com/learn/pandas",
        "skills_covered": ["Pandas", "DataFrames", "Indexing", "Grouping", "Merging", "Missing Values"],
        "estimated_hours": 16.0,
        "prerequisites": ["Python"],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Interactive courses",
        "verification_notes": "Complete free hands-on exercises covering all core pandas methods."
    },
    {
        "id": "res_cat_pandas_docs",
        "domain": "data_analysis",
        "subdomain": "pandas",
        "title": "10 Minutes to Pandas & Getting Started Tutorials",
        "provider": "Pandas Documentation",
        "original_url": "https://pandas.pydata.org/docs/user_guide/10min.html",
        "skills_covered": ["Pandas", "NumPy", "Series", "Data Transformation"],
        "estimated_hours": 12.0,
        "prerequisites": ["Python"],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Documentation",
        "verification_notes": "Official pandas user guide with reproducible examples."
    },

    # ------------------ DATA VISUALIZATION & BI ------------------
    {
        "id": "res_cat_viz_kaggle",
        "domain": "data_analysis",
        "subdomain": "visualization",
        "title": "Data Visualization with Seaborn and Matplotlib",
        "provider": "Kaggle Learn",
        "original_url": "https://www.kaggle.com/learn/data-visualization",
        "skills_covered": ["Seaborn", "Matplotlib", "Bar Charts", "Heatmaps", "Scatter Plots"],
        "estimated_hours": 14.0,
        "prerequisites": ["Python", "Pandas"],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Interactive courses",
        "verification_notes": "Free practical visualization micro-course."
    },
    {
        "id": "res_cat_tableau_free",
        "domain": "data_analysis",
        "subdomain": "bi_tools",
        "title": "Tableau Public Training Videos and Starter Kits",
        "provider": "Tableau Software",
        "original_url": "https://www.tableau.com/learn/training/20222",
        "skills_covered": ["Tableau", "Interactive Dashboards", "Calculated Fields", "Storyboards"],
        "estimated_hours": 16.0,
        "prerequisites": ["Data Manipulation"],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Videos",
        "verification_notes": "Free official video training library for Tableau Public."
    },
    {
        "id": "res_cat_powerbi_msft",
        "domain": "data_analysis",
        "subdomain": "bi_tools",
        "title": "Get Started with Microsoft Power BI",
        "provider": "Microsoft Learn",
        "original_url": "https://learn.microsoft.com/en-us/training/paths/power-bi-getting-started/",
        "skills_covered": ["Power BI", "DAX", "Data Modeling", "Report Design"],
        "estimated_hours": 15.0,
        "prerequisites": ["Spreadsheets"],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Mixed",
        "verification_notes": "Free Microsoft official learning path with sandbox access."
    },

    # ------------------ STATISTICS & EXPERIMENTAL DESIGN ------------------
    {
        "id": "res_cat_stats_khan",
        "domain": "data_analysis",
        "subdomain": "statistics",
        "title": "High School and College Statistics & Probability",
        "provider": "Khan Academy",
        "original_url": "https://www.khanacademy.org/math/statistics-probability",
        "skills_covered": ["Mean/Median/Mode", "Standard Deviation", "Normal Distribution", "Hypothesis Testing", "p-values"],
        "estimated_hours": 20.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Mixed",
        "verification_notes": "World-renowned free non-profit education portal."
    },
    {
        "id": "res_cat_openintro_stats",
        "domain": "data_analysis",
        "subdomain": "statistics",
        "title": "OpenIntro Statistics (Free Open Textbook & Labs)",
        "provider": "OpenIntro",
        "original_url": "https://www.openintro.org/book/stat/",
        "skills_covered": ["Probability", "Inference", "Linear Regression", "Confidence Intervals"],
        "estimated_hours": 18.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Documentation",
        "verification_notes": "Free open-source peer-reviewed textbook and laboratory datasets."
    },

    # ------------------ CAPSTONE & PORTFOLIO PROJECTS ------------------
    {
        "id": "res_cat_capstone_fcc",
        "domain": "data_analysis",
        "subdomain": "capstone",
        "title": "Data Analysis with Python Certification & 5 Projects",
        "provider": "freeCodeCamp",
        "original_url": "https://www.freecodecamp.org/learn/data-analysis-with-python/",
        "skills_covered": ["Demographic Data Analyzer", "Medical Data Visualizer", "Page View Time Series", "Sea Level Predictor"],
        "estimated_hours": 25.0,
        "prerequisites": ["Python", "Pandas", "Matplotlib"],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Interactive courses",
        "verification_notes": "100% free verified certificate upon submitting 5 working project codebases."
    },
    {
        "id": "res_cat_kaggle_datasets",
        "domain": "data_analysis",
        "subdomain": "capstone",
        "title": "Kaggle Open Datasets & Analysis Competitions",
        "provider": "Kaggle",
        "original_url": "https://www.kaggle.com/datasets",
        "skills_covered": ["Real-world EDA", "Data Storytelling", "Portfolio Building"],
        "estimated_hours": 20.0,
        "prerequisites": ["SQL", "Pandas", "Data Visualization"],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Mixed",
        "verification_notes": "Public repositories of real company and civic datasets."
    },

    # ------------------ WEB DEVELOPMENT CATALOG ------------------
    {
        "id": "res_cat_web_fcc_html",
        "domain": "web_development",
        "subdomain": "frontend",
        "title": "Responsive Web Design Certification",
        "provider": "freeCodeCamp",
        "original_url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
        "skills_covered": ["HTML5", "CSS3", "Flexbox", "CSS Grid", "Responsive Design"],
        "estimated_hours": 25.0,
        "prerequisites": [],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Interactive courses",
        "verification_notes": "Free accredited interactive curriculum."
    },
    {
        "id": "res_cat_web_mdn_js",
        "domain": "web_development",
        "subdomain": "frontend",
        "title": "JavaScript Guide & Web Docs",
        "provider": "MDN Web Docs (Mozilla)",
        "original_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "skills_covered": ["JavaScript", "DOM", "Async/Await", "ES6+", "APIs"],
        "estimated_hours": 30.0,
        "prerequisites": ["HTML/CSS"],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Documentation",
        "verification_notes": "Gold standard web documentation by Mozilla Foundation."
    },
    {
        "id": "res_cat_web_react_docs",
        "domain": "web_development",
        "subdomain": "frontend",
        "title": "React Official Documentation: Quick Start & Tutorial",
        "provider": "React Team",
        "original_url": "https://react.dev/learn",
        "skills_covered": ["React", "Components", "Hooks", "State", "Effects"],
        "estimated_hours": 20.0,
        "prerequisites": ["JavaScript"],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Interactive courses",
        "verification_notes": "Official React documentation with live interactive code sandboxes."
    },

    # ------------------ MACHINE LEARNING CATALOG ------------------
    {
        "id": "res_cat_ml_kaggle_intro",
        "domain": "machine_learning",
        "subdomain": "ml_basics",
        "title": "Intro to Machine Learning",
        "provider": "Kaggle Learn",
        "original_url": "https://www.kaggle.com/learn/intro-to-machine-learning",
        "skills_covered": ["Decision Trees", "Random Forests", "Model Validation", "Underfitting/Overfitting"],
        "estimated_hours": 15.0,
        "prerequisites": ["Python", "Pandas"],
        "free_status": "verified_free",
        "account_required": True,
        "format": "Interactive courses",
        "verification_notes": "Free practical machine learning fundamentals on Kaggle."
    },
    {
        "id": "res_cat_ml_fastai",
        "domain": "machine_learning",
        "subdomain": "deep_learning",
        "title": "Practical Deep Learning for Coders",
        "provider": "fast.ai",
        "original_url": "https://course.fast.ai/",
        "skills_covered": ["Neural Networks", "Computer Vision", "NLP", "PyTorch"],
        "estimated_hours": 35.0,
        "prerequisites": ["Python"],
        "free_status": "verified_free",
        "account_required": False,
        "format": "Videos",
        "verification_notes": "Acclaimed free deep learning course by Jeremy Howard."
    }
]

# Replacement backup pool specifically indexed by skill/subdomain
REPLACEMENT_POOL: Dict[str, List[Dict[str, Any]]] = {
    "sql": [
        {
            "id": "res_rep_sql_w3schools",
            "title": "W3Schools SQL Tutorial & Live Database Sandbox",
            "provider": "W3Schools",
            "original_url": "https://www.w3schools.com/sql/",
            "skills_covered": ["SQL", "SELECT", "INSERT", "UPDATE", "JOINs"],
            "estimated_hours": 12.0,
            "prerequisites": [],
            "free_status": "verified_free",
            "account_required": False,
            "format": "Interactive courses",
            "verification_notes": "Verified free open access SQL training resource with in-browser SQL try-it editor."
        },
        {
            "id": "res_rep_sql_sqltutorial",
            "title": "SQLBolt - Interactive Lessons and Queries",
            "provider": "SQLBolt",
            "original_url": "https://sqlbolt.com/",
            "skills_covered": ["SQL", "Queries", "Aggregates", "Table Creation"],
            "estimated_hours": 10.0,
            "prerequisites": [],
            "free_status": "verified_free",
            "account_required": False,
            "format": "Interactive courses",
            "verification_notes": "100% free interactive lessons, no login or payment required."
        }
    ],
    "python": [
        {
            "id": "res_rep_py_fcc",
            "title": "Scientific Computing with Python Certification",
            "provider": "freeCodeCamp",
            "original_url": "https://www.freecodecamp.org/learn/scientific-computing-with-python/",
            "skills_covered": ["Python", "Algorithms", "Object Oriented Programming", "File I/O"],
            "estimated_hours": 20.0,
            "prerequisites": [],
            "free_status": "verified_free",
            "account_required": True,
            "format": "Interactive courses",
            "verification_notes": "Free non-profit accredited Python curriculum."
        },
        {
            "id": "res_rep_py_automating",
            "title": "Automate the Boring Stuff with Python (Free Online Edition)",
            "provider": "Al Sweigart (Creative Commons)",
            "original_url": "https://automatetheboringstuff.com/",
            "skills_covered": ["Python", "Scripting", "Regex", "Web Scraping", "Automation"],
            "estimated_hours": 18.0,
            "prerequisites": [],
            "free_status": "verified_free",
            "account_required": False,
            "format": "Documentation",
            "verification_notes": "Freely published under Creative Commons license on author's official site."
        }
    ],
    "spreadsheets": [
        {
            "id": "res_rep_sheets_benlcollins",
            "title": "Advanced Google Sheets Formulas & Pivot Tables",
            "provider": "Ben Collins Google Developer Expert",
            "original_url": "https://www.benlcollins.com/spreadsheets/starting-out-with-google-sheets/",
            "skills_covered": ["Google Sheets", "Array Formulas", "QUERY function", "Pivot Tables"],
            "estimated_hours": 12.0,
            "prerequisites": [],
            "free_status": "verified_free",
            "account_required": False,
            "format": "Documentation",
            "verification_notes": "Free official tutorials by recognized Google Sheets Developer Expert."
        }
    ],
    "pandas": [
        {
            "id": "res_rep_pandas_dataschool",
            "title": "Data School Pandas Video Series & Notebooks",
            "provider": "Data School",
            "original_url": "https://www.dataschool.io/easier-data-analysis-with-pandas/",
            "skills_covered": ["Pandas", "Filtering", "Aggregations", "String Methods"],
            "estimated_hours": 14.0,
            "prerequisites": ["Python"],
            "free_status": "verified_free",
            "account_required": False,
            "format": "Videos",
            "verification_notes": "High quality free video series with open source GitHub notebooks."
        }
    ],
    "visualization": [
        {
            "id": "res_rep_viz_python_graph_gallery",
            "title": "The Python Graph Gallery - Code & Charts",
            "provider": "Python Graph Gallery",
            "original_url": "https://python-graph-gallery.com/",
            "skills_covered": ["Matplotlib", "Seaborn", "Plotly", "Interactive Visualizations"],
            "estimated_hours": 12.0,
            "prerequisites": ["Python"],
            "free_status": "verified_free",
            "account_required": False,
            "format": "Documentation",
            "verification_notes": "Open-access chart gallery with reproducible copy-paste Python code."
        }
    ],
    "statistics": [
        {
            "id": "res_rep_stats_seeing_theory",
            "title": "Seeing Theory: A Visual Introduction to Probability and Data",
            "provider": "Brown University",
            "original_url": "https://seeing-theory.brown.edu/",
            "skills_covered": ["Probability", "Compound Probability", "Distributions", "Inference"],
            "estimated_hours": 10.0,
            "prerequisites": [],
            "free_status": "verified_free",
            "account_required": False,
            "format": "Interactive courses",
            "verification_notes": "Free educational project funded by Brown University."
        }
    ]
}
