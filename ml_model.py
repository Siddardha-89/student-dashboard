import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Simplified ML logic as requested by the user
def predict_risk(gpa, attendance):
    """
    Risk Prediction:
    If GPA < 6 and Attendance < 70% → High Risk
    If GPA 6–7.5 → Medium Risk
    If GPA > 7.5 → Low Risk
    """
    if gpa < 6 and attendance < 70:
        risk = "High"
        color = "red"
        probability = 85.0
    elif 6 <= gpa <= 7.5:
        risk = "Medium"
        color = "yellow"
        probability = 45.0
    else:
        risk = "Low"
        color = "green"
        probability = 10.0
    
    return {"risk": risk, "color": color, "probability": probability}

def predict_placement(gpa, coding_score, communication_score, projects_count):
    """
    Placement Prediction:
    If GPA > 8 and Coding > 7 → 80–95% chance (Tier 1)
    If GPA 7–8 → 60–75% chance (Tier 2)
    Else → Below 50% (Tier 3)
    """
    if gpa > 8 and coding_score > 7:
        probability = np.random.uniform(80, 95)
        tier = "Tier 1"
        salary_range = "12 - 25 LPA"
    elif 7 <= gpa <= 8:
        probability = np.random.uniform(60, 75)
        tier = "Tier 2"
        salary_range = "6 - 12 LPA"
    else:
        probability = np.random.uniform(30, 50)
        tier = "Tier 3"
        salary_range = "3 - 6 LPA"
    
    return {
        "placement_probability": round(probability, 2),
        "eligible_tier": tier,
        "expected_salary": salary_range
    }

def get_improvement_suggestions(marks):
    """
    Smart Subject Improvement Suggestions
    """
    suggestions = []
    weak_subjects = [sub for sub, score in marks.items() if score < 50]
    
    if weak_subjects:
        for sub in weak_subjects:
            suggestions.append({
                "subject": sub,
                "suggestion": f"Focus more on {sub}. Dedicate at least 2 extra hours daily.",
                "resources": ["YouTube: Traversy Media", "YouTube: FreeCodeCamp"],
                "platforms": ["LeetCode", "HackerRank"]
            })
    else:
        suggestions.append({
                "subject": "All",
                "suggestion": "Keep up the good work! Focus on advanced projects and mock interviews.",
                "resources": ["YouTube: Tech with Tim"],
                "platforms": ["CodeChef", "GeeksforGeeks"]
            })
    
    return {
        "weak_subjects": weak_subjects,
        "personalized_suggestions": suggestions,
        "mock_interview": "Suggested" if not weak_subjects else "After improvement"
    }
