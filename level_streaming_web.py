"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              LEVEL STREAMING WEB API & DASHBOARD                            ║
║                 REST API · Real-time Monitoring · Control Panel             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import logging

from level_streaming_manager import (
    LevelStreamingManager, StreamingVolume, StreamingState, LODLevel,
    OcclusionType, MemoryPriority, ProfilingMetric
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class StreamingVolumeRequest(BaseModel):
    name: str
    position: tuple
    radius: float
    level_name: str
    load_distance: float = 100.0
    priority: str = "NORMAL"


class LODRequest(BaseModel):
    level_name: str
    new_lod: str


class OcclusionRequest(BaseModel):
    level_name: str
    visible_actors: int
    occluded_actors: int


class MemoryBudgetRequest(BaseModel):
    budget_name: str
    max_memory_mb: float
    priority: str = "NORMAL"


class LoadLevelRequest(BaseModel):
    level_name: str


class ProfileFrameRequest(BaseModel):
    frame_time_ms: float
    memory_mb: float
    draw_calls: int
    triangles: int


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="Level Streaming Manager", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = LevelStreamingManager()
connected_clients: List[WebSocket] = []


# ═══════════════════════════════════════════════════════════════════════════════
# STREAMING VOLUME ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/volumes/create")
async def create_volume(req: StreamingVolumeRequest):
    """Create a new streaming volume."""
    try:
        priority = MemoryPriority[req.priority]
        volume = manager.create_streaming_volume(
            name=req.name,
            position=req.position,
            radius=req.radius,
            level_name=req.level_name,
            load_distance=req.load_distance,
            priority=priority
        )
        return {"volume_id": volume.volume_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/volumes")
async def list_volumes():
    """List all streaming volumes."""
    return {
        "volumes": [v.to_dict() for v in manager.streaming_volumes.values()],
        "count": len(manager.streaming_volumes)
    }


@app.post("/api/volumes/check")
async def check_volumes(camera_pos: tuple):
    """Check which volumes should load/unload."""
    changes = manager.check_streaming_volume(camera_pos)
    return {
        "changes": [
            {"level": vol.level_name, "should_load": load}
            for vol, load in changes
        ],
        "count": len(changes)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LEVEL MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/levels/load")
async def load_level(req: LoadLevelRequest):
    """Load a level."""
    result = manager.load_level(req.level_name)
    state = manager.level_states.get(req.level_name, StreamingState.UNLOADED)
    return {
        "level": req.level_name,
        "success": result,
        "state": state.value
    }


@app.post("/api/levels/unload")
async def unload_level(req: LoadLevelRequest):
    """Unload a level."""
    result = manager.unload_level(req.level_name)
    return {"level": req.level_name, "success": result}


@app.get("/api/levels/states")
async def get_level_states():
    """Get all level states."""
    return {
        "states": {k: v.value for k, v in manager.level_states.items()},
        "count": len(manager.level_states)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LOD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/lod/create")
async def create_lod(level_name: str):
    """Create LOD settings for a level."""
    settings = manager.create_lod_settings(level_name)
    return {"level": level_name, "current_lod": settings.current_lod.name}


@app.post("/api/lod/adjust")
async def adjust_lod(req: LODRequest):
    """Adjust LOD for a level."""
    try:
        new_lod = LODLevel[req.new_lod]
        result = manager.adjust_lod(req.level_name, new_lod)
        quality = manager.get_lod_quality_values(req.level_name)
        return {
            "level": req.level_name,
            "success": result,
            "new_lod": new_lod.name,
            "quality_values": quality
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/lod/calculate")
async def calculate_lod(
    distance: float,
    available_memory_mb: float,
    frame_time_ms: float
):
    """Calculate optimal LOD."""
    lod = manager.calculate_optimal_lod(distance, available_memory_mb, frame_time_ms)
    return {
        "optimal_lod": lod.name,
        "distance": distance,
        "available_memory_mb": available_memory_mb,
        "frame_time_ms": frame_time_ms
    }


@app.get("/api/lod/settings/{level_name}")
async def get_lod_settings(level_name: str):
    """Get LOD settings for a level."""
    settings = manager.lod_settings.get(level_name)
    if not settings:
        raise HTTPException(status_code=404, detail="Level not found")
    
    return {
        "level": level_name,
        "current_lod": settings.current_lod.name,
        "quality_values": manager.get_lod_quality_values(level_name)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# OCCLUSION CULLING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/occlusion/create")
async def create_occlusion(level_name: str, occlusion_type: str = "CONSERVATIVE"):
    """Create occlusion culling data."""
    try:
        occ_type = OcclusionType[occlusion_type]
        data = manager.create_occlusion_data(level_name, occ_type)
        return {"level": level_name, "occlusion_type": occ_type.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/occlusion/update")
async def update_occlusion(req: OcclusionRequest):
    """Update occlusion statistics."""
    efficiency = manager.update_occlusion(
        req.level_name,
        req.visible_actors,
        req.occluded_actors
    )
    
    data = manager.occlusion_data.get(req.level_name)
    return {
        "level": req.level_name,
        "efficiency": efficiency,
        "visible_actors": req.visible_actors,
        "occluded_actors": req.occluded_actors,
        "frame_time_saved_ms": data.frame_time_saved if data else 0
    }


@app.get("/api/occlusion/{level_name}")
async def get_occlusion(level_name: str):
    """Get occlusion data for a level."""
    data = manager.occlusion_data.get(level_name)
    if not data:
        raise HTTPException(status_code=404, detail="Level not found")
    
    return {
        "level": level_name,
        "efficiency": data.culling_efficiency,
        "visible_actors": data.visible_actors_count,
        "occluded_actors": data.occluded_actors_count,
        "frame_time_saved_ms": data.frame_time_saved
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY BUDGET ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/memory/budget/create")
async def create_budget(req: MemoryBudgetRequest):
    """Create a memory budget."""
    try:
        priority = MemoryPriority[req.priority]
        budget = manager.create_memory_budget(
            req.budget_name,
            req.max_memory_mb,
            priority
        )
        return {"budget_name": budget.budget_name, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/memory/allocate")
async def allocate_to_budget(
    budget_name: str,
    level_name: str,
    memory_mb: float
):
    """Allocate level to memory budget."""
    result = manager.allocate_level_to_budget(budget_name, level_name, memory_mb)
    if not result:
        raise HTTPException(status_code=400, detail="Allocation failed")
    
    return {"success": result, "level": level_name, "memory_mb": memory_mb}


@app.get("/api/memory/status")
async def get_memory_status():
    """Get overall memory status."""
    return manager.get_memory_status()


@app.get("/api/memory/budgets")
async def list_budgets():
    """List all memory budgets."""
    budgets = []
    for name, budget in manager.memory_budgets.items():
        budgets.append({
            "name": name,
            "max_mb": budget.max_memory_mb,
            "used_mb": budget.current_usage_mb,
            "available_mb": budget.available_memory_mb(),
            "usage_pct": budget.usage_percentage() * 100,
            "is_warning": budget.is_warning(),
            "is_critical": budget.is_critical()
        })
    
    return {"budgets": budgets, "count": len(budgets)}


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE PROFILING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/performance/profile-frame")
async def profile_frame(req: ProfileFrameRequest):
    """Record frame profiling data."""
    manager.profile_frame(
        req.frame_time_ms,
        req.memory_mb,
        req.draw_calls,
        req.triangles
    )
    return {"status": "recorded", "frame": manager.frame_count}


@app.get("/api/performance/metrics/{metric_type}")
async def get_metric(metric_type: str):
    """Get statistics for a metric."""
    try:
        m_type = ProfilingMetric[metric_type]
        stats = manager.get_metric_stats(m_type)
        return {"metric": metric_type, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/performance/report")
async def get_performance_report():
    """Get comprehensive performance report."""
    return manager.get_performance_report()


# ═══════════════════════════════════════════════════════════════════════════════
# LOADING SCREEN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/loading/create")
async def create_loading_screen(
    title: str,
    description: str = "",
    total_assets: int = 0
):
    """Create a loading screen."""
    screen = manager.create_loading_screen(title, description, total_assets)
    return {"screen_id": screen.screen_id, "title": title}


@app.post("/api/loading/show/{screen_id}")
async def show_loading_screen(screen_id: str):
    """Show a loading screen."""
    result = manager.show_loading_screen(screen_id)
    if not result:
        raise HTTPException(status_code=404, detail="Screen not found")
    return {"screen_id": screen_id, "visible": True}


@app.post("/api/loading/progress/{screen_id}")
async def update_loading_progress(screen_id: str, assets_loaded: int):
    """Update loading progress."""
    progress = manager.update_loading_progress(screen_id, assets_loaded)
    
    screen = manager.loading_screens.get(screen_id)
    return {
        "screen_id": screen_id,
        "progress": progress,
        "assets_loaded": assets_loaded,
        "assets_total": screen.assets_total if screen else 0
    }


@app.post("/api/loading/hide/{screen_id}")
async def hide_loading_screen(screen_id: str):
    """Hide a loading screen."""
    result = manager.hide_loading_screen(screen_id)
    if not result:
        raise HTTPException(status_code=404, detail="Screen not found")
    return {"screen_id": screen_id, "visible": False}


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/streaming")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time streaming updates."""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif message.get("type") == "get_status":
                status = manager.to_dict()
                await websocket.send_json({"type": "status", "data": status})
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def dashboard():
    """Interactive dashboard."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Level Streaming Manager</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }
            header { background: #0d47a1; padding: 20px; text-align: center; }
            nav { display: flex; gap: 10px; padding: 10px; background: #222; }
            nav button { padding: 10px 20px; background: #0d47a1; color: white; border: none; cursor: pointer; border-radius: 4px; }
            nav button.active { background: #ff6b6b; }
            .container { max-width: 1400px; margin: 20px auto; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
            .card { background: #222; padding: 20px; border-radius: 8px; border-left: 4px solid #0d47a1; }
            .card h3 { margin-bottom: 15px; color: #ff6b6b; }
            .stat { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }
            .stat-value { font-weight: bold; color: #4caf50; }
            input, select { width: 100%; padding: 8px; margin: 8px 0; background: #333; color: white; border: 1px solid #444; border-radius: 4px; }
            button { padding: 10px 20px; background: #0d47a1; color: white; border: none; cursor: pointer; border-radius: 4px; }
            button:hover { background: #1565c0; }
            .progress-bar { width: 100%; height: 20px; background: #444; border-radius: 4px; overflow: hidden; }
            .progress-fill { height: 100%; background: linear-gradient(90deg, #4caf50, #ff6b6b); transition: width 0.3s; }
            .alert { padding: 10px; border-radius: 4px; margin: 10px 0; }
            .alert-warning { background: #f57f17; color: white; }
            .alert-critical { background: #d32f2f; color: white; }
            .memory-chart { width: 100%; height: 300px; background: #333; border-radius: 4px; margin: 20px 0; }
            h2 { color: #ff6b6b; margin-top: 20px; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <header>
            <h1>⚡ Level Streaming Manager</h1>
            <p>Real-time Level Streaming, LOD, and Performance Monitoring</p>
        </header>
        
        <nav>
            <button class="nav-btn active" onclick="showTab('overview', this)">Overview</button>
            <button class="nav-btn" onclick="showTab('volumes', this)">Volumes</button>
            <button class="nav-btn" onclick="showTab('lod', this)">LOD</button>
            <button class="nav-btn" onclick="showTab('occlusion', this)">Occlusion</button>
            <button class="nav-btn" onclick="showTab('memory', this)">Memory</button>
            <button class="nav-btn" onclick="showTab('performance', this)">Performance</button>
            <button class="nav-btn" onclick="showTab('loading', this)">Loading</button>
        </nav>
        
        <div class="container">
            
            <!-- OVERVIEW TAB -->
            <div id="overview" class="tab-content active">
                <h2>System Overview</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Streaming Status</h3>
                        <div class="stat">
                            <span>Active Volumes:</span>
                            <span class="stat-value" id="volumeCount">0</span>
                        </div>
                        <div class="stat">
                            <span>Loaded Levels:</span>
                            <span class="stat-value" id="loadedLevels">0</span>
                        </div>
                        <div class="stat">
                            <span>Frame Count:</span>
                            <span class="stat-value" id="frameCount">0</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Memory Status</h3>
                        <div class="stat">
                            <span>Total Memory:</span>
                            <span class="stat-value" id="totalMemory">0 MB</span>
                        </div>
                        <div class="stat">
                            <span>Used Memory:</span>
                            <span class="stat-value" id="usedMemory">0 MB</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="memoryBar"></div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Performance</h3>
                        <div class="stat">
                            <span>Avg Frame Time:</span>
                            <span class="stat-value" id="avgFrameTime">0 ms</span>
                        </div>
                        <div class="stat">
                            <span>Draw Calls:</span>
                            <span class="stat-value" id="drawCalls">0</span>
                        </div>
                        <div class="stat">
                            <span>Triangles:</span>
                            <span class="stat-value" id="triangles">0</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- VOLUMES TAB -->
            <div id="volumes" class="tab-content">
                <h2>Streaming Volumes</h2>
                <h3>Create Volume</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="text" id="volName" placeholder="Volume Name">
                    <input type="text" id="volPosition" placeholder="Position (x,y,z)">
                    <input type="number" id="volRadius" placeholder="Radius">
                    <input type="text" id="volLevel" placeholder="Level Name">
                    <input type="number" id="volDistance" placeholder="Load Distance">
                    <button onclick="createVolume()">Create Volume</button>
                </div>
                
                <h3>Active Volumes</h3>
                <div id="volumesList" class="grid"></div>
            </div>
            
            <!-- LOD TAB -->
            <div id="lod" class="tab-content">
                <h2>Level of Detail (LOD)</h2>
                <h3>Create LOD Settings</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="text" id="lodLevel" placeholder="Level Name">
                    <button onclick="createLOD()">Create LOD Settings</button>
                </div>
                
                <h3>Adjust LOD</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="text" id="adjustLevel" placeholder="Level Name">
                    <select id="adjustLOD">
                        <option>ULTRA</option>
                        <option>HIGH</option>
                        <option selected>MEDIUM</option>
                        <option>LOW</option>
                        <option>MINIMAL</option>
                    </select>
                    <button onclick="adjustLOD()">Adjust LOD</button>
                </div>
                
                <h3>Calculate Optimal LOD</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="number" id="distance" placeholder="Distance from Camera">
                    <input type="number" id="availMemory" placeholder="Available Memory (MB)">
                    <input type="number" id="frameTime" placeholder="Frame Time (ms)">
                    <button onclick="calculateLOD()">Calculate</button>
                    <p id="optimalLOD"></p>
                </div>
            </div>
            
            <!-- OCCLUSION TAB -->
            <div id="occlusion" class="tab-content">
                <h2>Occlusion Culling</h2>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="text" id="occLevel" placeholder="Level Name">
                    <input type="number" id="visibleActors" placeholder="Visible Actors">
                    <input type="number" id="occludedActors" placeholder="Occluded Actors">
                    <button onclick="updateOcclusion()">Update Occlusion</button>
                </div>
                <div id="occlusionStats" class="grid" style="margin-top: 20px;"></div>
            </div>
            
            <!-- MEMORY TAB -->
            <div id="memory" class="tab-content">
                <h2>Memory Budgets</h2>
                <h3>Create Budget</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="text" id="budgetName" placeholder="Budget Name">
                    <input type="number" id="budgetMemory" placeholder="Max Memory (MB)">
                    <button onclick="createBudget()">Create Budget</button>
                </div>
                
                <h3>Allocate to Budget</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="text" id="allocBudget" placeholder="Budget Name">
                    <input type="text" id="allocLevel" placeholder="Level Name">
                    <input type="number" id="allocMemory" placeholder="Memory (MB)">
                    <button onclick="allocateToBudget()">Allocate</button>
                </div>
                
                <div id="budgetsList" class="grid" style="margin-top: 20px;"></div>
            </div>
            
            <!-- PERFORMANCE TAB -->
            <div id="performance" class="tab-content">
                <h2>Performance Profiling</h2>
                <h3>Frame Profiling</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="number" id="profileFrameTime" placeholder="Frame Time (ms)">
                    <input type="number" id="profileMemory" placeholder="Memory (MB)">
                    <input type="number" id="profileDrawCalls" placeholder="Draw Calls">
                    <input type="number" id="profileTriangles" placeholder="Triangles">
                    <button onclick="profileFrame()">Record Frame</button>
                </div>
                <div id="performanceStats" class="grid" style="margin-top: 20px;"></div>
            </div>
            
            <!-- LOADING TAB -->
            <div id="loading" class="tab-content">
                <h2>Loading Screens</h2>
                <h3>Create Loading Screen</h3>
                <div style="background: #222; padding: 20px; border-radius: 8px;">
                    <input type="text" id="loadTitle" placeholder="Title">
                    <input type="text" id="loadDesc" placeholder="Description">
                    <input type="number" id="loadAssets" placeholder="Total Assets">
                    <button onclick="createLoadingScreen()">Create Screen</button>
                </div>
                <div id="loadingScreens" class="grid" style="margin-top: 20px;"></div>
            </div>
        </div>
        
        <script>
            function showTab(tabName, buttonElement) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName).classList.add('active');
                document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
                if (buttonElement) buttonElement.classList.add('active');
            }
            
            async function createVolume() {
                try {
                    const req = {
                        name: document.getElementById('volName').value,
                        position: JSON.parse('[' + document.getElementById('volPosition').value + ']'),
                        radius: parseFloat(document.getElementById('volRadius').value),
                        level_name: document.getElementById('volLevel').value,
                        load_distance: parseFloat(document.getElementById('volDistance').value)
                    };
                    const res = await fetch('/api/volumes/create', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(req),
                        signal: AbortSignal.timeout(5000)
                    });
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    alert('Volume created!');
                    loadVolumes();
                } catch (e) {
                    alert('Error creating volume: ' + e.message);
                    console.error(e);
                }
            }
            
            async function loadVolumes() {
                try {
                    const res = await fetch('/api/volumes', {signal: AbortSignal.timeout(5000)});
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    const html = data.volumes.map(v => `
                        <div class="card">
                            <h3>${v.name}</h3>
                            <div class="stat"><span>Level:</span> <span class="stat-value">${v.level_name}</span></div>
                            <div class="stat"><span>Radius:</span> <span class="stat-value">${v.radius}</span></div>
                            <div class="stat"><span>Load Distance:</span> <span class="stat-value">${v.load_distance}</span></div>
                        </div>
                    `).join('');
                    document.getElementById('volumesList').innerHTML = html || '<p>No volumes created</p>';
                } catch (e) {
                    console.warn('Load volumes failed:', e);
                    document.getElementById('volumesList').innerHTML = '<p style="color: #f57f17;">Failed to load volumes</p>';
                }
            }
            
            async function createLOD() {
                const level = document.getElementById('lodLevel').value;
                await fetch(`/api/lod/create?level_name=${level}`);
                alert('LOD settings created!');
            }
            
            async function adjustLOD() {
                try {
                    const req = {
                        level_name: document.getElementById('adjustLevel').value,
                        new_lod: document.getElementById('adjustLOD').value
                    };
                    const res = await fetch('/api/lod/adjust', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(req),
                        signal: AbortSignal.timeout(5000)
                    });
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    alert(`LOD adjusted to ${data.new_lod}`);
                } catch (e) {
                    alert('Error adjusting LOD: ' + e.message);
                }
            }
            
            async function calculateLOD() {
                try {
                    const distance = parseFloat(document.getElementById('distance').value);
                    const memory = parseFloat(document.getElementById('availMemory').value);
                    const frameTime = parseFloat(document.getElementById('frameTime').value);
                    const res = await fetch(`/api/lod/calculate?distance=${distance}&available_memory_mb=${memory}&frame_time_ms=${frameTime}`, {
                        signal: AbortSignal.timeout(5000)
                    });
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    document.getElementById('optimalLOD').textContent = `Optimal LOD: ${data.optimal_lod}`;
                } catch (e) {
                    document.getElementById('optimalLOD').textContent = `Error: ${e.message}`;
                }
            }
            
            async function createBudget() {
                try {
                    const req = {
                        budget_name: document.getElementById('budgetName').value,
                        max_memory_mb: parseFloat(document.getElementById('budgetMemory').value)
                    };
                    const res = await fetch('/api/memory/budget/create', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(req),
                        signal: AbortSignal.timeout(5000)
                    });
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    alert('Budget created!');
                    loadBudgets();
                } catch (e) {
                    alert('Error creating budget: ' + e.message);
                    console.error(e);
                }
            }
            
            async function loadBudgets() {
                try {
                    const res = await fetch('/api/memory/budgets', {signal: AbortSignal.timeout(5000)});
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    const html = data.budgets.map(b => `
                        <div class="card ${b.is_critical ? 'alert alert-critical' : b.is_warning ? 'alert alert-warning' : ''}">
                            <h3>${b.name}</h3>
                            <div class="stat"><span>Max:</span> <span class="stat-value">${b.max_mb} MB</span></div>
                            <div class="stat"><span>Used:</span> <span class="stat-value">${b.used_mb.toFixed(1)} MB</span></div>
                            <div class="stat"><span>Usage:</span> <span class="stat-value">${b.usage_pct.toFixed(1)}%</span></div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${b.usage_pct}%"></div>
                            </div>
                        </div>
                    `).join('');
                    document.getElementById('budgetsList').innerHTML = html;
                } catch (e) {
                    console.warn('Load budgets failed:', e);
                }
            }
            
            async function updateStatus() {
                try {
                    const res = await fetch('/api/memory/status', {signal: AbortSignal.timeout(5000)});
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    document.getElementById('totalMemory').textContent = data.total_memory_mb + ' MB';
                    document.getElementById('usedMemory').textContent = data.used_memory_mb.toFixed(1) + ' MB';
                    document.getElementById('memoryBar').style.width = data.usage_percentage + '%';
                } catch (e) {
                    console.warn('Memory status fetch failed:', e);
                }
                
                try {
                    const perfRes = await fetch('/api/performance/report', {signal: AbortSignal.timeout(5000)});
                    if (!perfRes.ok) throw new Error(`HTTP ${perfRes.status}`);
                    const perfData = await perfRes.json();
                    if (perfData.metrics && perfData.metrics.FRAME_TIME) {
                        document.getElementById('avgFrameTime').textContent = perfData.metrics.FRAME_TIME.average.toFixed(2) + ' ms';
                    }
                    if (perfData.metrics && perfData.metrics.DRAW_CALLS) {
                        document.getElementById('drawCalls').textContent = perfData.metrics.DRAW_CALLS.current;
                    }
                    if (perfData.metrics && perfData.metrics.TRIANGLE_COUNT) {
                        document.getElementById('triangles').textContent = perfData.metrics.TRIANGLE_COUNT.current;
                    }
                    document.getElementById('frameCount').textContent = perfData.frame_count || 0;
                } catch (e) {
                    console.warn('Performance report fetch failed:', e);
                }
                
                try {
                    await loadBudgets();
                } catch (e) {
                    console.warn('Load budgets failed:', e);
                }
            }
            
            async function profileFrame() {
                try {
                    const req = {
                        frame_time_ms: parseFloat(document.getElementById('profileFrameTime').value),
                        memory_mb: parseFloat(document.getElementById('profileMemory').value),
                        draw_calls: parseInt(document.getElementById('profileDrawCalls').value),
                        triangles: parseInt(document.getElementById('profileTriangles').value)
                    };
                    await fetch('/api/performance/profile-frame', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(req),
                        signal: AbortSignal.timeout(5000)
                    });
                    updateStatus();
                } catch (e) {
                    alert('Error recording frame: ' + e.message);
                }
            }
            
            // Initialize with error handling
            setInterval(updateStatus, 1000);
            
            // Initial load
            Promise.resolve()
                .then(() => loadVolumes()).catch(e => console.warn('Failed to load volumes:', e))
                .then(() => updateStatus()).catch(e => console.warn('Failed to update status:', e));
        </script>
    </body>
    </html>
    """)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
