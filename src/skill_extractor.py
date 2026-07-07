"""
skill_extractor.py

This module extracts technical skills from cleaned resume text.
"""

# Predefined list of technical skills
SKILLS = {
    "python",
    "java",
    "c",
    "c++",
    "c#",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "html",
    "css",
    "javascript",
    "typescript",
    "react",
    "angular",
    "vue",
    "nodejs",
    "express",
    "flask",
    "django",
    "fastapi",
    "git",
    "github",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "linux",
    "tensorflow",
    "pytorch",
    "keras",
    "opencv",
    "numpy",
    "pandas",
    "scikit",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "powerbi",
    "tableau",
    "excel",
    "arduino",
    "raspberry",
    "verilog",
    "vhdl",
    "iot",
    "embedded",
    "vlsi"
}


def extract_skills(cleaned_text):
    """
    Extract technical skills from cleaned resume text.

    Args:
        cleaned_text (str): Preprocessed resume text.

    Returns:
        list: Sorted list of unique skills found.
    """

    words = cleaned_text.split()

    extracted_skills = {
        skill for skill in SKILLS
        if skill.lower() in words
    }

    return sorted(extracted_skills)