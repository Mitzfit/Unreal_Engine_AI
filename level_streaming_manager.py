"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        LEVEL STREAMING MANAGER                                              ║
║  Auto Streaming · LOD · Occlusion Culling · Memory Budgets · Profiling     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class StreamingState(Enum):
    """Level streaming states."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    UNLOADING = "unloading"
    HIDDEN = "hidden"


class LODLevel(Enum):
    """Level of Detail levels."""
    ULTRA = 0        # Highest quality, full detail
    HIGH = 1         # High quality
    MEDIUM = 2       # Medium quality (balanced)
    LOW = 3          # Low quality
    MINIMAL = 4      # Minimal quality


class OcclusionType(Enum):
    """Occlusion culling types."""
    NONE = "none"
    SIMPLE = "simple"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


class MemoryPriority(Enum):
    """Memory allocation priorities."""
    CRITICAL = 1     # Must always be in memory
    HIGH = 2         # Should be loaded first
    NORMAL = 3       # Normal priority
    LOW = 4          # Load if space available
    BACKGROUND = 5   # Load in background


class ProfilingMetric(Enum):
    """Performance metrics to track."""
    FRAME_TIME = "frame_time"
    MEMORY_USAGE = "memory_usage"
    STREAMING_BANDWIDTH = "streaming_bandwidth"
    ASSET_LOAD_TIME = "asset_load_time"
    DRAW_CALLS = "draw_calls"
    TRIANGLE_COUNT = "triangle_count"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class StreamingVolume:
    """Defines a volume that triggers level streaming."""
    volume_id: str
    name: str
    position: Tuple[float, float, float]  # x, y, z
    radius: float
    level_name: str
    
    load_distance: float = 100.0
    unload_distance: float = 150.0
    pre_load_offset: float = 50.0
    
    streaming_priority: MemoryPriority = MemoryPriority.NORMAL
    target_lod: LODLevel = LODLevel.MEDIUM
    
    is_always_loaded: bool = False
    is_visible: bool = True
    
    on_load_callback: Optional[Callable] = None
    on_unload_callback: Optional[Callable] = None
    on_visibility_change: Optional[Callable] = None
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary, excluding callbacks."""
        d = asdict(self)
        d.pop('on_load_callback', None)
        d.pop('on_unload_callback', None)
        d.pop('on_visibility_change', None)
        return d


@dataclass
class LODSettings:
    """LOD configuration for a level."""
    level_name: str
    current_lod: LODLevel = LODLevel.MEDIUM
    
    # Quality settings per LOD
    texture_quality: Dict[LODLevel, int] = field(default_factory=lambda: {
        LODLevel.ULTRA: 100,
        LODLevel.HIGH: 80,
        LODLevel.MEDIUM: 60,
        LODLevel.LOW: 40,
        LODLevel.MINIMAL: 20
    })
    
    mesh_quality: Dict[LODLevel, int] = field(default_factory=lambda: {
        LODLevel.ULTRA: 100,
        LODLevel.HIGH: 90,
        LODLevel.MEDIUM: 70,
        LODLevel.LOW: 50,
        LODLevel.MINIMAL: 30
    })
    
    draw_distance: Dict[LODLevel, float] = field(default_factory=lambda: {
        LODLevel.ULTRA: 10000.0,
        LODLevel.HIGH: 8000.0,
        LODLevel.MEDIUM: 5000.0,
        LODLevel.LOW: 3000.0,
        LODLevel.MINIMAL: 1500.0
    })
    
    shadow_quality: Dict[LODLevel, int] = field(default_factory=lambda: {
        LODLevel.ULTRA: 100,
        LODLevel.HIGH: 80,
        LODLevel.MEDIUM: 60,
        LODLevel.LOW: 40,
        LODLevel.MINIMAL: 20
    })
    
    auto_adjust: bool = True
    adjust_interval: float = 1.0  # seconds
    
    last_adjusted: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class OcclusionData:
    """Occlusion culling information."""
    level_name: str
    occlusion_type: OcclusionType = OcclusionType.CONSERVATIVE
    
    occlusion_mesh_count: int = 0
    occluded_actors_count: int = 0
    visible_actors_count: int = 0
    
    culling_efficiency: float = 0.0  # % of actors culled
    frame_time_saved: float = 0.0    # ms saved from culling
    
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def get_culling_ratio(self) -> float:
        """Get ratio of culled to total actors."""
        total = self.occluded_actors_count + self.visible_actors_count
        if total == 0:
            return 0.0
        return self.occluded_actors_count / total


