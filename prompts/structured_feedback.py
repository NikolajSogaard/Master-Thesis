from typing import Dict, List, Optional

STRUCTURED_FEEDBACK_FORMAT = '''
Please provide your feedback in the following format:

ANALYSIS:
[Your detailed analysis of the current program for this specific task]

ISSUES:
- [Issue 1]
- [Issue 2]
...

RECOMMENDATIONS:
1. [Specific recommendation with exact details]
2. [Specific recommendation with exact details]
...

CONCLUSION:
[Summarize if changes are needed or if program is optimal for this aspect]

If no changes are needed, include ONLY "No changes needed" in the RECOMMENDATIONS section.
'''

def parse_structured_feedback(feedback: str) -> Dict:
    """Parse structured feedback into a dictionary"""
    result = {
        "analysis": "",
        "issues": [],
        "recommendations": [],
        "modified_program": ""
    }
    
    current_section = None
    for line in feedback.split('\n'):
        line = line.strip()
        if line in ["ANALYSIS:", "ISSUES:", "RECOMMENDATIONS:", "MODIFIED_PROGRAM:"]:
            current_section = line[:-1].lower()
        elif current_section:
            if current_section == "issues" and line.startswith("- "):
                result["issues"].append(line[2:])
            elif current_section == "recommendations" and any(line.startswith(f"{i}. ") for i in range(1, 10)):
                result["recommendations"].append(line[3:])
            else:
                result[current_section] = result[current_section] + line + "\n"
                
    return result

def has_actionable_recommendations(feedback: Dict) -> bool:
    """Check if the feedback contains actionable recommendations"""
    # Check if recommendations section exists and isn't empty
    if not feedback.get("recommendations"):
        return False
        
    # Check if the only recommendation is that no changes are needed
    recommendations = "\n".join(feedback["recommendations"]).lower()
    no_changes_phrases = ["no changes needed", "none", "no changes are needed", "no changes required"]
    
    if any(phrase in recommendations for phrase in no_changes_phrases) and len(feedback["recommendations"]) == 1:
        return False
        
    return True
