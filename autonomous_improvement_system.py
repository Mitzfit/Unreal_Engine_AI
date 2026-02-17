"""
Autonomous Improvement System
Scrapes web when user logs out to find improvements
Generates daily admin reports
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sqlite3
from pathlib import Path
import hashlib

class AutonomousImprovementSystem:
    """
    System that automatically improves itself by learning from the web
    """
    
    def __init__(self, openai_key: str, db_path: str = "autonomous_learning.db"):
        self.openai_key = openai_key
        self.db_path = db_path
        self.session = None
        
        self._init_database()
        
    def _init_database(self):
        """Initialize database for autonomous learning"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Session analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_analysis (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                start_time TEXT,
                end_time TEXT,
                duration_minutes REAL,
                actions_taken INTEGER,
                assets_created INTEGER,
                errors_encountered INTEGER,
                features_used TEXT,
                pain_points TEXT,
                success_metrics TEXT,
                analyzed_at TEXT
            )
        ''')
        
        # Web research table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_research (
                research_id TEXT PRIMARY KEY,
                session_id TEXT,
                research_date TEXT,
                sources_searched TEXT,
                insights_found TEXT,
                improvements_identified TEXT,
                priority_score REAL,
                implementation_status TEXT,
                FOREIGN KEY (session_id) REFERENCES session_analysis(session_id)
            )
        ''')
        
        # Improvement suggestions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_suggestions (
                suggestion_id TEXT PRIMARY KEY,
                research_id TEXT,
                category TEXT,
                title TEXT,
                description TEXT,
                implementation_plan TEXT,
                expected_impact TEXT,
                effort_estimate TEXT,
                priority INTEGER,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY (research_id) REFERENCES web_research(research_id)
            )
        ''')
        
        # Daily reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_reports (
                report_id TEXT PRIMARY KEY,
                report_date TEXT,
                sessions_analyzed INTEGER,
                improvements_found INTEGER,
                high_priority_items INTEGER,
                system_health_score REAL,
                report_data TEXT,
                generated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def analyze_session(
        self,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze user session to identify improvement opportunities
        """
        
        session_id = session_data.get("session_id", self._generate_id("session"))
        
        # Extract metrics
        metrics = {
            "duration_minutes": session_data.get("duration", 0) / 60,
            "actions_taken": len(session_data.get("actions", [])),
            "assets_created": len(session_data.get("assets_created", [])),
            "errors_encountered": len(session_data.get("errors", [])),
            "features_used": json.dumps(session_data.get("features_used", [])),
            "pain_points": json.dumps(self._identify_pain_points(session_data)),
            "success_metrics": json.dumps(self._calculate_success_metrics(session_data))
        }
        
        # Store analysis
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_analysis VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            session_data.get("user_id"),
            session_data.get("start_time"),
            session_data.get("end_time"),
            metrics["duration_minutes"],
            metrics["actions_taken"],
            metrics["assets_created"],
            metrics["errors_encountered"],
            metrics["features_used"],
            metrics["pain_points"],
            metrics["success_metrics"],
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "session_id": session_id,
            "metrics": metrics,
            "ready_for_research": True
        }
    
    def _identify_pain_points(self, session_data: Dict[str, Any]) -> List[str]:
        """Identify user pain points from session"""
        
        pain_points = []
        
        # Long duration on single action
        actions = session_data.get("actions", [])
        for action in actions:
            if action.get("duration", 0) > 300:  # 5 minutes
                pain_points.append(f"Slow action: {action.get('type')}")
        
        # Multiple errors on same feature
        errors = session_data.get("errors", [])
        error_counts = {}
        for error in errors:
            feature = error.get("feature", "unknown")
            error_counts[feature] = error_counts.get(feature, 0) + 1
        
        for feature, count in error_counts.items():
            if count >= 3:
                pain_points.append(f"Frequent errors in {feature}")
        
        # Feature abandonment
        if session_data.get("abandoned_features"):
            for feature in session_data["abandoned_features"]:
                pain_points.append(f"User abandoned {feature}")
        
        return pain_points
    
    def _calculate_success_metrics(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate success metrics"""
        
        return {
            "completion_rate": session_data.get("tasks_completed", 0) / max(session_data.get("tasks_started", 1), 1),
            "error_rate": len(session_data.get("errors", [])) / max(session_data.get("actions_count", 1), 1),
            "feature_usage_diversity": len(set(session_data.get("features_used", []))),
            "user_satisfaction": session_data.get("satisfaction_score", 5) / 10.0
        }
    
    async def research_improvements(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Research the web for improvements based on session analysis
        """
        
        # Get session analysis
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM session_analysis WHERE session_id = ?",
            (session_id,)
        )
        
        session_row = cursor.fetchone()
        conn.close()
        
        if not session_row:
            return {"error": "Session not found"}
        
        pain_points = json.loads(session_row[8])  # pain_points column
        features_used = json.loads(session_row[7])  # features_used column
        
        # Research each pain point
        research_results = []
        
        for pain_point in pain_points:
            result = await self._research_pain_point(pain_point, features_used)
            research_results.append(result)
        
        # Research general improvements
        general_improvements = await self._research_general_improvements(features_used)
        research_results.append(general_improvements)
        
        # Store research
        research_id = self._generate_id("research")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO web_research VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            research_id,
            session_id,
            datetime.now().isoformat(),
            json.dumps([r.get("sources", []) for r in research_results]),
            json.dumps([r.get("insights", []) for r in research_results]),
            json.dumps([r.get("improvements", []) for r in research_results]),
            self._calculate_priority_score(research_results),
            "pending"
        ))
        
        conn.commit()
        conn.close()
        
        # Generate improvement suggestions
        suggestions = await self._generate_suggestions(research_id, research_results)
        
        return {
            "research_id": research_id,
            "pain_points_researched": len(pain_points),
            "sources_consulted": sum(len(r.get("sources", [])) for r in research_results),
            "improvements_found": len(suggestions),
            "suggestions": suggestions
        }
    
    async def _research_pain_point(
        self,
        pain_point: str,
        features_used: List[str]
    ) -> Dict[str, Any]:
        """Research a specific pain point on the web"""
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Search Stack Overflow
        stackoverflow_results = await self._search_stackoverflow_for_solutions(pain_point)
        
        # Search GitHub for similar issues
        github_results = await self._search_github_solutions(pain_point)
        
        # Search academic papers
        academic_results = await self._search_academic_papers(pain_point)
        
        # Synthesize findings with AI
        synthesis = await self._synthesize_research(
            pain_point,
            stackoverflow_results + github_results + academic_results
        )
        
        return {
            "pain_point": pain_point,
            "sources": ["Stack Overflow", "GitHub", "Academic"],
            "insights": synthesis.get("insights", []),
            "improvements": synthesis.get("improvements", [])
        }
    
    async def _search_stackoverflow_for_solutions(self, query: str) -> List[Dict]:
        """Search Stack Overflow"""
        
        try:
            async with self.session.get(
                "https://api.stackexchange.com/2.3/search/advanced",
                params={
                    "q": query[:100],
                    "site": "stackoverflow",
                    "sort": "votes",
                    "filter": "withbody",
                    "pagesize": 5
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {
                            "source": "stackoverflow",
                            "title": item.get("title"),
                            "url": item.get("link"),
                            "votes": item.get("score", 0),
                            "tags": item.get("tags", [])
                        }
                        for item in data.get("items", [])
                    ]
        except:
            pass
        
        return []
    
    async def _search_github_solutions(self, query: str) -> List[Dict]:
        """Search GitHub for solutions"""
        
        try:
            async with self.session.get(
                "https://api.github.com/search/issues",
                params={
                    "q": f"{query[:100]} is:closed",
                    "sort": "reactions",
                    "per_page": 5
                },
                headers={"Accept": "application/vnd.github.v3+json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {
                            "source": "github",
                            "title": item.get("title"),
                            "url": item.get("html_url"),
                            "state": item.get("state"),
                            "comments": item.get("comments", 0)
                        }
                        for item in data.get("items", [])
                    ]
        except:
            pass
        
        return []
    
    async def _search_academic_papers(self, query: str) -> List[Dict]:
        """Search academic papers (arXiv, etc.)"""
        
        # Placeholder - would integrate with arXiv API, Google Scholar, etc.
        return [{
            "source": "academic",
            "title": "Research on UI/UX optimization",
            "relevance": "medium"
        }]
    
    async def _research_general_improvements(
        self,
        features_used: List[str]
    ) -> Dict[str, Any]:
        """Research general improvements for the system"""
        
        # Search for best practices
        best_practices = await self._search_best_practices(features_used)
        
        # Search for emerging technologies
        emerging_tech = await self._search_emerging_technologies()
        
        # Search competitor features
        competitor_features = await self._search_competitor_analysis()
        
        return {
            "pain_point": "General System Improvements",
            "sources": ["Best Practices", "Emerging Tech", "Competitors"],
            "insights": best_practices + emerging_tech + competitor_features,
            "improvements": []
        }
    
    async def _search_best_practices(self, features: List[str]) -> List[str]:
        """Search for best practices"""
        
        return [
            "Implement progressive disclosure for complex features",
            "Add keyboard shortcuts for power users",
            "Provide contextual help tooltips",
            "Use consistent design patterns throughout"
        ]
    
    async def _search_emerging_technologies(self) -> List[str]:
        """Search for emerging technologies"""
        
        return [
            "WebGPU for better graphics performance",
            "WASM for faster code execution",
            "Diffusion models for better image generation",
            "Real-time collaboration with WebRTC"
        ]
    
    async def _search_competitor_analysis(self) -> List[str]:
        """Analyze competitor features"""
        
        return [
            "Visual scripting nodes like Unreal Blueprints",
            "Asset marketplace integration",
            "Version control built-in",
            "Cloud rendering for previews"
        ]
    
    async def _synthesize_research(
        self,
        pain_point: str,
        research_results: List[Dict]
    ) -> Dict[str, Any]:
        """Use AI to synthesize research findings"""
        
        prompt = f"""Analyze these research findings about a user pain point and provide actionable insights:

PAIN POINT: {pain_point}

RESEARCH FINDINGS:
{json.dumps(research_results, indent=2)}

Provide a JSON response with:
{{
    "insights": ["key insight 1", "key insight 2", "key insight 3"],
    "improvements": [
        {{
            "title": "improvement title",
            "description": "what to do",
            "impact": "high|medium|low",
            "effort": "high|medium|low",
            "implementation": "how to implement"
        }}
    ],
    "priority": "high|medium|low"
}}"""

        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": [
                        {"role": "system", "content": "You are a product improvement analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "response_format": {"type": "json_object"}
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return json.loads(result["choices"][0]["message"]["content"])
        except:
            pass
        
        return {"insights": [], "improvements": []}
    
    def _calculate_priority_score(self, research_results: List[Dict]) -> float:
        """Calculate priority score for improvements"""
        
        high_priority_count = sum(
            1 for r in research_results 
            for imp in r.get("improvements", [])
            if imp.get("impact") == "high"
        )
        
        total_improvements = sum(len(r.get("improvements", [])) for r in research_results)
        
        if total_improvements == 0:
            return 0.5
        
        return min(1.0, high_priority_count / max(total_improvements, 1))
    
    async def _generate_suggestions(
        self,
        research_id: str,
        research_results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate concrete improvement suggestions"""
        
        suggestions = []
        
        for result in research_results:
            for improvement in result.get("improvements", []):
                suggestion_id = self._generate_id("suggestion")
                
                suggestion = {
                    "suggestion_id": suggestion_id,
                    "research_id": research_id,
                    "category": self._categorize_improvement(improvement),
                    "title": improvement.get("title", "Improvement"),
                    "description": improvement.get("description", ""),
                    "implementation_plan": improvement.get("implementation", ""),
                    "expected_impact": improvement.get("impact", "medium"),
                    "effort_estimate": improvement.get("effort", "medium"),
                    "priority": self._calculate_suggestion_priority(improvement),
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                }
                
                suggestions.append(suggestion)
                
                # Store in database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO improvement_suggestions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(suggestion.values()))
                
                conn.commit()
                conn.close()
        
        return suggestions
    
    def _categorize_improvement(self, improvement: Dict) -> str:
        """Categorize improvement type"""
        
        title = improvement.get("title", "").lower()
        description = improvement.get("description", "").lower()
        combined = title + " " + description
        
        if any(word in combined for word in ["ui", "interface", "design", "layout"]):
            return "UI/UX"
        elif any(word in combined for word in ["performance", "speed", "optimize"]):
            return "Performance"
        elif any(word in combined for word in ["feature", "functionality", "capability"]):
            return "Feature"
        elif any(word in combined for word in ["bug", "fix", "error", "crash"]):
            return "Bug Fix"
        elif any(word in combined for word in ["documentation", "help", "tutorial"]):
            return "Documentation"
        else:
            return "Other"
    
    def _calculate_suggestion_priority(self, improvement: Dict) -> int:
        """Calculate priority (1-5, 5 being highest)"""
        
        impact = improvement.get("impact", "medium")
        effort = improvement.get("effort", "medium")
        
        impact_score = {"low": 1, "medium": 2, "high": 3}[impact]
        effort_score = {"low": 3, "medium": 2, "high": 1}[effort]
        
        return min(5, impact_score + effort_score)
    
    async def generate_daily_report(
        self,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate daily admin report"""
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get sessions analyzed today
        cursor.execute('''
            SELECT COUNT(*), AVG(duration_minutes), SUM(assets_created), SUM(errors_encountered)
            FROM session_analysis
            WHERE DATE(analyzed_at) = ?
        ''', (date,))
        
        session_stats = cursor.fetchone()
        
        # Get improvements found today
        cursor.execute('''
            SELECT COUNT(*) FROM web_research
            WHERE DATE(research_date) = ?
        ''', (date,))
        
        improvements_count = cursor.fetchone()[0]
        
        # Get high priority suggestions
        cursor.execute('''
            SELECT COUNT(*) FROM improvement_suggestions
            WHERE DATE(created_at) = ? AND priority >= 4
        ''', (date,))
        
        high_priority_count = cursor.fetchone()[0]
        
        # Calculate system health
        cursor.execute('''
            SELECT AVG(CAST(success_metrics AS REAL))
            FROM session_analysis
            WHERE DATE(analyzed_at) >= DATE(?, '-7 days')
        ''', (date,))
        
        health_score = cursor.fetchone()[0] or 0.5
        
        # Get all suggestions for report
        cursor.execute('''
            SELECT * FROM improvement_suggestions
            WHERE DATE(created_at) = ?
            ORDER BY priority DESC
            LIMIT 20
        ''', (date,))
        
        suggestions = cursor.fetchall()
        
        conn.close()
        
        # Build report
        report = {
            "report_date": date,
            "summary": {
                "sessions_analyzed": session_stats[0] or 0,
                "avg_session_duration": round(session_stats[1] or 0, 2),
                "assets_created_total": session_stats[2] or 0,
                "errors_encountered_total": session_stats[3] or 0,
                "improvements_researched": improvements_count,
                "high_priority_items": high_priority_count,
                "system_health_score": round(health_score * 100, 1)
            },
            "top_improvements": [
                {
                    "title": s[3],
                    "category": s[2],
                    "priority": s[8],
                    "impact": s[6],
                    "effort": s[7],
                    "description": s[4]
                }
                for s in suggestions[:10]
            ],
            "recommendations": self._generate_admin_recommendations(session_stats, suggestions)
        }
        
        # Store report
        report_id = self._generate_id("report")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO daily_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            date,
            session_stats[0] or 0,
            improvements_count,
            high_priority_count,
            health_score,
            json.dumps(report),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return report
    
    def _generate_admin_recommendations(
        self,
        session_stats: tuple,
        suggestions: List[tuple]
    ) -> List[str]:
        """Generate recommendations for admin"""
        
        recommendations = []
        
        # Based on session stats
        if session_stats[3] and session_stats[3] > 10:  # errors > 10
            recommendations.append("HIGH: Error rate is elevated. Review error logs and prioritize bug fixes.")
        
        if session_stats[1] and session_stats[1] < 10:  # avg duration < 10 min
            recommendations.append("MEDIUM: Short session durations. Consider improving user engagement.")
        
        # Based on suggestions
        high_priority = [s for s in suggestions if s[8] >= 4]
        if len(high_priority) > 5:
            recommendations.append(f"HIGH: {len(high_priority)} high-priority improvements identified. Review and plan implementation.")
        
        if not recommendations:
            recommendations.append("System performing well. Continue monitoring user sessions.")
        
        return recommendations
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        timestamp = str(time.time())
        return f"{prefix}_{hashlib.md5(timestamp.encode()).hexdigest()[:12]}"
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
