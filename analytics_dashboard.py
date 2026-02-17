"""
╔══════════════════════════════════════════════════════════════╗
║        ANALYTICS DASHBOARD  ·  analytics_dashboard.py        ║
║  Player Tracking · Heatmaps · Funnels · AI Insights · Charts ║
╚══════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import asyncio, csv, json, math, random, sqlite3, uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════ ENUMS ══════════════════════════════
class EventType(Enum):
    # Session
    SESSION_START   = "session_start"
    SESSION_END     = "session_end"
    LEVEL_START     = "level_start"
    LEVEL_COMPLETE  = "level_complete"
    LEVEL_FAIL      = "level_fail"
    CHECKPOINT      = "checkpoint"
    # Player actions
    KILL            = "kill"
    DEATH           = "death"
    DAMAGE_DEALT    = "damage_dealt"
    DAMAGE_TAKEN    = "damage_taken"
    ITEM_COLLECTED  = "item_collected"
    ITEM_USED       = "item_used"
    ITEM_PURCHASED  = "item_purchased"
    QUEST_STARTED   = "quest_started"
    QUEST_COMPLETED = "quest_completed"
    QUEST_ABANDONED = "quest_abandoned"
    DIALOGUE_CHOICE = "dialogue_choice"
    ABILITY_USED    = "ability_used"
    # Economy
    CURRENCY_EARNED = "currency_earned"
    CURRENCY_SPENT  = "currency_spent"
    IAP_PURCHASE    = "iap_purchase"
    # Meta
    TUTORIAL_STEP   = "tutorial_step"
    ACHIEVEMENT     = "achievement"
    SETTING_CHANGED = "setting_changed"
    ERROR           = "error"
    CUSTOM          = "custom"

class MetricPeriod(Enum):
    HOURLY  = "hourly"
    DAILY   = "daily"
    WEEKLY  = "weekly"
    MONTHLY = "monthly"
    ALL_TIME= "all_time"


# ════════════════════════ DATA CLASSES ══════════════════════════
@dataclass
class GameEvent:
    event_id:   str
    player_id:  str
    event_type: EventType
    timestamp:  str
    session_id: str        = ""
    level_id:   str        = ""
    x: float               = 0.0
    y: float               = 0.0
    z: float               = 0.0
    value:      float      = 0.0
    metadata:   Dict       = field(default_factory=dict)

    def to_tuple(self) -> tuple:
        return (self.event_id, self.player_id, self.event_type.value,
                self.timestamp, self.session_id, self.level_id,
                self.x, self.y, self.z, self.value,
                json.dumps(self.metadata))


@dataclass
class PlayerSession:
    session_id:    str
    player_id:     str
    started_at:    str
    ended_at:      Optional[str] = None
    duration_secs: float         = 0.0
    level_id:      str           = ""
    events_count:  int           = 0
    kills:         int           = 0
    deaths:        int           = 0
    xp_earned:     float         = 0.0
    currency_earned:float        = 0.0
    currency_spent: float        = 0.0
    platform:      str           = "pc"
    version:       str           = "1.0.0"
    country:       str           = ""

    def to_tuple(self) -> tuple:
        return (self.session_id, self.player_id, self.started_at, self.ended_at,
                self.duration_secs, self.level_id, self.events_count,
                self.kills, self.deaths, self.xp_earned,
                self.currency_earned, self.currency_spent,
                self.platform, self.version, self.country)


@dataclass
class HeatmapPoint:
    x:         float
    y:         float
    z:         float
    intensity: float = 1.0
    label:     str   = ""


@dataclass
class FunnelStep:
    step_name:    str
    event_type:   EventType
    count:        int   = 0
    drop_off_pct: float = 0.0
    avg_time_secs:float = 0.0


@dataclass
class ABTest:
    test_id:    str
    name:       str
    variant_a:  str
    variant_b:  str
    metric:     str          # what we're measuring
    started_at: str
    ended_at:   Optional[str]= None
    results_a:  Dict         = field(default_factory=dict)
    results_b:  Dict         = field(default_factory=dict)

    def winner(self) -> Optional[str]:
        a = self.results_a.get("metric_value", 0)
        b = self.results_b.get("metric_value", 0)
        if abs(a - b) < 0.01: return None
        return "A" if a > b else "B"


# ═══════════════════════ EVENT TRACKER ══════════════════════════
class EventTracker:
    """Ingests raw events from the game and writes to SQLite."""

    def __init__(self, db_path: str = "analytics.db"):
        self.db = db_path
        self._init_db()
        self._buffer: List[GameEvent] = []
        self._flush_every = 50   # auto-flush every N events

    def _init_db(self):
        c = sqlite3.connect(self.db)
        c.executescript("""
        CREATE TABLE IF NOT EXISTS events(
            event_id TEXT PRIMARY KEY, player_id TEXT, event_type TEXT,
            timestamp TEXT, session_id TEXT, level_id TEXT,
            x REAL, y REAL, z REAL, value REAL, metadata TEXT);
        CREATE TABLE IF NOT EXISTS sessions(
            session_id TEXT PRIMARY KEY, player_id TEXT,
            started_at TEXT, ended_at TEXT, duration_secs REAL,
            level_id TEXT, events_count INT, kills INT, deaths INT,
            xp_earned REAL, currency_earned REAL, currency_spent REAL,
            platform TEXT, version TEXT, country TEXT);
        CREATE TABLE IF NOT EXISTS players(
            player_id TEXT PRIMARY KEY, first_seen TEXT, last_seen TEXT,
            total_sessions INT DEFAULT 0, total_playtime_secs REAL DEFAULT 0,
            total_kills INT DEFAULT 0, total_deaths INT DEFAULT 0,
            total_xp REAL DEFAULT 0, level INT DEFAULT 1,
            platform TEXT, country TEXT, version TEXT);
        CREATE TABLE IF NOT EXISTS ab_tests(
            test_id TEXT PRIMARY KEY, name TEXT, variant_a TEXT,
            variant_b TEXT, metric TEXT, started_at TEXT, ended_at TEXT,
            results TEXT);
        CREATE INDEX IF NOT EXISTS idx_events_player   ON events(player_id);
        CREATE INDEX IF NOT EXISTS idx_events_type     ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_level    ON events(level_id);
        CREATE INDEX IF NOT EXISTS idx_events_ts       ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_sessions_player ON sessions(player_id);
        """)
        c.commit(); c.close()

    # ── Track ─────────────────────────────────────
    def track(self, player_id: str, event_type: EventType,
              session_id: str = "", level_id: str = "",
              x: float = 0, y: float = 0, z: float = 0,
              value: float = 0, **metadata) -> GameEvent:
        ev = GameEvent(
            event_id   = str(uuid.uuid4()),
            player_id  = player_id,
            event_type = event_type,
            timestamp  = datetime.utcnow().isoformat(),
            session_id = session_id,
            level_id   = level_id,
            x=x, y=y, z=z, value=value,
            metadata   = metadata,
        )
        self._buffer.append(ev)
        if len(self._buffer) >= self._flush_every:
            self.flush()
        return ev

    def flush(self):
        if not self._buffer: return
        c = sqlite3.connect(self.db)
        c.executemany(
            "INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            [e.to_tuple() for e in self._buffer])
        c.commit(); c.close()
        self._buffer.clear()

    def start_session(self, player_id: str, level_id: str = "",
                      platform: str = "pc", version: str = "1.0", country: str = "") -> str:
        sid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        sess = PlayerSession(sid, player_id, now, level_id=level_id,
                             platform=platform, version=version, country=country)
        c = sqlite3.connect(self.db)
        c.execute("INSERT OR IGNORE INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  sess.to_tuple())
        # upsert player
        c.execute("""
            INSERT INTO players(player_id,first_seen,last_seen,platform,country,version)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(player_id) DO UPDATE SET last_seen=excluded.last_seen""",
            (player_id, now, now, platform, country, version))
        c.commit(); c.close()
        self.track(player_id, EventType.SESSION_START, session_id=sid, level_id=level_id)
        return sid

    def end_session(self, session_id: str, player_id: str,
                    duration_secs: float = 0, kills: int = 0, deaths: int = 0,
                    xp: float = 0, currency_earned: float = 0, currency_spent: float = 0):
        now = datetime.utcnow().isoformat()
        c = sqlite3.connect(self.db)
        c.execute("""UPDATE sessions SET ended_at=?,duration_secs=?,kills=?,deaths=?,
                     xp_earned=?,currency_earned=?,currency_spent=? WHERE session_id=?""",
                  (now, duration_secs, kills, deaths, xp,
                   currency_earned, currency_spent, session_id))
        c.execute("""UPDATE players SET last_seen=?,total_sessions=total_sessions+1,
                     total_playtime_secs=total_playtime_secs+?,
                     total_kills=total_kills+?,total_deaths=total_deaths+?,
                     total_xp=total_xp+? WHERE player_id=?""",
                  (now, duration_secs, kills, deaths, xp, player_id))
        c.commit(); c.close()
        self.track(player_id, EventType.SESSION_END, session_id=session_id, value=duration_secs)


# ═══════════════════════ ANALYTICS ENGINE ═══════════════════════
class AnalyticsEngine:
    """Queries the event database and computes KPIs, heatmaps, funnels."""

    def __init__(self, db_path: str = "analytics.db"):
        self.db = db_path

    def _q(self, sql: str, params: tuple = ()) -> List[Dict]:
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        rows = c.execute(sql, params).fetchall()
        c.close()
        return [dict(r) for r in rows]

    def _scalar(self, sql: str, params: tuple = (), default: Any = 0) -> Any:
        rows = self._q(sql, params)
        if rows:
            v = list(rows[0].values())[0]
            return v if v is not None else default
        return default

    # ── Core KPIs ────────────────────────────────
    def dau(self, date: str = None) -> int:
        d = date or datetime.utcnow().strftime("%Y-%m-%d")
        return self._scalar(
            "SELECT COUNT(DISTINCT player_id) FROM sessions WHERE started_at LIKE ?",
            (f"{d}%",))

    def mau(self, year_month: str = None) -> int:
        ym = year_month or datetime.utcnow().strftime("%Y-%m")
        return self._scalar(
            "SELECT COUNT(DISTINCT player_id) FROM sessions WHERE started_at LIKE ?",
            (f"{ym}%",))

    def total_players(self) -> int:
        return self._scalar("SELECT COUNT(*) FROM players")

    def total_sessions(self) -> int:
        return self._scalar("SELECT COUNT(*) FROM sessions")

    def avg_session_duration(self, days: int = 7) -> float:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        v = self._scalar(
            "SELECT AVG(duration_secs) FROM sessions WHERE ended_at IS NOT NULL AND started_at > ?",
            (since,), 0.0)
        return round(float(v or 0), 1)

    def retention(self, day: int = 1) -> float:
        """D1/D7/D30 retention — % of players who returned after `day` days."""
        rows = self._q("SELECT player_id, MIN(started_at) first FROM sessions GROUP BY player_id")
        if not rows: return 0.0
        returned = 0
        for r in rows:
            first = datetime.fromisoformat(r["first"])
            target_date = (first + timedelta(days=day)).strftime("%Y-%m-%d")
            count = self._scalar(
                "SELECT COUNT(*) FROM sessions WHERE player_id=? AND started_at LIKE ? AND started_at!=?",
                (r["player_id"], f"{target_date}%", r["first"]))
            if count: returned += 1
        return round(returned / len(rows) * 100, 1)

    def churn_rate(self, inactive_days: int = 30) -> float:
        cutoff = (datetime.utcnow() - timedelta(days=inactive_days)).isoformat()
        total  = self.total_players()
        active = self._scalar(
            "SELECT COUNT(DISTINCT player_id) FROM sessions WHERE started_at > ?", (cutoff,))
        if not total: return 0.0
        return round((1 - active / total) * 100, 1)

    def kd_ratio(self, level_id: str = None) -> float:
        sql = "SELECT SUM(kills), SUM(deaths) FROM sessions"
        params = ()
        if level_id:
            sql += " WHERE level_id=?"; params = (level_id,)
        rows = self._q(sql, params)
        if not rows or not rows[0]["SUM(kills)"]: return 0.0
        k, d = rows[0]["SUM(kills)"] or 0, rows[0]["SUM(deaths)"] or 1
        return round(k / max(d, 1), 2)

    def quest_completion_rate(self) -> Dict[str, float]:
        started   = defaultdict(int)
        completed = defaultdict(int)
        for row in self._q("SELECT metadata FROM events WHERE event_type IN (?,?)",
                           (EventType.QUEST_STARTED.value, EventType.QUEST_COMPLETED.value)):
            meta = json.loads(row["metadata"] or "{}")
            qid  = meta.get("quest_id","unknown")
        # simplified
        s = self._scalar("SELECT COUNT(*) FROM events WHERE event_type=?",
                         (EventType.QUEST_STARTED.value,))
        c2= self._scalar("SELECT COUNT(*) FROM events WHERE event_type=?",
                         (EventType.QUEST_COMPLETED.value,))
        if not s: return {"overall": 0.0}
        return {"overall": round(c2 / s * 100, 1)}

    def most_popular_levels(self, limit: int = 10) -> List[Dict]:
        return self._q(
            "SELECT level_id, COUNT(*) plays, AVG(duration_secs) avg_secs "
            "FROM sessions WHERE level_id != '' GROUP BY level_id "
            "ORDER BY plays DESC LIMIT ?", (limit,))

    def top_items_collected(self, limit: int = 10) -> List[Dict]:
        rows = self._q(
            "SELECT metadata FROM events WHERE event_type=?",
            (EventType.ITEM_COLLECTED.value,))
        counts: Dict[str, int] = defaultdict(int)
        for r in rows:
            meta = json.loads(r["metadata"] or "{}")
            counts[meta.get("item_id","?")] += 1
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"item_id": k, "count": v} for k, v in sorted_items]

    def revenue_summary(self, days: int = 30) -> Dict:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        earned = self._scalar(
            "SELECT SUM(value) FROM events WHERE event_type=? AND timestamp>?",
            (EventType.IAP_PURCHASE.value, since), 0.0)
        payers = self._scalar(
            "SELECT COUNT(DISTINCT player_id) FROM events WHERE event_type=? AND timestamp>?",
            (EventType.IAP_PURCHASE.value, since))
        total  = self.dau()
        return {
            "total_revenue":  round(float(earned or 0), 2),
            "paying_players": payers,
            "conversion_pct": round(payers / max(total, 1) * 100, 1),
            "arpu":           round(float(earned or 0) / max(total, 1), 2),
            "arppu":          round(float(earned or 0) / max(payers, 1), 2),
        }

    def platform_breakdown(self) -> List[Dict]:
        return self._q(
            "SELECT platform, COUNT(*) sessions, COUNT(DISTINCT player_id) players "
            "FROM sessions GROUP BY platform ORDER BY sessions DESC")

    def version_breakdown(self) -> List[Dict]:
        return self._q(
            "SELECT version, COUNT(DISTINCT player_id) players "
            "FROM sessions GROUP BY version ORDER BY players DESC")

    def daily_active_trend(self, days: int = 30) -> List[Dict]:
        result = []
        for i in range(days, -1, -1):
            d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            dau = self._scalar(
                "SELECT COUNT(DISTINCT player_id) FROM sessions WHERE started_at LIKE ?",
                (f"{d}%",))
            result.append({"date": d, "dau": dau})
        return result

    # ── Heatmap ───────────────────────────────────
    def heatmap(self, event_type: EventType, level_id: str = "",
                grid_size: float = 5.0) -> List[HeatmapPoint]:
        sql  = "SELECT x,y,z FROM events WHERE event_type=?"
        args: tuple = (event_type.value,)
        if level_id:
            sql += " AND level_id=?"; args += (level_id,)
        rows = self._q(sql, args)
        # bucket into grid cells
        buckets: Dict[Tuple, int] = defaultdict(int)
        for r in rows:
            gx = round(r["x"] / grid_size) * grid_size
            gz = round(r["z"] / grid_size) * grid_size
            buckets[(gx, r["y"], gz)] += 1
        max_count = max(buckets.values(), default=1)
        return [
            HeatmapPoint(x=k[0], y=k[1], z=k[2],
                         intensity=v / max_count, label=f"{v} events")
            for k, v in sorted(buckets.items(), key=lambda x: x[1], reverse=True)
        ]

    def death_heatmap(self, level_id: str = "") -> List[HeatmapPoint]:
        return self.heatmap(EventType.DEATH, level_id)

    def kill_heatmap(self, level_id: str = "") -> List[HeatmapPoint]:
        return self.heatmap(EventType.KILL, level_id)

    # ── Funnel ────────────────────────────────────
    def funnel(self, steps: List[Tuple[str, EventType]]) -> List[FunnelStep]:
        """steps = [("Step Name", EventType.XXX), ...]"""
        result: List[FunnelStep] = []
        prev_count = None
        for name, etype in steps:
            count = self._scalar(
                "SELECT COUNT(DISTINCT player_id) FROM events WHERE event_type=?",
                (etype.value,))
            drop = 0.0
            if prev_count and prev_count > 0:
                drop = round((1 - count / prev_count) * 100, 1)
            result.append(FunnelStep(name, etype, count, drop))
            prev_count = count
        return result

    def onboarding_funnel(self) -> List[FunnelStep]:
        return self.funnel([
            ("Tutorial Start",    EventType.TUTORIAL_STEP),
            ("First Kill",        EventType.KILL),
            ("Quest Started",     EventType.QUEST_STARTED),
            ("Quest Completed",   EventType.QUEST_COMPLETED),
            ("Item Purchased",    EventType.ITEM_PURCHASED),
        ])

    # ── Player segments ───────────────────────────
    def player_segments(self) -> Dict[str, int]:
        """Classify players by engagement level."""
        rows = self._q(
            "SELECT player_id, total_sessions, total_playtime_secs FROM players")
        segments = {"whales": 0, "regulars": 0, "casuals": 0, "dormant": 0}
        for r in rows:
            hrs = r["total_playtime_secs"] / 3600
            s   = r["total_sessions"]
            if hrs >= 50: segments["whales"]   += 1
            elif hrs >= 10: segments["regulars"]+= 1
            elif s >= 1:  segments["casuals"]  += 1
            else:          segments["dormant"] += 1
        return segments

    def leaderboard(self, metric: str = "kills", limit: int = 10) -> List[Dict]:
        col = {"kills":"total_kills","deaths":"total_deaths",
               "xp":"total_xp","playtime":"total_playtime_secs"}.get(metric, "total_kills")
        return self._q(
            f"SELECT player_id, {col} as value FROM players ORDER BY {col} DESC LIMIT ?",
            (limit,))


# ═══════════════════════ DASHBOARD ══════════════════════════════
class AnalyticsDashboard:
    """Combines tracker + engine + AI insights into a full dashboard."""

    def __init__(self, openai_key: str = "", db_path: str = "analytics.db"):
        self.openai_key = openai_key
        self.tracker    = EventTracker(db_path)
        self.engine     = AnalyticsEngine(db_path)
        self.ab_tests:  Dict[str, ABTest] = {}

    # ── Quick property aliases ────────────────────
    def track(self, *a, **kw) -> GameEvent:
        return self.tracker.track(*a, **kw)

    def start_session(self, *a, **kw) -> str:
        return self.tracker.start_session(*a, **kw)

    def end_session(self, *a, **kw):
        self.tracker.end_session(*a, **kw)

    def flush(self):
        self.tracker.flush()

    # ── Full dashboard snapshot ───────────────────
    def snapshot(self, days: int = 7) -> Dict:
        e = self.engine
        return {
            "generated_at":        datetime.utcnow().isoformat(),
            "period_days":         days,
            "overview": {
                "total_players":   e.total_players(),
                "total_sessions":  e.total_sessions(),
                "dau":             e.dau(),
                "mau":             e.mau(),
                "avg_session_mins":round(e.avg_session_duration(days) / 60, 1),
            },
            "retention": {
                "d1":  e.retention(1),
                "d7":  e.retention(7),
                "d30": e.retention(30),
            },
            "engagement": {
                "churn_rate_pct":  e.churn_rate(),
                "kd_ratio":        e.kd_ratio(),
                "quest_completion":e.quest_completion_rate(),
                "segments":        e.player_segments(),
            },
            "economy":             e.revenue_summary(days),
            "top_levels":          e.most_popular_levels(5),
            "top_items":           e.top_items_collected(5),
            "platforms":           e.platform_breakdown(),
            "versions":            e.version_breakdown(),
            "daily_trend":         e.daily_active_trend(days),
            "leaderboard":         e.leaderboard("kills", 5),
        }

    # ── Heatmap export ────────────────────────────
    def export_heatmap(self, event_type: EventType, level_id: str = "",
                       out: str = "exports") -> str:
        Path(out).mkdir(parents=True, exist_ok=True)
        points = self.engine.heatmap(event_type, level_id)
        p = f"{out}/heatmap_{event_type.value}_{level_id or 'all'}.json"
        Path(p).write_text(json.dumps(
            [{"x":pt.x,"y":pt.y,"z":pt.z,"intensity":pt.intensity} for pt in points],
            indent=2)); return p

    # ── A/B tests ─────────────────────────────────
    def create_ab_test(self, name: str, variant_a: str,
                       variant_b: str, metric: str) -> ABTest:
        test = ABTest(str(uuid.uuid4())[:8], name, variant_a, variant_b,
                      metric, datetime.utcnow().isoformat())
        self.ab_tests[test.test_id] = test
        c = sqlite3.connect(self.engine.db)
        c.execute("INSERT OR IGNORE INTO ab_tests VALUES(?,?,?,?,?,?,?,?)",
                  (test.test_id, test.name, test.variant_a, test.variant_b,
                   test.metric, test.started_at, None, "{}"))
        c.commit(); c.close()
        return test

    def record_ab_result(self, test_id: str, variant: str, metric_value: float):
        t = self.ab_tests.get(test_id)
        if not t: return
        if variant.upper() == "A": t.results_a["metric_value"] = metric_value
        else:                       t.results_b["metric_value"] = metric_value

    # ── AI insights ───────────────────────────────
    async def ai_insights(self, days: int = 7) -> List[str]:
        snap = self.snapshot(days)
        prompt = f"""You are a game analytics expert. Analyse this dashboard data and give
