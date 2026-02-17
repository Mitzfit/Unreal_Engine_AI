"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     LEVEL STREAMING MANAGER GUIDE                           ║
║             Complete Documentation · API Reference · Integration            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# COMPREHENSIVE LEVEL STREAMING SYSTEM DOCUMENTATION

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [Web Dashboard](#web-dashboard)
6. [Unreal Integration](#unreal-integration)
7. [Examples](#examples)
8. [Best Practices](#best-practices)

---

## OVERVIEW

The Level Streaming Manager is a comprehensive system for managing large-scale game worlds with:

- **Automatic Streaming Volumes**: Distance-based level loading/unloading
- **LOD System**: Intelligent quality adjustment based on distance, memory, and frame time
- **Occlusion Culling**: Visibility optimization with efficiency tracking
- **Memory Management**: Budget tracking with priority levels
- **Performance Profiling**: Real-time metrics monitoring
- **Loading Screens**: Progress tracking and user feedback
- **WebSocket Integration**: Real-time Unreal Engine synchronization

### Key Features

✅ **Smart Streaming**
- Distance-based triggers
- Priority-aware loading
- Async level operations
- Automatic unloading

✅ **Advanced LOD**
- Multi-factor calculation
- Distance-based adjustment
- Memory-aware scaling
- Performance-driven changes

✅ **Visibility Optimization**
- Occlusion culling stats
- Efficiency metrics
- Frame time tracking
- Triangle/draw call reduction

✅ **Memory Intelligence**
- Budget allocation
- Priority levels
- Warning/critical states
- Automatic cleanup

✅ **Performance Insights**
- Frame time tracking
- Memory usage profiling
- Draw call monitoring
- Triangle count tracking

---

## QUICK START

### Installation

```bash
# 1. Copy files to your project
cp level_streaming_manager.py your_project/
cp level_streaming_web.py your_project/
cp level_streaming_unreal_integration.py your_project/

# 2. Install dependencies
pip install fastapi uvicorn websockets pydantic

# 3. Start the web server
python level_streaming_web.py
# Server runs on http://localhost:8000

# 4. Start Unreal bridge (in another terminal)
python level_streaming_unreal_integration.py
# WebSocket runs on ws://localhost:8765
```

### Basic Usage

```python
from level_streaming_manager import LevelStreamingManager, MemoryPriority

# Create manager
manager = LevelStreamingManager()

# Create streaming volume
volume = manager.create_streaming_volume(
    name="forest_volume",
    position=(0, 0, 0),
    radius=500,
    level_name="Forest",
    load_distance=200,
    priority=MemoryPriority.HIGH
)

# Set up memory budget
budget = manager.create_memory_budget(
    budget_name="world_streaming",
    max_memory_mb=1024
)

# Allocate levels to budget
manager.allocate_level_to_budget("world_streaming", "Forest", 256)
manager.allocate_level_to_budget("world_streaming", "Desert", 256)

# Create LOD settings
lod_settings = manager.create_lod_settings("Forest")

# Check volumes each frame
changes = manager.check_streaming_volume((camera_x, camera_y, camera_z))
for volume, should_load in changes:
    if should_load:
        manager.load_level(volume.level_name)
    else:
        manager.unload_level(volume.level_name)
```

---

## CORE CONCEPTS

### 1. Streaming States

```
UNLOADED → LOADING → LOADED → ACTIVE
                              ↓
                            UNLOADING → HIDDEN
```

- **UNLOADED**: Level not in memory
- **LOADING**: Async load in progress
- **LOADED**: In memory, not visible
- **ACTIVE**: Visible and updating
- **UNLOADING**: Async unload in progress
- **HIDDEN**: Previously active, now hidden

### 2. LOD Levels

```
ULTRA (0)    - Highest quality, high memory/GPU cost
HIGH (1)     - High quality, balanced
MEDIUM (2)   - Balanced quality and performance
LOW (3)      - Reduced quality, low performance impact
MINIMAL (4)  - Minimal quality, minimal cost
```

Each LOD level has quality settings:

```python
LOD_QUALITY_VALUES = {
    LODLevel.ULTRA: {
        "texture_quality": 1.0,
        "mesh_quality": 1.0,
        "draw_distance": 10000,
        "shadow_quality": 1.0
    },
    LODLevel.HIGH: {
        "texture_quality": 0.8,
        "mesh_quality": 0.95,
        "draw_distance": 8000,
        "shadow_quality": 0.8
    },
    LODLevel.MEDIUM: {
        "texture_quality": 0.6,
        "mesh_quality": 0.85,
        "draw_distance": 6000,
        "shadow_quality": 0.6
    },
    LODLevel.LOW: {
        "texture_quality": 0.4,
        "mesh_quality": 0.7,
        "draw_distance": 4000,
        "shadow_quality": 0.3
    },
    LODLevel.MINIMAL: {
        "texture_quality": 0.2,
        "mesh_quality": 0.5,
        "draw_distance": 2000,
        "shadow_quality": 0
    }
}
```

### 3. Memory Priorities

```
CRITICAL (1)   - Must always be loaded (main area)
HIGH (2)       - High priority, load first
NORMAL (3)     - Default priority
LOW (4)        - Can unload if needed
BACKGROUND (5) - Lowest priority, unload first
```

### 4. Performance Metrics

Tracked metrics:
- **FRAME_TIME**: Time to render one frame (ms)
- **MEMORY_USAGE**: Total memory used (MB)
- **STREAMING_BANDWIDTH**: Data loaded per second (MB/s)
- **ASSET_LOAD_TIME**: Time to load asset (ms)
- **DRAW_CALLS**: Draw calls per frame
- **TRIANGLE_COUNT**: Triangles rendered per frame

---

## API REFERENCE

### Core Classes

#### LevelStreamingManager

Main orchestrator class.

**Methods:**

```python
# Streaming Volume Management
create_streaming_volume(name, position, radius, level_name, 
                       load_distance, priority)
check_streaming_volume(camera_position) -> List[Tuple[Volume, bool]]

# Level Loading
load_level(level_name) -> bool
unload_level(level_name) -> bool

# LOD Management
create_lod_settings(level_name) -> LODSettings
calculate_optimal_lod(distance, available_memory, frame_time) -> LODLevel
adjust_lod(level_name, new_lod) -> bool
get_lod_quality_values(level_name) -> Dict

# Occlusion Culling
create_occlusion_data(level_name, occlusion_type) -> OcclusionData
update_occlusion(level_name, visible_actors, occluded_actors) -> float
get_occlusion_efficiency(level_name) -> float

# Memory Management
create_memory_budget(name, max_memory_mb, priority) -> MemoryBudget
allocate_level_to_budget(budget, level, memory) -> bool
get_memory_status() -> Dict

# Performance Profiling
record_metric(metric_type, value)
get_metric_stats(metric_type) -> Dict
profile_frame(frame_time, memory, draw_calls, triangles)
get_performance_report() -> Dict

# Loading Screens
create_loading_screen(title, description, total_assets) -> LoadingScreenInfo
show_loading_screen(screen_id) -> bool
update_loading_progress(screen_id, assets_loaded) -> float
hide_loading_screen(screen_id) -> bool

# Events
register_event_listener(event_type, callback)
```

#### StreamingVolume

Defines an area that triggers level streaming.

```python
@dataclass
class StreamingVolume:
    volume_id: str
    name: str
    position: Tuple[float, float, float]
    radius: float
    level_name: str
    load_distance: float
    unload_distance: float
    priority: MemoryPriority
    is_active: bool
    load_callback: Optional[Callable]
    unload_callback: Optional[Callable]
```

#### LODSettings

Configuration for level-of-detail system.

```python
@dataclass
class LODSettings:
    level_name: str
    current_lod: LODLevel
    auto_adjust: bool
    distance_thresholds: Dict[LODLevel, float]
    memory_thresholds: Dict[LODLevel, float]
```

#### MemoryBudget

Memory allocation tracking.

```python
@dataclass
class MemoryBudget:
    budget_name: str
    max_memory_mb: float
    current_usage_mb: float
    priority: MemoryPriority
    allocated_levels: Dict[str, float]
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95
```

---

## WEB DASHBOARD

### Access

Open browser: **http://localhost:8000**

### Tabs

#### 1. Overview Tab
- Total memory status
- Active volumes count
- Loaded levels
- Frame statistics
- Performance indicators

#### 2. Volumes Tab
- Create new streaming volumes
- List active volumes
- Monitor volume activity
- Adjust load distances

#### 3. LOD Tab
- Create LOD settings
- Adjust LOD levels
- Calculate optimal LOD
- View quality settings

#### 4. Occlusion Tab
- Update culling statistics
- View efficiency metrics
- Monitor triangle reduction
- Frame time savings

#### 5. Memory Tab
- Create budgets
- Allocate levels
- Monitor usage percentage
- View warning states

#### 6. Performance Tab
- Record frame metrics
- View performance statistics
- Track average frame time
- Monitor draw calls

#### 7. Loading Tab
- Create loading screens
- Show/hide screens
- Update progress
- Track timing

---

## UNREAL INTEGRATION

### WebSocket Bridge

Connect Unreal to Python backend:

```cpp
// In your Unreal level
void AMyGameMode::BeginPlay()
{
    Super::BeginPlay();
    
    // Connect to streaming bridge
    UWebSocketConnection* Connection = NewObject<UWebSocketConnection>();
    Connection->Connect("ws://localhost:8765");
}
```

### Unreal Events

```cpp
// Subscribe to streaming events
void AMyCharacter::BeginPlay()
{
    Super::BeginPlay();
    
    if (ALevelStreamingManager* StreamingMgr = 
        GetWorld()->SpawnActor<ALevelStreamingManager>())
    {
        // Level state changed
        StreamingMgr->OnLevelStateChanged.AddDynamic(this, 
            &AMyCharacter::OnLevelStateChanged);
        
        // Memory state changed
        StreamingMgr->OnMemoryStateChanged.AddDynamic(this,
            &AMyCharacter::OnMemoryStateChanged);
        
        // Performance warning
        StreamingMgr->OnPerformanceWarning.AddDynamic(this,
            &AMyCharacter::OnPerformanceWarning);
    }
}

void AMyCharacter::OnLevelStateChanged(const FString& LevelName, 
    EStreamingState NewState)
{
    if (NewState == EStreamingState::ACTIVE)
    {
        UE_LOG(LogStreaming, Warning, TEXT("Level %s is now active"), 
            *LevelName);
    }
}
```

### Unreal API

```cpp
// Load level
StreamingManager->LoadLevel("Forest");

// Unload level
StreamingManager->UnloadLevel("Forest");

// Set LOD
StreamingManager->SetLOD("Forest", ELODLevel::HIGH);

// Get level state
EStreamingState State = StreamingManager->GetLevelState("Forest");

// Check memory
float UsedMemory, TotalMemory;
StreamingManager->GetMemoryStatus(UsedMemory, TotalMemory);

// Record performance
StreamingManager->RecordFrame(16.67f, 512.0f, 2000, 5000000);

// Get report
FString Report = StreamingManager->GetPerformanceReport();
```

---

## EXAMPLES

### Example 1: Streaming Multiple Levels

```python
from level_streaming_manager import LevelStreamingManager, MemoryPriority

manager = LevelStreamingManager()

# Create volumes for different areas
areas = [
    ("Forest Hub", (0, 0, 0), "Forest_Hub"),
    ("Desert Zone", (1000, 0, 0), "Desert_Zone"),
    ("Mountain Pass", (2000, 0, 0), "Mountain_Pass"),
    ("Underground Cavern", (1000, 1000, -500), "Cavern")
]

for name, pos, level in areas:
    volume = manager.create_streaming_volume(
        name=name,
        position=pos,
        radius=500,
        level_name=level,
        load_distance=300,
        priority=MemoryPriority.NORMAL
    )

# Game loop
def game_loop():
    while True:
        camera_pos = get_camera_position()
        
        # Check which levels should load/unload
        changes = manager.check_streaming_volume(camera_pos)
        
        for volume, should_load in changes:
            if should_load:
                print(f"Loading {volume.level_name}...")
                manager.load_level(volume.level_name)
            else:
                print(f"Unloading {volume.level_name}...")
                manager.unload_level(volume.level_name)
```

### Example 2: Smart LOD Adjustment

```python
def update_lods():
    """Update LOD based on current conditions."""
    
    # Get performance data
    perf_report = manager.get_performance_report()
    avg_frame_time = perf_report["metrics"]["FRAME_TIME"]["average"]
    
    # Get memory status
    mem_status = manager.get_memory_status()
    memory_pct = mem_status["usage_percentage"]
    
    # Adjust LODs for each active level
    for level_name in manager.level_states:
        if manager.level_states[level_name].value == "ACTIVE":
            # Calculate optimal LOD
            lod = manager.calculate_optimal_lod(
                distance=distance_to_camera,
                available_memory_mb=1024 - mem_status["used_memory_mb"],
                frame_time_ms=avg_frame_time
            )
            
            # Apply if different
            current_lod = manager.lod_settings[level_name].current_lod
            if current_lod != lod:
                print(f"Adjusting {level_name} from {current_lod.name} to {lod.name}")
                manager.adjust_lod(level_name, lod)
```

### Example 3: Memory Budget Management

```python
def setup_memory_budgets():
    """Set up memory budgets for different systems."""
    
    # Create budgets
    world_budget = manager.create_memory_budget(
        budget_name="world_streaming",
        max_memory_mb=2048,
        priority=MemoryPriority.HIGH
    )
    
    ui_budget = manager.create_memory_budget(
        budget_name="ui_assets",
        max_memory_mb=512,
        priority=MemoryPriority.NORMAL
    )
    
    # Allocate levels
    manager.allocate_level_to_budget("world_streaming", "Forest_Hub", 512)
    manager.allocate_level_to_budget("world_streaming", "Desert_Zone", 512)
    manager.allocate_level_to_budget("world_streaming", "Mountain_Pass", 512)
    manager.allocate_level_to_budget("world_streaming", "Cavern", 512)
    
    # Monitor
    while True:
        status = manager.get_memory_status()
        
        for budget_name, budget in manager.memory_budgets.items():
            if budget.is_critical():
                print(f"CRITICAL: {budget_name} at {budget.usage_percentage() * 100:.1f}%")
            elif budget.is_warning():
                print(f"WARNING: {budget_name} at {budget.usage_percentage() * 100:.1f}%")
```

### Example 4: Performance Monitoring

```python
def monitor_performance():
    """Monitor and log performance metrics."""
    
    while True:
        # Get metrics
        frame_stats = manager.get_metric_stats(ProfilingMetric.FRAME_TIME)
        memory_stats = manager.get_metric_stats(ProfilingMetric.MEMORY_USAGE)
        
        # Check thresholds
        if frame_stats["average"] > 20:
            print(f"Frame time high: {frame_stats['average']:.2f}ms")
            
            # Auto-reduce quality
            for level_name in manager.lod_settings:
                current_lod = manager.lod_settings[level_name].current_lod
                if current_lod != LODLevel.MINIMAL:
                    next_lod = LODLevel(current_lod.value + 1)
                    manager.adjust_lod(level_name, next_lod)
        
        if memory_stats["average"] > 3000:  # 3GB
            print(f"Memory high: {memory_stats['average']:.1f}MB")
            
            # Unload lowest priority levels
            for level_name, state in manager.level_states.items():
                if state == StreamingState.LOADED:
                    manager.unload_level(level_name)
        
        time.sleep(1)
```

---

## BEST PRACTICES

### 1. Streaming Volumes

✅ **DO:**
- Create volumes strategically around key areas
- Use appropriate load/unload distances
- Set priorities based on importance
- Test volume overlap

❌ **DON'T:**
- Create too many overlapping volumes
- Set load distances too large
- Ignore memory constraints
- Forget to create LOD settings

### 2. LOD Management

✅ **DO:**
- Enable auto-adjust for dynamic adaptation
- Test with varied hardware
- Monitor frame time impact
- Provide player LOD presets

❌ **DON'T:**
- Make quality differences too extreme
- Ignore distance-based changes
- Set unrealistic distance thresholds
- Forget about shader complexity

### 3. Memory Management

✅ **DO:**
- Create budgets per system
- Allocate realistically
- Monitor warning states
- Plan for edge cases

❌ **DON'T:**
- Overallocate budgets
- Ignore critical states
- Load unnecessary levels
- Forget to track usage

### 4. Performance

✅ **DO:**
- Profile regularly
- Set reasonable thresholds
- React to warnings
- Test on target hardware

❌ **DON'T:**
- Ignore performance warnings
- Load too many levels
- Render distant geometry
- Skip profiling

### 5. Loading Screens

✅ **DO:**
- Show progress feedback
- Provide tips/hints
- Estimate load time
- Handle errors gracefully

❌ **DON'T:**
- Skip loading screens
- Show inaccurate progress
- Provide no feedback
- Allow skipping loads

---

## TROUBLESHOOTING

### Levels Not Loading

**Problem**: Levels stay in LOADING state
**Solution**:
1. Check volume is created: `print(manager.streaming_volumes)`
2. Verify camera is in load distance: `print(volume.load_distance)`
3. Check memory budget: `print(manager.get_memory_status())`

### High Memory Usage

**Problem**: Memory exceeds budget
**Solution**:
1. Lower LOD levels: `manager.adjust_lod(level, LODLevel.LOW)`
2. Unload inactive levels: `manager.unload_level(level_name)`
3. Check occlusion efficiency: `print(manager.get_occlusion_efficiency(level))`

### Frame Rate Drops

**Problem**: FPS drops below target
**Solution**:
1. Enable performance profiling
2. Check draw calls: `stats = manager.get_metric_stats(ProfilingMetric.DRAW_CALLS)`
3. Reduce LOD or triangle count
4. Enable aggressive occlusion

### WebSocket Connection Issues

**Problem**: Can't connect to Unreal
**Solution**:
1. Verify bridge is running: `python level_streaming_unreal_integration.py`
2. Check port 8765 is open
3. Verify WebSocket in Unreal code
4. Check firewall settings

---

## PERFORMANCE TARGETS

Recommended values:

```python
# Frame Time Targets
FRAME_TIME_TARGET_60FPS = 16.67  # ms
FRAME_TIME_TARGET_30FPS = 33.33  # ms

# Memory Budgets
BUDGET_HIGH_END = 4096    # MB (4GB)
BUDGET_MID_END = 2048     # MB (2GB)
BUDGET_LOW_END = 1024     # MB (1GB)

# LOD Distances
ULTRA_DISTANCE = 1000     # meters
HIGH_DISTANCE = 2000
MEDIUM_DISTANCE = 4000
LOW_DISTANCE = 8000
MINIMAL_DISTANCE = 16000

# Occlusion
MIN_CULLING_EFFICIENCY = 0.3  # 30%
GOOD_CULLING_EFFICIENCY = 0.6  # 60%
EXCELLENT_CULLING_EFFICIENCY = 0.8  # 80%
```

---

## SUMMARY

The Level Streaming Manager provides a complete solution for managing large-scale game worlds. Use this guide to:

1. Set up streaming volumes strategically
2. Implement LOD systems effectively
3. Manage memory budgets
4. Monitor performance
5. Integrate with Unreal Engine
6. Provide smooth player experience

For more help, check the documentation files or the web dashboard at http://localhost:8000!
