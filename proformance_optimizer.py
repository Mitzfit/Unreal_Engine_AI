"""
╔══════════════════════════════════════════════════════════════╗
║       PERFORMANCE OPTIMIZER  ·  performance_optimizer.py     ║
║  Profiling · LOD · Draw Calls · Memory · GPU · Auto-Fix      ║
╚══════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import asyncio, json, os, sqlite3, time, uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════ ENUMS ══════════════════════════════
class PlatformTarget(Enum):
    PC_HIGH    = "pc_high"
    PC_MED     = "pc_medium"
    PC_LOW     = "pc_low"
    CONSOLE    = "console"
    MOBILE     = "mobile"
    VR         = "vr"

class IssueSeverity(Enum):
    CRITICAL = "critical"    # frame drops / crashes
    HIGH     = "high"        # consistent dips
    MEDIUM   = "medium"      # occasional dips
    LOW      = "low"         # minor improvement possible
    INFO     = "info"        # informational only

class IssueCategory(Enum):
    DRAW_CALLS   = "draw_calls"
    MEMORY       = "memory"
    GPU          = "gpu"
    CPU          = "cpu"
    LOD          = "lod"
    TEXTURE      = "texture"
    SHADER       = "shader"
    PHYSICS      = "physics"
    AUDIO        = "audio"
    STREAMING    = "streaming"
    SHADOW       = "shadow"
    PARTICLE     = "particle"

# Target FPS / budgets per platform
PLATFORM_BUDGETS: Dict[PlatformTarget, Dict] = {
    PlatformTarget.PC_HIGH:  {"fps":120,"draw_calls":3000,"memory_mb":8192,"vram_mb":8192,"triangles_m":15},
    PlatformTarget.PC_MED:   {"fps":60, "draw_calls":2000,"memory_mb":4096,"vram_mb":4096,"triangles_m":8},
    PlatformTarget.PC_LOW:   {"fps":30, "draw_calls":1000,"memory_mb":2048,"vram_mb":2048,"triangles_m":4},
    PlatformTarget.CONSOLE:  {"fps":60, "draw_calls":2500,"memory_mb":6144,"vram_mb":6144,"triangles_m":10},
    PlatformTarget.MOBILE:   {"fps":30, "draw_calls":250, "memory_mb":1024,"vram_mb":512, "triangles_m":1},
    PlatformTarget.VR:       {"fps":90, "draw_calls":1500,"memory_mb":8192,"vram_mb":8192,"triangles_m":6},
}


# ═══════════════════════ DATA CLASSES ═══════════════════════════
@dataclass
class FrameMetrics:
    timestamp:      float
    frame_time_ms:  float
    fps:            float
    gpu_ms:         float
    cpu_ms:         float
    draw_calls:     int
    triangles:      int
    memory_mb:      float
    vram_mb:        float
    shadow_ms:      float  = 0.0
    particle_ms:    float  = 0.0
    physics_ms:     float  = 0.0
    audio_ms:       float  = 0.0

    @property
    def is_smooth(self) -> bool:
        return self.frame_time_ms < 16.7  # 60 fps threshold

    def to_dict(self) -> Dict:
        return {k: round(v, 2) if isinstance(v, float) else v
                for k, v in self.__dict__.items()}


@dataclass
class PerformanceIssue:
    issue_id:    str
    category:   IssueCategory
    severity:   IssueSeverity
    title:      str
    detail:     str
    measured:   Any
    budget:     Any
    auto_fixes: List[str] = field(default_factory=list)
    code_fix:   str       = ""
    doc_url:    str       = ""

    def to_dict(self) -> Dict:
        return {
            "id":        self.issue_id,
            "category":  self.category.value,
            "severity":  self.severity.value,
            "title":     self.title,
            "detail":    self.detail,
            "measured":  self.measured,
            "budget":    self.budget,
            "auto_fixes":self.auto_fixes,
        }


@dataclass
class AssetReport:
    asset_name:   str
    asset_type:   str   # mesh, texture, material, particle, audio
    file_size_mb: float
    triangle_count: int = 0
    texture_res:  str   = ""
    lod_count:    int   = 0
    issues:       List[str] = field(default_factory=list)
    suggestions:  List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return self.__dict__


@dataclass
class OptimizationReport:
    report_id:   str
    platform:    PlatformTarget
    created_at:  str
    issues:      List[PerformanceIssue]
    assets:      List[AssetReport]
    score:       float          # 0-100
    grade:       str            # A-F
    summary:     str
    savings:     Dict           # estimated savings

    def to_dict(self) -> Dict:
        return {
            "report_id":  self.report_id,
            "platform":   self.platform.value,
            "created_at": self.created_at,
            "score":      round(self.score, 1),
            "grade":      self.grade,
            "summary":    self.summary,
            "issues":     [i.to_dict() for i in self.issues],
            "savings":    self.savings,
            "asset_count":len(self.assets),
        }


# ═══════════════════════ PROFILER ═══════════════════════════════
class FrameProfiler:
    """Records and analyses frame metrics over time."""

    HISTORY_LIMIT = 1800  # 30 seconds at 60 fps

    def __init__(self):
        self.frames: List[FrameMetrics] = []

    def record(self, m: FrameMetrics):
        self.frames.append(m)
        if len(self.frames) > self.HISTORY_LIMIT:
            self.frames.pop(0)

    # ── statistics ───────────────────────────────
    def avg(self, attr: str) -> float:
        if not self.frames: return 0.0
        return sum(getattr(f, attr) for f in self.frames) / len(self.frames)

    def p95(self, attr: str) -> float:
        """95th-percentile (frame spikes)."""
        vals = sorted(getattr(f, attr) for f in self.frames)
        if not vals: return 0.0
        idx = int(len(vals) * 0.95)
        return vals[min(idx, len(vals)-1)]

    def p99(self, attr: str) -> float:
        vals = sorted(getattr(f, attr) for f in self.frames)
        if not vals: return 0.0
        return vals[min(int(len(vals)*0.99), len(vals)-1)]

    def min_fps(self) -> float:
        if not self.frames: return 0.0
        return min(f.fps for f in self.frames)

    def max_fps(self) -> float:
        if not self.frames: return 0.0
        return max(f.fps for f in self.frames)

    def stutter_count(self, threshold_ms: float = 33.3) -> int:
        """Frames longer than threshold (stutters)."""
        return sum(1 for f in self.frames if f.frame_time_ms > threshold_ms)

    def summary(self) -> Dict:
        return {
            "samples":         len(self.frames),
            "avg_fps":         round(self.avg("fps"), 1),
            "min_fps":         round(self.min_fps(), 1),
            "max_fps":         round(self.max_fps(), 1),
            "avg_frame_ms":    round(self.avg("frame_time_ms"), 2),
            "p95_frame_ms":    round(self.p95("frame_time_ms"), 2),
            "p99_frame_ms":    round(self.p99("frame_time_ms"), 2),
            "avg_draw_calls":  round(self.avg("draw_calls")),
            "avg_triangles":   round(self.avg("triangles")),
            "avg_memory_mb":   round(self.avg("memory_mb"), 1),
            "avg_vram_mb":     round(self.avg("vram_mb"), 1),
            "avg_gpu_ms":      round(self.avg("gpu_ms"), 2),
            "avg_cpu_ms":      round(self.avg("cpu_ms"), 2),
            "stutter_count":   self.stutter_count(),
        }


# ══════════════════ ANALYSER ════════════════════════════════════
class PerformanceAnalyser:
    """Compares profiler data against platform budgets and surfaces issues."""

    def analyse(
        self,
        profiler: FrameProfiler,
        platform: PlatformTarget,
        assets:   List[AssetReport] = None,
    ) -> List[PerformanceIssue]:
        budget = PLATFORM_BUDGETS[platform]
        stats  = profiler.summary()
        issues: List[PerformanceIssue] = []

        # ── FPS ──────────────────────────────────
        avg_fps = stats["avg_fps"]
        tgt_fps = budget["fps"]
        if avg_fps < tgt_fps * 0.5:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.CPU, IssueSeverity.CRITICAL,
                f"FPS critically low ({avg_fps:.0f} vs {tgt_fps} target)",
                "Average frame rate is less than 50% of target. Immediate optimisation required.",
                measured=avg_fps, budget=tgt_fps,
                auto_fixes=["Reduce draw calls","Disable dynamic shadows","Lower shadow resolution",
                            "Enable occlusion culling","Reduce particle count"],
            ))
        elif avg_fps < tgt_fps * 0.8:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.CPU, IssueSeverity.HIGH,
                f"FPS below target ({avg_fps:.0f} vs {tgt_fps})",
                "Frame rate consistently below target.",
                measured=avg_fps, budget=tgt_fps,
                auto_fixes=["Profile CPU hotspots","Enable async loading","Reduce Blueprint tick rate"],
            ))

        # ── Draw Calls ───────────────────────────
        dc = stats["avg_draw_calls"]
        dc_budget = budget["draw_calls"]
        if dc > dc_budget * 1.5:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.DRAW_CALLS, IssueSeverity.CRITICAL,
                f"Draw calls critically high ({dc:.0f} vs {dc_budget} budget)",
                "Excessive draw calls causing CPU bottleneck.",
                measured=int(dc), budget=dc_budget,
                auto_fixes=["Enable GPU instancing","Merge static meshes","Use HLOD","Enable material batching"],
                code_fix='// Enable instancing on StaticMeshComponent\nMesh->SetMobility(EComponentMobility::Static);\nMesh->bUseDefaultCollision = false;',
            ))
        elif dc > dc_budget:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.DRAW_CALLS, IssueSeverity.HIGH,
                f"Draw calls over budget ({dc:.0f} vs {dc_budget})",
                "Draw calls exceed platform budget.",
                measured=int(dc), budget=dc_budget,
                auto_fixes=["Combine meshes in areas with many static objects","Use Nanite for high-poly assets"],
            ))

        # ── Memory ───────────────────────────────
        mem = stats["avg_memory_mb"]
        mem_b = budget["memory_mb"]
        if mem > mem_b * 0.9:
            sev = IssueSeverity.CRITICAL if mem > mem_b else IssueSeverity.HIGH
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.MEMORY, sev,
                f"Memory usage high ({mem:.0f} MB / {mem_b} MB budget)",
                "Approaching or exceeding memory budget — risk of crashes on target platform.",
                measured=round(mem), budget=mem_b,
                auto_fixes=["Compress textures (use BC7/ASTC)","Enable texture streaming",
                            "Pool frequently-spawned objects","Unload unused level chunks"],
            ))

        # ── VRAM ─────────────────────────────────
        vram  = stats["avg_vram_mb"]
        vram_b= budget["vram_mb"]
        if vram > vram_b * 0.85:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.TEXTURE, IssueSeverity.HIGH,
                f"VRAM high ({vram:.0f} MB / {vram_b} MB)",
                "GPU memory pressure — may cause stuttering as assets are evicted.",
                measured=round(vram), budget=vram_b,
                auto_fixes=["Reduce texture resolution","Enable virtual texturing","Use texture atlases",
                            "Stream textures at distance"],
            ))

        # ── GPU time ─────────────────────────────
        gpu_ms  = stats["avg_gpu_ms"]
        frame_b = 1000 / budget["fps"]
        if gpu_ms > frame_b * 0.7:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.GPU, IssueSeverity.HIGH,
                f"GPU time high ({gpu_ms:.1f} ms, budget {frame_b:.1f} ms)",
                "GPU is the primary bottleneck. Shader or fill-rate issue likely.",
                measured=round(gpu_ms,1), budget=round(frame_b,1),
                auto_fixes=["Optimise expensive shaders","Reduce overdraw","Lower shadow map resolution",
                            "Disable ambient occlusion on low-end targets","Use screen-space reflections instead of ray traced"],
            ))

        # ── Shadows ──────────────────────────────
        shadow_ms = stats.get("avg_shadow_ms", self._extract(profiler, "shadow_ms"))
        if shadow_ms > frame_b * 0.2:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.SHADOW, IssueSeverity.MEDIUM,
                f"Shadow rendering cost high ({shadow_ms:.1f} ms)",
                "Shadow pass consuming too much GPU budget.",
                measured=round(shadow_ms,1), budget=round(frame_b*0.2,1),
                auto_fixes=["Reduce cascade shadow map count","Lower shadow resolution",
                            "Use baked lighting where possible","Enable distance-based shadow fading"],
                code_fix="// Reduce shadow cascades\nDirectionalLight->SetDynamicShadowCascades(2);\nDirectionalLight->SetCascadeDistributionExponent(2.0f);",
            ))

        # ── Particles ────────────────────────────
        part_ms = self._extract(profiler, "particle_ms")
        if part_ms > frame_b * 0.15:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.PARTICLE, IssueSeverity.MEDIUM,
                f"Particle systems expensive ({part_ms:.1f} ms)",
                "Particle simulation is consuming significant frame time.",
                measured=round(part_ms,1), budget=round(frame_b*0.15,1),
                auto_fixes=["Reduce max particle count","Use GPU particles","Add LOD levels to effects",
                            "Pool particle systems","Cull off-screen particles"],
            ))

        # ── Stutters ─────────────────────────────
        sc = stats["stutter_count"]
        if sc > 10:
            issues.append(PerformanceIssue(
                uuid.uuid4().hex[:6], IssueCategory.STREAMING, IssueSeverity.HIGH,
                f"Frequent frame stutters ({sc} detected)",
                "Frame spikes indicate hitches — likely async loading, GC, or shader compilation.",
                measured=sc, budget=0,
                auto_fixes=["Pre-compile shaders at startup","Use async level streaming",
                            "Enable pak file loading","Pool allocations to reduce GC pressure"],
            ))

        # ── Asset-level issues ────────────────────
        for asset in (assets or []):
            issues.extend(self._analyse_asset(asset, budget))

        return issues

    def _extract(self, profiler: FrameProfiler, attr: str) -> float:
        if not profiler.frames: return 0.0
        vals = [getattr(f, attr, 0.0) for f in profiler.frames]
        return sum(vals) / len(vals)

    def _analyse_asset(self, asset: AssetReport, budget: Dict) -> List[PerformanceIssue]:
        issues = []
        if asset.asset_type == "mesh":
            if asset.triangle_count > 500_000:
                issues.append(PerformanceIssue(
                    uuid.uuid4().hex[:6], IssueCategory.LOD, IssueSeverity.HIGH,
                    f"High-poly mesh: {asset.asset_name} ({asset.triangle_count:,} tris)",
                    "This mesh needs LODs. Without them it renders full geometry at all distances.",
                    measured=asset.triangle_count, budget=500_000,
                    auto_fixes=["Auto-generate 4 LOD levels","Enable Nanite (UE5)","Decimate by 50% for LOD1"],
                ))
            if asset.lod_count == 0 and asset.triangle_count > 100_000:
                issues.append(PerformanceIssue(
                    uuid.uuid4().hex[:6], IssueCategory.LOD, IssueSeverity.MEDIUM,
                    f"No LODs: {asset.asset_name}",
                    "Complex mesh missing LOD chain.",
                    measured=0, budget=4,
                    auto_fixes=["Generate LODs with 50%/25%/10%/5% reduction","Enable auto-LOD in import settings"],
                ))
        if asset.asset_type == "texture":
            if "4096" in asset.texture_res or "8192" in asset.texture_res:
                issues.append(PerformanceIssue(
                    uuid.uuid4().hex[:6], IssueCategory.TEXTURE, IssueSeverity.MEDIUM,
                    f"Oversized texture: {asset.asset_name} ({asset.texture_res})",
                    "4K+ textures should only be used for hero assets viewed very close.",
                    measured=asset.texture_res, budget="2048 or less for non-hero",
                    auto_fixes=["Downscale to 2048","Enable BC7 compression","Add texture streaming group"],
                ))
        return issues


# ═════════════════════ OPTIMIZER ════════════════════════════════
class PerformanceOptimizer:
    """Top-level optimizer: profile → analyse → score → AI-suggest."""

    def __init__(self, openai_key: str = ""):
        self.openai_key = openai_key
        self.profiler   = FrameProfiler()
        self.analyser   = PerformanceAnalyser()
        self._init_db()

    def _init_db(self):
        c = sqlite3.connect("performance.db")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY,platform TEXT,score REAL,grade TEXT,data TEXT,ts TEXT);
        CREATE TABLE IF NOT EXISTS frame_sessions(id TEXT PRIMARY KEY,platform TEXT,summary TEXT,ts TEXT);
        """)
        c.commit(); c.close()

    # ── Public API ───────────────────────────────
    def record_frame(self, **kwargs):
        """Feed one frame's metrics into the profiler."""
        self.profiler.record(FrameMetrics(time.time(), **kwargs))

    def record_bulk(self, frames: List[Dict]):
        for f in frames:
            self.profiler.record(FrameMetrics(**f))

    def analyse(
        self,
        platform: PlatformTarget = PlatformTarget.PC_MED,
        assets:   List[AssetReport] = None,
    ) -> OptimizationReport:
        issues  = self.analyser.analyse(self.profiler, platform, assets)
        score   = self._compute_score(issues)
        grade   = self._grade(score)
        savings = self._estimate_savings(issues)
        summary = self._write_summary(score, grade, issues)
        report  = OptimizationReport(
            report_id  = str(uuid.uuid4())[:8],
            platform   = platform,
            created_at = datetime.utcnow().isoformat(),
            issues     = sorted(issues, key=lambda i: list(IssueSeverity).index(i.severity)),
            assets     = assets or [],
            score      = score,
            grade      = grade,
            summary    = summary,
            savings    = savings,
        )
        self._save_report(report); return report

    def quick_scan(self, scene_data: Dict) -> List[str]:
        """Fast heuristic scan of scene JSON — no profiler needed."""
        tips = []
        dc = scene_data.get("draw_calls", 0)
        if dc > 2000: tips.append(f"⚠️ {dc:,} draw calls — consider GPU instancing or mesh merging.")
        lights = scene_data.get("dynamic_lights", 0)
        if lights > 8:  tips.append(f"⚠️ {lights} dynamic lights — each adds shadow passes. Bake where possible.")
        mats = scene_data.get("unique_materials", 0)
        if mats > 500:  tips.append(f"⚠️ {mats} unique materials — use material instances to reduce shader variants.")
        verts = scene_data.get("total_vertices", 0)
        if verts > 5_000_000: tips.append(f"⚠️ {verts:,} vertices in scene — enable Nanite or add LODs.")
        blueprints = scene_data.get("tick_blueprints", 0)
        if blueprints > 50: tips.append(f"⚠️ {blueprints} ticking Blueprints — convert hot paths to C++ or use timers.")
        if not tips: tips.append("✅ Scene looks healthy based on surface scan.")
        return tips

    # ── AI suggestions ───────────────────────────
    async def ai_suggestions(self, report: OptimizationReport) -> List[str]:
        top = [i.to_dict() for i in report.issues[:8]]
        prompt = f"""You are a senior Unreal Engine performance engineer.

Platform:  {report.platform.value}
Score:     {report.score}/100 (grade {report.grade})
Issues:    {json.dumps(top, indent=2)}

Give 5-8 concise, actionable optimisation recommendations.
Return a JSON array of strings, each one specific and practical."""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}","Content-Type":"application/json"},
                    json={"model":"gpt-4-turbo-preview",
                          "messages":[{"role":"user","content":prompt}],
                          "response_format":{"type":"json_object"}}
                ) as r:
                    d = await r.json()
                    raw = json.loads(d["choices"][0]["message"]["content"])
                    return raw if isinstance(raw, list) else raw.get("suggestions", raw.get("recommendations", []))
        except Exception:
            return [f.auto_fixes[0] for f in report.issues[:5] if f.auto_fixes]

    # ── Utilities ────────────────────────────────
    def _compute_score(self, issues: List[PerformanceIssue]) -> float:
        deductions = {IssueSeverity.CRITICAL:20, IssueSeverity.HIGH:10,
                      IssueSeverity.MEDIUM:4,  IssueSeverity.LOW:1, IssueSeverity.INFO:0}
        return max(0.0, 100.0 - sum(deductions[i.severity] for i in issues))

    def _grade(self, score: float) -> str:
        if score >= 90: return "A"
        if score >= 80: return "B"
        if score >= 70: return "C"
        if score >= 60: return "D"
        return "F"

    def _estimate_savings(self, issues: List[PerformanceIssue]) -> Dict:
        draw_saves = sum(1 for i in issues if i.category == IssueCategory.DRAW_CALLS) * 500
        mem_saves  = sum(1 for i in issues if i.category == IssueCategory.MEMORY)     * 512
        fps_gain   = sum(1 for i in issues if i.severity in (IssueSeverity.CRITICAL,IssueSeverity.HIGH)) * 5
        return {"estimated_draw_call_reduction":draw_saves,
                "estimated_memory_mb_saved":mem_saves,
                "estimated_fps_gain":min(fps_gain, 60)}

    def _write_summary(self, score: float, grade: str, issues: List[PerformanceIssue]) -> str:
        crit = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        return (f"Performance grade {grade} ({score:.0f}/100). "
                f"{crit} critical and {high} high-priority issues found. "
                f"{'Immediate action required.' if crit else 'Good baseline — target improvements above.'}")

    def _save_report(self, report: OptimizationReport):
        c = sqlite3.connect("performance.db")
        c.execute("INSERT OR REPLACE INTO reports VALUES(?,?,?,?,?,?)",
                  (report.report_id, report.platform.value, report.score,
                   report.grade, json.dumps(report.to_dict()), datetime.utcnow().isoformat()))
        c.commit(); c.close()

    def export_report(self, report: OptimizationReport, out: str = "exports") -> str:
        Path(out).mkdir(parents=True, exist_ok=True)
        p = f"{out}/perf_report_{report.report_id}.json"
        Path(p).write_text(json.dumps(report.to_dict(), indent=2)); return p

    def export_csv(self, report: OptimizationReport, out: str = "exports") -> str:
        import csv
        Path(out).mkdir(parents=True, exist_ok=True)
        p = f"{out}/perf_issues_{report.report_id}.csv"
        with open(p,"w",newline="") as f:
            w = csv.writer(f)
            w.writerow(["id","category","severity","title","measured","budget","top_fix"])
            for i in report.issues:
                w.writerow([i.issue_id, i.category.value, i.severity.value,
                             i.title, i.measured, i.budget,
                             i.auto_fixes[0] if i.auto_fixes else ""])
        return p