5-7 specific, actionable insights to improve player retention and engagement.

DASHBOARD:
{json.dumps(snap, indent=2)}

Return a JSON array of insight strings. Each should be one clear sentence with a recommendation."""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}",
                             "Content-Type": "application/json"},
                    json={"model": "gpt-4-turbo-preview",
                          "messages": [{"role": "user", "content": prompt}],
                          "response_format": {"type": "json_object"}}
                ) as r:
                    d = await r.json()
                    raw = json.loads(d["choices"][0]["message"]["content"])
                    return raw if isinstance(raw, list) else raw.get("insights", [])
        except Exception:
            return self._fallback_insights(snap)

    def _fallback_insights(self, snap: Dict) -> List[str]:
        insights = []
        d1 = snap["retention"].get("d1", 0)
        if d1 < 40:
            insights.append(f"D1 retention is {d1}% — improve the first-session experience with a better tutorial.")
        churn = snap["engagement"].get("churn_rate_pct", 0)
        if churn > 50:
            insights.append(f"Churn rate of {churn}% is high — add daily login rewards or push notifications.")
        avg = snap["overview"].get("avg_session_mins", 0)
        if avg < 5:
            insights.append(f"Average session is only {avg} min — add quick-play modes to encourage short sessions.")
        return insights or ["Data looks healthy! Keep monitoring retention trends."]

    # ── Export ────────────────────────────────────
    def export_snapshot_json(self, out: str = "exports") -> str:
        Path(out).mkdir(parents=True, exist_ok=True)
        snap = self.snapshot()
        p = f"{out}/analytics_snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        Path(p).write_text(json.dumps(snap, indent=2)); return p

    def export_events_csv(self, limit: int = 10000, out: str = "exports") -> str:
        Path(out).mkdir(parents=True, exist_ok=True)
        rows = self.engine._q(
            "SELECT event_id,player_id,event_type,timestamp,level_id,x,y,z,value "
            "FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
        p = f"{out}/events_export.csv"
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            w.writeheader(); w.writerows(rows)
        return p


# ════════════════════════ DEMO ═══════════════════════════════════
if __name__ == "__main__":
    dash = AnalyticsDashboard()

    # Simulate a week of gameplay
    players = [f"p{i:04d}" for i in range(50)]
    levels  = ["level_01","level_02","level_03","dungeon_01"]
    for day in range(7):
        for pid in random.sample(players, random.randint(10, 35)):
            sid = dash.start_session(pid, random.choice(levels),
                                     platform=random.choice(["pc","console","mobile"]),
                                     version="1.2.0",
                                     country=random.choice(["US","UK","DE","JP","BR"]))
            kills  = random.randint(0, 30)
            deaths = random.randint(0, 10)
            for _ in range(kills):
                dash.track(pid, EventType.KILL,   sid, levels[0], x=random.uniform(0,100), z=random.uniform(0,100))
            for _ in range(deaths):
                dash.track(pid, EventType.DEATH,  sid, levels[0], x=random.uniform(0,100), z=random.uniform(0,100))
            if random.random() > 0.4:
                dash.track(pid, EventType.QUEST_STARTED,   sid, metadata={"quest_id": "q001"})
            if random.random() > 0.6:
                dash.track(pid, EventType.QUEST_COMPLETED, sid, metadata={"quest_id": "q001"})
            if random.random() > 0.8:
                dash.track(pid, EventType.IAP_PURCHASE, sid, value=random.choice([0.99,4.99,9.99]))
            dash.end_session(sid, pid,
                             duration_secs=random.uniform(300, 3600),
                             kills=kills, deaths=deaths,
                             xp=kills*100, currency_earned=kills*10)

    dash.flush()
    snap = dash.snapshot()
    print(json.dumps(snap, indent=2))
    print("\nHeatmap export:", dash.export_heatmap(EventType.DEATH, "level_01"))
    print("Funnel:", [(s.step_name, s.count) for s in dash.engine.onboarding_funnel()])
