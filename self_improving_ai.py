"""
Self-Improving AI System
- Web search for error solutions
- Performance tracking and analytics
- Learning from successes and failures
- Continuous improvement through reflection
"""

import asyncio
import aiohttp
import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

@dataclass
class PerformanceMetrics:
    """Track performance of AI operations"""
    operation_id: str
    operation_type: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    confidence_score: float = 0.0
    tokens_used: int = 0
    quality_score: float = 0.0
    user_feedback: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class LearningEntry:
    """Entry in the learning database"""
    entry_id: str
    timestamp: str
    category: str  # error_solution, optimization, pattern
    problem: str
    solution: str
    success_rate: float
    times_used: int
    effectiveness_score: float
    source: str  # web_search, user_feedback, self_discovery
    
    def to_dict(self):
        return asdict(self)

class SelfImprovingAI:
    """
    AI system that learns from experience and searches web for solutions
    """
    
    def __init__(self, openai_key: str, db_path: str = "ai_learning.db"):
        self.openai_key = openai_key
        self.db_path = db_path
        self.session = None
        
        # Initialize databases
        self._init_databases()
        
        # Performance tracking
        self.performance_history = []
        self.success_rate_cache = {}
        
        # Web search APIs
        self.search_engines = {
            "google": "https://www.googleapis.com/customsearch/v1",
            "duckduckgo": "https://api.duckduckgo.com/",
            "stackoverflow": "https://api.stackexchange.com/2.3/search"
        }
        
    def _init_databases(self):
        """Initialize SQLite databases for learning"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                operation_id TEXT PRIMARY KEY,
                operation_type TEXT,
                start_time REAL,
                end_time REAL,
                duration REAL,
                success INTEGER,
                error_message TEXT,
                confidence_score REAL,
                tokens_used INTEGER,
                quality_score REAL,
                user_feedback TEXT,
                timestamp TEXT
            )
        ''')
        
        # Learning entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_entries (
                entry_id TEXT PRIMARY KEY,
                timestamp TEXT,
                category TEXT,
                problem TEXT,
                solution TEXT,
                success_rate REAL,
                times_used INTEGER,
                effectiveness_score REAL,
                source TEXT
            )
        ''')
        
        # Error patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_patterns (
                pattern_id TEXT PRIMARY KEY,
                error_signature TEXT UNIQUE,
                error_type TEXT,
                solution_count INTEGER,
                best_solution TEXT,
                avg_fix_time REAL,
                last_seen TEXT
            )
        ''')
        
        # Optimization insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_insights (
                insight_id TEXT PRIMARY KEY,
                insight_type TEXT,
                description TEXT,
                impact_score REAL,
                implementation_count INTEGER,
                avg_improvement REAL,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def setup_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    # ===== WEB SEARCH FOR ERROR SOLUTIONS =====
    
    async def search_error_solution(
        self,
        error_message: str,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the internet for error solutions
        """
        await self.setup_session()
        
        # First, check local database for known solutions
        local_solutions = self._search_local_knowledge(error_message)
        
        if local_solutions:
            return local_solutions
        
        # Search multiple sources
        solutions = []
        
        # Search Stack Overflow
        stackoverflow_results = await self._search_stackoverflow(error_message)
        solutions.extend(stackoverflow_results)
        
        # Search GitHub Issues
        github_results = await self._search_github_issues(error_message, context)
        solutions.extend(github_results)
        
        # Search Unreal Engine forums
        if context and context.get("engine") == "unreal":
            unreal_results = await self._search_unreal_forums(error_message)
            solutions.extend(unreal_results)
        
        # Use AI to synthesize best solution
        best_solution = await self._synthesize_solutions(error_message, solutions)
        
        # Store in learning database
        self._store_learned_solution(error_message, best_solution, "web_search")
        
        return solutions
    
    async def _search_stackoverflow(self, query: str) -> List[Dict[str, Any]]:
        """Search Stack Overflow for solutions"""
        
        try:
            params = {
                "order": "desc",
                "sort": "votes",
                "intitle": query[:100],
                "site": "stackoverflow",
                "filter": "withbody"
            }
            
            async with self.session.get(
                self.search_engines["stackoverflow"],
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for item in data.get("items", [])[:5]:
                        results.append({
                            "source": "stackoverflow",
                            "title": item.get("title"),
                            "url": item.get("link"),
                            "score": item.get("score", 0),
                            "answer_count": item.get("answer_count", 0),
                            "is_answered": item.get("is_answered", False),
                            "tags": item.get("tags", [])
                        })
                    
                    return results
        except Exception as e:
            print(f"Stack Overflow search error: {e}")
        
        return []
    
    async def _search_github_issues(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search GitHub issues for similar problems"""
        
        # Construct search query
        search_terms = query[:100]
        if context and context.get("engine") == "unreal":
            search_terms += " UnrealEngine"
        
        try:
            async with self.session.get(
                "https://api.github.com/search/issues",
                params={
                    "q": f"{search_terms} is:issue is:closed",
                    "sort": "reactions",
                    "per_page": 5
                },
                headers={"Accept": "application/vnd.github.v3+json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for item in data.get("items", []):
                        results.append({
                            "source": "github",
                            "title": item.get("title"),
                            "url": item.get("html_url"),
                            "state": item.get("state"),
                            "comments": item.get("comments", 0),
                            "reactions": item.get("reactions", {}).get("total_count", 0)
                        })
                    
                    return results
        except Exception as e:
            print(f"GitHub search error: {e}")
        
        return []
    
    async def _search_unreal_forums(self, query: str) -> List[Dict[str, Any]]:
        """Search Unreal Engine forums"""
        
        # Use web scraping or API if available
        # For now, return placeholder
        return [{
            "source": "unreal_forums",
            "title": "Check Unreal Engine forums manually",
            "url": f"https://forums.unrealengine.com/search?q={query.replace(' ', '+')}",
            "note": "Manual search recommended"
        }]
    
    async def _synthesize_solutions(
        self,
        error_message: str,
        solutions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use AI to synthesize best solution from multiple sources"""
        
        prompt = f"""Analyze these solutions for the error and provide the best approach:

ERROR: {error_message}

SOLUTIONS FOUND:
{json.dumps(solutions, indent=2)}

Provide a synthesized solution in JSON format:
{{
    "recommended_solution": "step by step fix",
    "confidence": 0.0-1.0,
    "reasoning": "why this is the best approach",
    "alternative_solutions": ["alt 1", "alt 2"],
    "estimated_fix_time": "time in minutes"
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
                        {"role": "system", "content": "You are an expert at analyzing error solutions."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return json.loads(result["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Solution synthesis error: {e}")
        
        return {
            "recommended_solution": "Manual review required",
            "confidence": 0.3,
            "reasoning": "Unable to synthesize solutions",
            "alternative_solutions": [],
            "estimated_fix_time": "unknown"
        }
    
    def _search_local_knowledge(self, error_message: str) -> List[Dict[str, Any]]:
        """Search local learning database for known solutions"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search error patterns
        cursor.execute(
            "SELECT * FROM error_patterns WHERE error_signature LIKE ? ORDER BY avg_fix_time ASC LIMIT 5",
            (f"%{error_message[:50]}%",)
        )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "source": "local_knowledge",
                "error_type": row[2],
                "best_solution": row[4],
                "avg_fix_time": row[5],
                "confidence": 0.9  # High confidence for known patterns
            })
        
        conn.close()
        return results
    
    # ===== PERFORMANCE TRACKING =====
    
    def start_operation(
        self,
        operation_type: str
    ) -> str:
        """Start tracking an operation"""
        
        operation_id = self._generate_id(operation_type)
        start_time = time.time()
        
        # Store in memory
        self.performance_history.append({
            "operation_id": operation_id,
            "operation_type": operation_type,
            "start_time": start_time
        })
        
        return operation_id
    
    def end_operation(
        self,
        operation_id: str,
        success: bool,
        error_message: Optional[str] = None,
        confidence_score: float = 0.0,
        quality_score: float = 0.0,
        tokens_used: int = 0
    ):
        """End tracking an operation and store metrics"""
        
        end_time = time.time()
        
        # Find operation in history
        operation = next((op for op in self.performance_history if op["operation_id"] == operation_id), None)
        
        if not operation:
            return
        
        duration = end_time - operation["start_time"]
        
        metrics = PerformanceMetrics(
            operation_id=operation_id,
            operation_type=operation["operation_type"],
            start_time=operation["start_time"],
            end_time=end_time,
            duration=duration,
            success=success,
            error_message=error_message,
            confidence_score=confidence_score,
            quality_score=quality_score,
            tokens_used=tokens_used
        )
        
        # Store in database
        self._store_metrics(metrics)
        
        # Analyze and learn
        self._analyze_performance(metrics)
    
    def _store_metrics(self, metrics: PerformanceMetrics):
        """Store metrics in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.operation_id,
            metrics.operation_type,
            metrics.start_time,
            metrics.end_time,
            metrics.duration,
            1 if metrics.success else 0,
            metrics.error_message,
            metrics.confidence_score,
            metrics.tokens_used,
            metrics.quality_score,
            metrics.user_feedback,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _analyze_performance(self, metrics: PerformanceMetrics):
        """Analyze performance and identify improvements"""
        
        # Calculate success rate for operation type
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(success) as successes,
                AVG(duration) as avg_duration,
                AVG(quality_score) as avg_quality
            FROM performance_metrics
            WHERE operation_type = ?
        ''', (metrics.operation_type,))
        
        row = cursor.fetchone()
        total, successes, avg_duration, avg_quality = row
        
        success_rate = successes / total if total > 0 else 0
        
        # Store in cache
        self.success_rate_cache[metrics.operation_type] = {
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "avg_quality": avg_quality,
            "total_operations": total
        }
        
        # Identify if performance is degrading
        if success_rate < 0.7:
            self._create_improvement_insight(
                f"Low success rate for {metrics.operation_type}",
                success_rate
            )
        
        if avg_duration > 30:  # More than 30 seconds
            self._create_improvement_insight(
                f"Slow performance for {metrics.operation_type}",
                avg_duration
            )
        
        conn.close()
    
    # ===== LEARNING & IMPROVEMENT =====
    
    def _store_learned_solution(
        self,
        problem: str,
        solution: Dict[str, Any],
        source: str
    ):
        """Store learned solution in database"""
        
        entry_id = self._generate_id(problem)
        
        learning_entry = LearningEntry(
            entry_id=entry_id,
            timestamp=datetime.now().isoformat(),
            category="error_solution",
            problem=problem,
            solution=json.dumps(solution),
            success_rate=solution.get("confidence", 0.5),
            times_used=0,
            effectiveness_score=0.0,
            source=source
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO learning_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            learning_entry.entry_id,
            learning_entry.timestamp,
            learning_entry.category,
            learning_entry.problem,
            learning_entry.solution,
            learning_entry.success_rate,
            learning_entry.times_used,
            learning_entry.effectiveness_score,
            learning_entry.source
        ))
        
        conn.commit()
        conn.close()
    
    def record_solution_success(self, problem: str, worked: bool):
        """Record whether a solution worked"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT entry_id, times_used, effectiveness_score FROM learning_entries WHERE problem LIKE ?",
            (f"%{problem[:50]}%",)
        )
        
        row = cursor.fetchone()
        if row:
            entry_id, times_used, effectiveness_score = row
            
            # Update effectiveness
            new_times_used = times_used + 1
            if worked:
                new_effectiveness = (effectiveness_score * times_used + 1.0) / new_times_used
            else:
                new_effectiveness = (effectiveness_score * times_used + 0.0) / new_times_used
            
            cursor.execute('''
                UPDATE learning_entries 
                SET times_used = ?, effectiveness_score = ?
                WHERE entry_id = ?
            ''', (new_times_used, new_effectiveness, entry_id))
            
            conn.commit()
        
        conn.close()
    
    def _create_improvement_insight(self, description: str, impact_score: float):
        """Create an improvement insight"""
        
        insight_id = self._generate_id(description)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO optimization_insights VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            insight_id,
            "performance",
            description,
            impact_score,
            0,
            0.0,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    async def reflect_and_improve(self) -> Dict[str, Any]:
        """
        Reflect on recent performance and identify improvements
        """
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent performance data
        cursor.execute('''
            SELECT operation_type, AVG(duration), AVG(quality_score), AVG(success)
            FROM performance_metrics
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY operation_type
        ''')
        
        performance_data = []
        for row in cursor.fetchall():
            performance_data.append({
                "operation_type": row[0],
                "avg_duration": row[1],
                "avg_quality": row[2],
                "success_rate": row[3]
            })
        
        # Get learning effectiveness
        cursor.execute('''
            SELECT category, AVG(effectiveness_score), COUNT(*)
            FROM learning_entries
            WHERE times_used > 0
            GROUP BY category
        ''')
        
        learning_data = []
        for row in cursor.fetchall():
            learning_data.append({
                "category": row[0],
                "avg_effectiveness": row[1],
                "entries": row[2]
            })
        
        conn.close()
        
        # Use AI to analyze and suggest improvements
        reflection_prompt = f"""Analyze this AI system's performance and suggest improvements:

PERFORMANCE DATA:
{json.dumps(performance_data, indent=2)}

LEARNING DATA:
{json.dumps(learning_data, indent=2)}

Provide analysis in JSON format:
{{
    "overall_health": "excellent|good|fair|poor",
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "improvement_priorities": [
        {{
            "area": "specific area",
            "current_metric": 0.0,
            "target_metric": 0.0,
            "recommended_action": "what to do"
        }}
    ],
    "learning_effectiveness": "high|medium|low",
    "recommendations": ["rec 1", "rec 2"]
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
                        {"role": "system", "content": "You are an AI performance analyst."},
                        {"role": "user", "content": reflection_prompt}
                    ],
                    "temperature": 0.4,
                    "response_format": {"type": "json_object"}
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    reflection = json.loads(result["choices"][0]["message"]["content"])
                    
                    # Store insights
                    for priority in reflection.get("improvement_priorities", []):
                        self._create_improvement_insight(
                            priority.get("recommended_action", ""),
                            priority.get("current_metric", 0.0)
                        )
                    
                    return reflection
        except Exception as e:
            print(f"Reflection error: {e}")
        
        return {
            "overall_health": "unknown",
            "message": "Unable to perform reflection"
        }
    
    # ===== ANALYTICS & REPORTING =====
    
    def get_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate performance report"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT 
                operation_type,
                COUNT(*) as total,
                SUM(success) as successes,
                AVG(duration) as avg_duration,
                AVG(quality_score) as avg_quality,
                AVG(confidence_score) as avg_confidence
            FROM performance_metrics
            WHERE timestamp > datetime('now', '-{days} days')
            GROUP BY operation_type
        ''')
        
        report = {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "operations": []
        }
        
        for row in cursor.fetchall():
            op_type, total, successes, avg_dur, avg_qual, avg_conf = row
            
            report["operations"].append({
                "type": op_type,
                "total_count": total,
                "success_count": successes,
                "success_rate": successes / total if total > 0 else 0,
                "avg_duration_sec": avg_dur,
                "avg_quality": avg_qual,
                "avg_confidence": avg_conf
            })
        
        # Get learning stats
        cursor.execute('''
            SELECT COUNT(*), AVG(effectiveness_score)
            FROM learning_entries
            WHERE times_used > 0
        ''')
        
        row = cursor.fetchone()
        report["learning_stats"] = {
            "active_entries": row[0],
            "avg_effectiveness": row[1]
        }
        
        conn.close()
        return report
    
    def get_top_solutions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most effective solutions"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT problem, solution, effectiveness_score, times_used, source
            FROM learning_entries
            WHERE times_used > 0
            ORDER BY effectiveness_score DESC, times_used DESC
            LIMIT ?
        ''', (limit,))
        
        solutions = []
        for row in cursor.fetchall():
            solutions.append({
                "problem": row[0],
                "solution": json.loads(row[1]) if row[1].startswith('{') else row[1],
                "effectiveness": row[2],
                "times_used": row[3],
                "source": row[4]
            })
        
        conn.close()
        return solutions
    
    # ===== HELPER METHODS =====
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID"""
        timestamp = str(time.time())
        return hashlib.md5(f"{text}{timestamp}".encode()).hexdigest()[:12]
