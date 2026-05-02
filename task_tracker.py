"""
📋 Task Tracker Module
Manages goals, tasks, and progress tracking across different domains (learning, career, finance, wellness).
Uses Cosmos DB for persistent storage and pattern recognition.
"""

from datetime import datetime, timedelta
from azure.cosmos import CosmosClient, PartitionKey
from config import COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DB
from typing import Dict, List, Optional

goals_container = None
progress_container = None


def get_goals_container():
    global goals_container

    if goals_container is not None:
        return goals_container

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.create_database_if_not_exists(id=COSMOS_DB)
    goals_container = database.create_container_if_not_exists(
        id="goals",
        partition_key=PartitionKey(path="/user_id")
    )
    return goals_container


def get_progress_container():
    global progress_container

    if progress_container is not None:
        return progress_container

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.create_database_if_not_exists(id=COSMOS_DB)
    progress_container = database.create_container_if_not_exists(
        id="progress",
        partition_key=PartitionKey(path="/user_id")
    )
    return progress_container


# 🎯 CREATE GOAL
def create_goal(
    user_id: str,
    goal_title: str,
    domain: str,
    target_date: str,
    steps: List[str],
    metrics: Dict
) -> Dict:
    """
    Create a structured goal with milestones and tracking metrics.
    
    Args:
        user_id: Unique user identifier
        goal_title: Title of the goal
        domain: learning, career, finance, or wellness
        target_date: Target completion date
        steps: List of actionable steps
        metrics: Metrics to track progress {metric_name: target_value}
    
    Returns:
        Created goal object
    """
    goal = {
        "id": f"{user_id}_{goal_title}_{datetime.now().timestamp()}",
        "user_id": user_id,
        "title": goal_title,
        "domain": domain,
        "created_at": datetime.now().isoformat(),
        "target_date": target_date,
        "steps": steps,
        "metrics": metrics,
        "progress": 0,  # Percentage
        "status": "active",  # active, completed, paused
        "completion_milestones": []
    }
    
    try:
        get_goals_container().create_item(body=goal)
        return {"status": "success", "goal": goal}
    except Exception as e:
        print(f"Goal creation error: {e}")
        return {"status": "error", "message": str(e)}


# 📊 LOG PROGRESS
def log_progress(
    user_id: str,
    goal_id: str,
    metric_name: str,
    metric_value: float,
    note: str = ""
) -> Dict:
    """
    Log progress on a specific metric.
    
    Args:
        user_id: User identifier
        goal_id: Goal identifier
        metric_name: Name of the metric being tracked
        metric_value: Current value
        note: Optional note about progress
    
    Returns:
        Progress record
    """
    progress_record = {
        "id": f"{goal_id}_{datetime.now().timestamp()}",
        "user_id": user_id,
        "goal_id": goal_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "timestamp": datetime.now().isoformat(),
        "note": note
    }
    
    try:
        get_progress_container().create_item(body=progress_record)
        return {"status": "success", "record": progress_record}
    except Exception as e:
        print(f"Progress logging error: {e}")
        return {"status": "error", "message": str(e)}