@dataclass
class MemoryBudget:
    """Memory allocation budget."""
    budget_name: str
    max_memory_mb: float
    
    reserved_memory_mb: float = 0.0
    current_usage_mb: float = 0.0
    
    priority: MemoryPriority = MemoryPriority.NORMAL
    
    allocated_levels: List[str] = field(default_factory=list)
    
    warning_threshold: float = 0.8      # 80% = warning
    critical_threshold: float = 0.95    # 95% = critical
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def usage_percentage(self) -> float:
        """Get memory usage as percentage."""
        if self.max_memory_mb == 0:
            return 0.0
        return self.current_usage_mb / self.max_memory_mb
    
    def available_memory_mb(self) -> float:
        """Get available memory."""
        return max(0, self.max_memory_mb - self.current_usage_mb)
    
    def is_warning(self) -> bool:
        """Check if at warning threshold."""
        return self.usage_percentage() >= self.warning_threshold
    
    def is_critical(self) -> bool:
        """Check if at critical threshold."""
        return self.usage_percentage() >= self.critical_threshold


@dataclass
class PerformanceMetric:
    """Performance profiling metric."""
    metric_type: ProfilingMetric
    value: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level_name: Optional[str] = None
    min_value: float = 0.0
    max_value: float = 0.0
    average_value: float = 0.0