# ════════════════════════ DEMO ═══════════════════════════════════
if __name__ == "__main__":
    import random
    opt = PerformanceOptimizer()

    # Simulate 300 frames of bad performance
    for i in range(300):
        opt.record_frame(
            timestamp=time.time(), frame_time_ms=random.uniform(18,28),
            fps=random.uniform(35,55), gpu_ms=random.uniform(10,16),
            cpu_ms=random.uniform(8,14), draw_calls=random.randint(2500,3500),
            triangles=random.randint(8_000_000,12_000_000),
            memory_mb=random.uniform(3500,4200), vram_mb=random.uniform(3800,4500),
            shadow_ms=random.uniform(3,6), particle_ms=random.uniform(2,4),
            physics_ms=random.uniform(1,3), audio_ms=random.uniform(0.5,1),
        )

    assets = [
        AssetReport("DragonMesh","mesh",45.0,triangle_count=980_000,lod_count=0),
        AssetReport("CastleWall4K","texture",32.0,texture_res="4096x4096"),
        AssetReport("SmallRock","mesh",0.5,triangle_count=2_000,lod_count=3),
    ]

    report = opt.analyse(PlatformTarget.PC_MED, assets)
    print(json.dumps(report.to_dict(), indent=2))
    print("Quick scan:", opt.quick_scan({"draw_calls":3200,"dynamic_lights":12,"unique_materials":600}))
    print("Exported:", opt.export_report(report))