# 📈 DETECT TRENDS
def detect_trends(user_id: str, goal_id: str, metric_name: str, domain: str = "general") -> Dict:
    """
    Analyze progress trends and detect patterns.

    Returns insight on whether progress is accelerating, decelerating, or stalled.
    """
    try:
        query = "SELECT * FROM c WHERE c.goal_id = @goal_id AND c.metric_name = @metric_name ORDER BY c.timestamp DESC"
        records = list(get_progress_container().query_items(
            query=query,
            parameters=[
                {"name": "@goal_id", "value": goal_id},
                {"name": "@metric_name", "value": metric_name}
            ]
        ))
        
        if len(records) < 2:
            return {"status": "insufficient_data", "message": "Need at least 2 data points"}
        
        recent_records = records[:7]  # Last 7 entries
        values = [r["metric_value"] for r in recent_records]
        
        # Calculate trend
        if len(values) >= 3:
            recent_avg = sum(values[:3]) / 3
            older_avg = sum(values[3:]) / len(values[3:])
            
            # Domain-aware trend logic: For finance/wellness, 'down' is often 'improving'
            is_inverse_metric = domain in ["finance", "wellness"] and any(word in metric_name.lower() for word in ["expense", "debt", "weight", "cost"])
            
            if is_inverse_metric:
                trend_direction = "improving" if recent_avg < older_avg else "declining" if recent_avg > older_avg else "stable"
            else:
                trend_direction = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
                
            improvement_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0
        else:
            trend_direction = "insufficient"
            improvement_rate = 0
        
        return {
            "status": "success",
            "metric": metric_name,
            "trend": trend_direction,
            "improvement_rate": round(improvement_rate, 2),
            "recent_values": values[:7],
            "recommendation": generate_trend_recommendation(trend_direction, improvement_rate),
            "proactive_actions": suggest_proactive_actions(domain, trend_direction, metric_name)
        }
    except Exception as e:
        print(f"Trend detection error: {e}")
        return {"status": "error", "message": str(e)}


# 💡 GENERATE TREND RECOMMENDATION
def generate_trend_recommendation(trend: str, rate: float) -> str:
    """Generate actionable recommendations based on trend analysis."""
    
    if trend == "improving":
        if rate > 20:
            return "🚀 Excellent progress! Keep up the momentum - you're significantly improving!"
        else:
            return "✅ Good progress! Small steady improvements add up - stay consistent."
    elif trend == "declining":
        if rate < -20:
            return "⚠️ Progress is declining significantly. Consider adjusting your strategy or breaking goals into smaller steps."
        else:
            return "📌 Slight decline detected. Try to refocus on your plan or seek additional resources."
    else:
        return "➡️ Progress is stable. To accelerate, consider increasing effort or trying new approaches."

def suggest_proactive_actions(domain: str, trend: str, metric: str) -> List[str]:
    """Demonstrates agentic reasoning by suggesting specific multi-step actions."""
    actions = {
        "learning": [
            "Schedule a deep-work session for tomorrow",
            "Generate a practice quiz based on the last 3 lessons",
            "Research advanced topics in this area using Bing Search"
        ],
        "finance": [
            "Review recurring subscriptions for potential cancellations",
            "Move 10% of this month's remaining budget to savings",
            "Search for high-yield savings accounts to maximize your progress"
        ],
        "wellness": [
            "Set a 'wind-down' reminder for 9:00 PM tonight",
            "Prepare a healthy meal prep list for the upcoming week",
            "Audit your sleep patterns to see if they correlate with your habit streaks"
        ]
    }
    
    base_actions = actions.get(domain, ["Review your overall goals for the week"])
    return base_actions if trend != "improving" else base_actions[:1] # Fewer actions needed if already crushing it