@dataclass
class LoadingScreenInfo:
    """Loading screen display information."""
    screen_id: str
    title: str
    description: str = ""
    
    progress: float = 0.0  # 0.0 - 1.0
    is_visible: bool = False
    
    estimated_time_remaining: float = 0.0  # seconds
    
    assets_loaded: int = 0
    assets_total: int = 0
    
    tips: List[str] = field(default_factory=list)
    current_tip_index: int = 0
    
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ═══════════════════════════════════════════════════════════════════════════════
# LEVEL STREAMING MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class LevelStreamingManager:
    """Main level streaming manager orchestrator."""
    
    def __init__(self):
        self.streaming_volumes: Dict[str, StreamingVolume] = {}
        self.level_states: Dict[str, StreamingState] = {}
        self.lod_settings: Dict[str, LODSettings] = {}
        self.occlusion_data: Dict[str, OcclusionData] = {}
        self.memory_budgets: Dict[str, MemoryBudget] = {}
        self.performance_metrics: Dict[ProfilingMetric, List[PerformanceMetric]] = \
            defaultdict(list)
        self.loading_screens: Dict[str, LoadingScreenInfo] = {}
        
        self.active_camera_position = (0.0, 0.0, 0.0)
        self.frame_count = 0
        self.total_memory_mb = 4096.0  # Default 4GB
        
        self.event_listeners: Dict[str, List[Callable]] = {
            "level_loaded": [],
            "level_unloaded": [],
            "lod_changed": [],
            "memory_warning": [],
            "memory_critical": [],
            "loading_started": [],
            "loading_complete": []
        }
    
    # ═════════════════════════════════ STREAMING VOLUMES ═════════════════════════

    def create_streaming_volume(
        self,
        name: str,
        position: Tuple[float, float, float],
        radius: float,
        level_name: str,
        load_distance: float = 100.0,
        priority: MemoryPriority = MemoryPriority.NORMAL
    ) -> StreamingVolume:
        """Create a new streaming volume."""
        volume = StreamingVolume(
            volume_id=str(uuid.uuid4()),
            name=name,
            position=position,
            radius=radius,
            level_name=level_name,
            load_distance=load_distance,
            streaming_priority=priority
        )
        
        self.streaming_volumes[volume.volume_id] = volume
        self.level_states[level_name] = StreamingState.UNLOADED
        
        logger.info(f"Created streaming volume: {name} for level {level_name}")
        return volume
    
    def check_streaming_volume(
        self,
        camera_position: Tuple[float, float, float]
    ) -> List[Tuple[StreamingVolume, bool]]:
        """Check if volumes should load/unload based on camera position."""
        self.active_camera_position = camera_position
        changes = []
        
        for volume in self.streaming_volumes.values():
            distance = self._calculate_distance(camera_position, volume.position)
            
            should_load = distance < volume.load_distance
            current_state = self.level_states.get(volume.level_name)
            
            # Determine if state should change
            if should_load and current_state in [StreamingState.UNLOADED, StreamingState.HIDDEN]:
                changes.append((volume, True))
            elif not should_load and current_state in [StreamingState.LOADED, StreamingState.ACTIVE]:
                if distance > volume.unload_distance:
                    changes.append((volume, False))
        
        return changes
    
    def load_level(self, level_name: str) -> bool:
        """Load a level."""
        if self.level_states.get(level_name) == StreamingState.LOADED:
            return True
        
        # Check memory budget
        budget = self._get_budget_for_level(level_name)
        if budget and budget.is_critical():
            logger.warning(f"Cannot load {level_name}: Memory critical")
            return False
        
        self.level_states[level_name] = StreamingState.LOADING
        
        # Simulate loading
        asyncio.create_task(self._async_load_level(level_name))
        
        return True
    
    async def _async_load_level(self, level_name: str):
        """Asynchronously load a level."""
        await asyncio.sleep(0.5)  # Simulate loading time
        
        self.level_states[level_name] = StreamingState.LOADED
        
        # Update memory budget
        budget = self._get_budget_for_level(level_name)
        if budget:
            budget.current_usage_mb += 100.0  # Estimate
        
        # Broadcast event
        await self._broadcast_event("level_loaded", {"level": level_name})
        logger.info(f"Loaded level: {level_name}")
    
    def unload_level(self, level_name: str) -> bool:
        """Unload a level."""
        if self.level_states.get(level_name) != StreamingState.LOADED:
            return False
        
        self.level_states[level_name] = StreamingState.UNLOADING
        
        asyncio.create_task(self._async_unload_level(level_name))
        return True
    
    async def _async_unload_level(self, level_name: str):
        """Asynchronously unload a level."""
        await asyncio.sleep(0.3)
        
        self.level_states[level_name] = StreamingState.UNLOADED
        
        # Update memory budget
        budget = self._get_budget_for_level(level_name)
        if budget:
            budget.current_usage_mb = max(0, budget.current_usage_mb - 100.0)
        
        await self._broadcast_event("level_unloaded", {"level": level_name})
        logger.info(f"Unloaded level: {level_name}")
    
    # ═════════════════════════════════ LOD MANAGEMENT ═════════════════════════════

    def create_lod_settings(self, level_name: str) -> LODSettings:
        """Create LOD settings for a level."""
        settings = LODSettings(level_name=level_name)
        self.lod_settings[level_name] = settings
        logger.info(f"Created LOD settings for {level_name}")
        return settings
    
    def calculate_optimal_lod(
        self,
        distance_from_camera: float,
        available_memory_mb: float,
        frame_time_ms: float
    ) -> LODLevel:
        """Calculate optimal LOD based on multiple factors."""
        # Distance-based LOD
        if distance_from_camera < 500:
            distance_lod = LODLevel.ULTRA
        elif distance_from_camera < 1500:
            distance_lod = LODLevel.HIGH
        elif distance_from_camera < 3000:
            distance_lod = LODLevel.MEDIUM
        elif distance_from_camera < 5000:
            distance_lod = LODLevel.LOW
        else:
            distance_lod = LODLevel.MINIMAL
        
        # Memory-based adjustment
        if available_memory_mb < 512:
            memory_lod = LODLevel.MINIMAL
        elif available_memory_mb < 1024:
            memory_lod = LODLevel.LOW
        else:
            memory_lod = distance_lod
        
        # Performance-based adjustment
        target_frame_time = 16.67  # 60 FPS
        if frame_time_ms > target_frame_time * 1.5:
            # Frame time too high, reduce LOD
            performance_lod_value = min(4, memory_lod.value + 1)
            return LODLevel(performance_lod_value)
        
        return memory_lod
    
    def adjust_lod(self, level_name: str, new_lod: LODLevel) -> bool:
        """Adjust LOD for a level."""
        settings = self.lod_settings.get(level_name)
        if not settings:
            return False
        
        old_lod = settings.current_lod
        settings.current_lod = new_lod
        settings.last_adjusted = datetime.utcnow().isoformat()
        
        if old_lod != new_lod:
            asyncio.create_task(
                self._broadcast_event("lod_changed", {
                    "level": level_name,
                    "old_lod": old_lod.name,
                    "new_lod": new_lod.name
                })
            )
        
        return True
    
    def get_lod_quality_values(self, level_name: str) -> Dict:
        """Get quality values for current LOD."""
        settings = self.lod_settings.get(level_name)
        if not settings:
            return {}
        
        lod = settings.current_lod
        return {
            "texture_quality": settings.texture_quality.get(lod, 0),
            "mesh_quality": settings.mesh_quality.get(lod, 0),
            "draw_distance": settings.draw_distance.get(lod, 0),
            "shadow_quality": settings.shadow_quality.get(lod, 0)
        }
    
    # ═════════════════════════════════ OCCLUSION CULLING ═════════════════════════

    def create_occlusion_data(
        self,
        level_name: str,
        occlusion_type: OcclusionType = OcclusionType.CONSERVATIVE
    ) -> OcclusionData:
        """Create occlusion culling data for a level."""
        data = OcclusionData(level_name=level_name, occlusion_type=occlusion_type)
        self.occlusion_data[level_name] = data
        logger.info(f"Created occlusion data for {level_name}: {occlusion_type.value}")
        return data
    
    def update_occlusion(
        self,
        level_name: str,
        visible_actors: int,
        occluded_actors: int
    ) -> float:
        """Update occlusion culling statistics."""
        data = self.occlusion_data.get(level_name)
        if not data:
            return 0.0
        
        data.visible_actors_count = visible_actors
        data.occluded_actors_count = occluded_actors
        
        total = visible_actors + occluded_actors
        if total > 0:
            data.culling_efficiency = (occluded_actors / total) * 100.0
            # Estimate frame time saved
            data.frame_time_saved = occluded_actors * 0.01  # 0.01ms per culled actor
        
        data.last_updated = datetime.utcnow().isoformat()
        return data.culling_efficiency
    
    def get_occlusion_efficiency(self, level_name: str) -> float:
        """Get occlusion culling efficiency percentage."""
        data = self.occlusion_data.get(level_name)
        if not data:
            return 0.0
        return data.culling_efficiency
    
    # ═════════════════════════════════ MEMORY BUDGETS ═════════════════════════════

    def create_memory_budget(
        self,
        budget_name: str,
        max_memory_mb: float,
        priority: MemoryPriority = MemoryPriority.NORMAL
    ) -> MemoryBudget:
        """Create a memory budget."""
        budget = MemoryBudget(
            budget_name=budget_name,
            max_memory_mb=max_memory_mb,
            priority=priority
        )
        self.memory_budgets[budget_name] = budget
        logger.info(f"Created memory budget: {budget_name} ({max_memory_mb}MB)")
        return budget
    
    def allocate_level_to_budget(
        self,
        budget_name: str,
        level_name: str,
        memory_mb: float
    ) -> bool:
        """Allocate a level to a memory budget."""
        budget = self.memory_budgets.get(budget_name)
        if not budget:
            return False
        
        if budget.current_usage_mb + memory_mb > budget.max_memory_mb:
            logger.warning(f"Cannot allocate {level_name}: Exceeds budget")
            return False
        
        budget.allocated_levels.append(level_name)
        budget.current_usage_mb += memory_mb
        
        if budget.is_critical():
            asyncio.create_task(
                self._broadcast_event("memory_critical", {
                    "budget": budget_name,
                    "usage": budget.usage_percentage()
                })
            )
        elif budget.is_warning():
            asyncio.create_task(
                self._broadcast_event("memory_warning", {
                    "budget": budget_name,
                    "usage": budget.usage_percentage()
                })
            )
        
        return True
    
    def get_memory_status(self) -> Dict:
        """Get overall memory status."""
        total_used = sum(b.current_usage_mb for b in self.memory_budgets.values())
        
        return {
            "total_memory_mb": self.total_memory_mb,
            "used_memory_mb": total_used,
            "available_memory_mb": self.total_memory_mb - total_used,
            "usage_percentage": (total_used / self.total_memory_mb) * 100 if self.total_memory_mb > 0 else 0,
            "budgets": {
                name: {
                    "max_mb": budget.max_memory_mb,
                    "used_mb": budget.current_usage_mb,
                    "available_mb": budget.available_memory_mb(),
                    "usage_pct": budget.usage_percentage() * 100,
                    "is_warning": budget.is_warning(),
                    "is_critical": budget.is_critical()
                }
                for name, budget in self.memory_budgets.items()
            }
        }
    
    # ═════════════════════════════════ PERFORMANCE PROFILING ═════════════════════

    def record_metric(
        self,
        metric_type: ProfilingMetric,
        value: float,
        level_name: Optional[str] = None
    ):
        """Record a performance metric."""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            level_name=level_name
        )
        self.performance_metrics[metric_type].append(metric)
        
        # Keep only last 3600 samples (1 hour at 1 sample/sec)
        if len(self.performance_metrics[metric_type]) > 3600:
            self.performance_metrics[metric_type] = \
                self.performance_metrics[metric_type][-3600:]
    
    def get_metric_stats(self, metric_type: ProfilingMetric) -> Dict:
        """Get statistics for a metric."""
        metrics = self.performance_metrics.get(metric_type, [])
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        return {
            "current": values[-1] if values else 0,
            "min": min(values),
            "max": max(values),
            "average": sum(values) / len(values),
            "count": len(values)
        }
    
    def profile_frame(
        self,
        frame_time_ms: float,
        memory_mb: float,
        draw_calls: int,
        triangles: int
    ):
        """Record profiling data for current frame."""
        self.record_metric(ProfilingMetric.FRAME_TIME, frame_time_ms)
        self.record_metric(ProfilingMetric.MEMORY_USAGE, memory_mb)
        self.record_metric(ProfilingMetric.DRAW_CALLS, draw_calls)
        self.record_metric(ProfilingMetric.TRIANGLE_COUNT, triangles)
        
        self.frame_count += 1
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report."""
        return {
            "frame_count": self.frame_count,
            "metrics": {
                metric.name: self.get_metric_stats(metric)
                for metric in ProfilingMetric
            }
        }
    
    # ═════════════════════════════════ LOADING SCREENS ═════════════════════════════

    def create_loading_screen(
        self,
        title: str,
        description: str = "",
        total_assets: int = 0,
        tips: List[str] = None
    ) -> LoadingScreenInfo:
        """Create a loading screen."""
        screen = LoadingScreenInfo(
            screen_id=str(uuid.uuid4()),
            title=title,
            description=description,
            assets_total=total_assets,
            tips=tips or []
        )
        self.loading_screens[screen.screen_id] = screen
        return screen
    
    def show_loading_screen(self, screen_id: str) -> bool:
        """Show a loading screen."""
        screen = self.loading_screens.get(screen_id)
        if not screen:
            return False
        
        screen.is_visible = True
        screen.started_at = datetime.utcnow().isoformat()
        
        asyncio.create_task(
            self._broadcast_event("loading_started", {"screen_id": screen_id})
        )
        
        return True
    
    def update_loading_progress(
        self,
        screen_id: str,
        assets_loaded: int
    ) -> float:
        """Update loading progress."""
        screen = self.loading_screens.get(screen_id)
        if not screen:
            return 0.0
        
        screen.assets_loaded = assets_loaded
        if screen.assets_total > 0:
            screen.progress = assets_loaded / screen.assets_total
        
        return screen.progress
    
    def hide_loading_screen(self, screen_id: str) -> bool:
        """Hide a loading screen."""
        screen = self.loading_screens.get(screen_id)
        if not screen:
            return False
        
        screen.is_visible = False
        
        asyncio.create_task(
            self._broadcast_event("loading_complete", {"screen_id": screen_id})
        )
        
        return True
    
    # ═════════════════════════════════ UTILITY METHODS ═════════════════════════════

    def _calculate_distance(
        self,
        pos1: Tuple[float, float, float],
        pos2: Tuple[float, float, float]
    ) -> float:
        """Calculate 3D Euclidean distance."""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        dz = pos1[2] - pos2[2]
        return (dx**2 + dy**2 + dz**2) ** 0.5
    
    def _get_budget_for_level(self, level_name: str) -> Optional[MemoryBudget]:
        """Get the budget associated with a level."""
        for budget in self.memory_budgets.values():
            if level_name in budget.allocated_levels:
                return budget
        return None
    
    def register_event_listener(self, event_name: str, callback: Callable):
        """Register an event listener."""
        if event_name in self.event_listeners:
            self.event_listeners[event_name].append(callback)
    
    async def _broadcast_event(self, event_name: str, data: Dict):
        """Broadcast an event to all listeners."""
        if event_name in self.event_listeners:
            for callback in self.event_listeners[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Event listener error: {e}")
    
    def to_dict(self) -> Dict:
        """Convert manager state to dictionary."""
        return {
            "streaming_volumes": len(self.streaming_volumes),
            "level_states": {k: v.value for k, v in self.level_states.items()},
            "lod_settings": len(self.lod_settings),
            "memory_status": self.get_memory_status(),
            "performance": self.get_performance_report(),
            "frame_count": self.frame_count
        }


def demo_streaming_manager():
    """Demonstrate level streaming manager."""
    manager = LevelStreamingManager()
    
    # Create streaming volumes
    vol1 = manager.create_streaming_volume(
        name="level_1_volume",
        position=(0, 0, 0),
        radius=200,
        level_name="Level_01_Forest",
        load_distance=100
    )
    
    vol2 = manager.create_streaming_volume(
        name="level_2_volume",
        position=(1000, 0, 0),
        radius=200,
        level_name="Level_02_Cave",
        load_distance=100
    )
    
    # Create LOD settings
    manager.create_lod_settings("Level_01_Forest")
    manager.create_lod_settings("Level_02_Cave")
    
    # Create occlusion data
    manager.create_occlusion_data("Level_01_Forest")
    manager.create_occlusion_data("Level_02_Cave")
    
    # Create memory budgets
    manager.create_memory_budget("gameplay", 2048.0)
    manager.create_memory_budget("streaming", 1024.0)
    
    # Allocate levels to budgets
    manager.allocate_level_to_budget("gameplay", "Level_01_Forest", 800.0)
    manager.allocate_level_to_budget("streaming", "Level_02_Cave", 600.0)
    
    print("Level Streaming Manager Demo:")
    print(f"Streaming volumes: {len(manager.streaming_volumes)}")
    print(f"Memory status: {json.dumps(manager.get_memory_status(), indent=2)}")


if __name__ == "__main__":
    demo_streaming_manager()