# 🎓 STUDY PLANNER (Learning Domain)
def create_study_plan(user_id: str, topic: str, exam_date: str, difficulty: str = "medium") -> Dict:
    """
    Create an adaptive study plan.
    
    Args:
        user_id: User identifier
        topic: Topic to study
        exam_date: Target exam date
        difficulty: beginner, intermediate, advanced
    
    Returns:
        Study plan with lessons and quizzes
    """
    
    difficulty_multiplier = {"beginner": 2, "intermediate": 1.5, "advanced": 1}[difficulty]
    days_until_exam = (datetime.fromisoformat(exam_date) - datetime.now()).days
    lessons_needed = max(5, int(days_until_exam / difficulty_multiplier))
    
    study_plan = {
        "topic": topic,
        "difficulty": difficulty,
        "total_lessons": lessons_needed,
        "lessons": [
            {"lesson": i+1, "focus": f"Module {i+1}: Core concepts", "duration_mins": 45}
            for i in range(lessons_needed)
        ],
        "quiz_schedule": [
            {"quiz": i+1, "after_lesson": (i+1) * (lessons_needed // 3)}
            for i in range(3)
        ],
        "revision_days": [lessons_needed - 3, lessons_needed - 1],
        "total_study_hours": round(lessons_needed * 0.75, 1)
    }
    
    return {"status": "success", "plan": study_plan}


# 💰 BUDGET PLANNER (Finance Domain)
def analyze_expenses(user_id: str, expenses: List[Dict]) -> Dict:
    """
    Analyze spending patterns and suggest budget adjustments.
    
    Args:
        expenses: List of {category, amount, date}
    
    Returns:
        Analysis with insights and recommendations
    """
    
    if not expenses:
        return {"status": "error", "message": "No expenses to analyze"}
    
    categories = {}
    total_spent = 0
    
    for expense in expenses:
        category = expense.get("category", "other")
        amount = expense.get("amount", 0)
        categories[category] = categories.get(category, 0) + amount
        total_spent += amount
    
    # Calculate percentages
    category_percentages = {k: round((v/total_spent)*100, 1) for k, v in categories.items()}
    
    # Detect overspending (over 50% in any category)
    overspending_alerts = [
        f"⚠️ {cat}: {pct}% of spending (consider setting a limit)"
        for cat, pct in category_percentages.items() if pct > 50
    ]
    
    analysis = {
        "status": "success",
        "total_spent": round(total_spent, 2),
        "by_category": {k: round(v, 2) for k, v in categories.items()},
        "percentages": category_percentages,
        "overspending_alerts": overspending_alerts if overspending_alerts else ["✅ Spending is well-distributed"],
        "suggested_budget": {
            k: round(v * 1.1, 2) if v <= (total_spent * 0.25) else round(v * 0.9, 2)
            for k, v in categories.items()
        }
    }
    
    return analysis


# 🏃 HABIT TRACKER (Wellness Domain)
def track_habit(user_id: str, habit: str, completed: bool, notes: str = "") -> Dict:
    """
    Track daily habits and detect streak patterns.
    
    Args:
        user_id: User identifier
        habit: Name of the habit
        completed: Whether completed today
        notes: Optional notes
    
    Returns:
        Habit record with streak info
    """
    
    habit_record = {
        "id": f"{user_id}_{habit}_{datetime.now().date()}",
        "user_id": user_id,
        "habit": habit,
        "date": datetime.now().isoformat(),
        "completed": completed,
        "notes": notes
    }
    
    try:
        progress_container = get_progress_container()
        progress_container.create_item(body=habit_record)
        
        # Calculate current streak
        query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.habit = @habit ORDER BY c.date DESC"
        records = list(progress_container.query_items(
            query=query,
            parameters=[
                {"name": "@user_id", "value": user_id},
                {"name": "@habit", "value": habit}
            ]
        ))
        
        streak = 0
        if records and records[0]["completed"]:
            for record in records:
                if record["completed"]:
                    streak += 1
                else:
                    break
        
        return {
            "status": "success",
            "record": habit_record,
            "current_streak": streak,
            "streak_message": f"🔥 {streak} day streak!" if streak > 0 else "⭐ Start your streak today!"
        }
    except Exception as e:
        print(f"Habit tracking error: {e}")
        return {"status": "error", "message": str(e)}


# 📋 GET ALL ACTIVE GOALS
def get_active_goals(user_id: str) -> Dict:
    """Retrieve all active goals for a user."""
    
    try:
        query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.status = 'active' ORDER BY c.created_at DESC"
        goals = list(get_goals_container().query_items(
            query=query,
            parameters=[{"name": "@user_id", "value": user_id}]
        ))
        
        return {"status": "success", "goals": goals, "count": len(goals)}
    except Exception as e:
        print(f"Goal retrieval error: {e}")
        return {"status": "error", "message": str(e)}
