"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           LEVEL STREAMING - UNREAL ENGINE INTEGRATION                       ║
║        WebSocket Bridge · Event System · C++ Header Generation              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import logging
import websockets
from typing import Callable, Dict, List
from dataclasses import dataclass
from level_streaming_manager import LevelStreamingManager, LODLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class StreamingEvent:
    """Event data for streaming changes."""
    event_type: str  # level_loaded, level_unloaded, lod_changed, memory_warning, etc
    level_name: str
    timestamp: float
    data: Dict = None


class StreamingEventSystem:
    """Central event system for broadcasting streaming changes."""
    
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}
        self.event_queue: List[StreamingEvent] = []
    
    def register_listener(self, event_type: str, callback: Callable):
        """Register callback for event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def broadcast_event(self, event: StreamingEvent):
        """Broadcast event to all listeners."""
        self.event_queue.append(event)
        if event.event_type in self.listeners:
            for callback in self.listeners[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Event callback error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# UNREAL INTEGRATION BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════

class UnrealStreamingBridge:
    """
    Bidirectional WebSocket bridge for Unreal Engine integration.
    Syncs streaming state between Python backend and Unreal client.
    """
    
    def __init__(self, streaming_manager: LevelStreamingManager, port: int = 8765):
        self.manager = streaming_manager
        self.port = port
        self.clients: List[websockets.WebSocketServerProtocol] = []
        self.event_system = StreamingEventSystem()
        
        # Register manager events
        self.manager.register_event_listener("level_loaded", self._on_level_loaded)
        self.manager.register_event_listener("level_unloaded", self._on_level_unloaded)
        self.manager.register_event_listener("lod_changed", self._on_lod_changed)
        self.manager.register_event_listener("memory_warning", self._on_memory_warning)
        self.manager.register_event_listener("performance_warning", self._on_perf_warning)
    
    async def start(self):
        """Start WebSocket server."""
        logger.info(f"Starting Unreal streaming bridge on port {self.port}")
        async with websockets.serve(self._handle_client, "0.0.0.0", self.port):
            await asyncio.Future()
    
    async def _handle_client(self, websocket, path):
        """Handle incoming Unreal client connection."""
        self.clients.append(websocket)
        logger.info(f"Unreal client connected. Total clients: {len(self.clients)}")
        
        try:
            async for message in websocket:
                await self._process_unreal_message(message, websocket)
        except websockets.exceptions.ConnectionClosed:
            self.clients.remove(websocket)
            logger.info(f"Unreal client disconnected. Remaining: {len(self.clients)}")
    
    async def _process_unreal_message(self, message: str, websocket):
        """Process message from Unreal."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "load_level":
                level_name = data.get("level_name")
                self.manager.load_level(level_name)
                await self._broadcast({"type": "level_load_requested", "level": level_name})
            
            elif msg_type == "unload_level":
                level_name = data.get("level_name")
                self.manager.unload_level(level_name)
                await self._broadcast({"type": "level_unload_requested", "level": level_name})
            
            elif msg_type == "adjust_lod":
                level_name = data.get("level_name")
                lod_name = data.get("lod")
                lod = LODLevel[lod_name]
                self.manager.adjust_lod(level_name, lod)
                await self._broadcast({
                    "type": "lod_adjusted",
                    "level": level_name,
                    "new_lod": lod_name
                })
            
            elif msg_type == "check_volumes":
                camera_pos = tuple(data.get("camera_position", (0, 0, 0)))
                changes = self.manager.check_streaming_volume(camera_pos)
                await self._broadcast({
                    "type": "volume_check_result",
                    "changes": [
                        {"level": vol.level_name, "should_load": load}
                        for vol, load in changes
                    ]
                })
            
            elif msg_type == "request_status":
                status = self.manager.to_dict()
                await websocket.send(json.dumps({
                    "type": "status_update",
                    "data": status
                }))
            
            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
        
        except Exception as e:
            logger.error(f"Error processing Unreal message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    async def _broadcast(self, data: Dict):
        """Broadcast message to all connected Unreal clients."""
        if not self.clients:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(client)
        
        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT CALLBACKS
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def _on_level_loaded(self, level_name: str):
        """Called when level is loaded."""
        await self._broadcast({
            "type": "level_loaded",
            "level": level_name,
            "state": "ACTIVE"
        })
    
    async def _on_level_unloaded(self, level_name: str):
        """Called when level is unloaded."""
        await self._broadcast({
            "type": "level_unloaded",
            "level": level_name,
            "state": "UNLOADED"
        })
    
    async def _on_lod_changed(self, level_name: str, new_lod: LODLevel):
        """Called when LOD is adjusted."""
        await self._broadcast({
            "type": "lod_changed",
            "level": level_name,
            "new_lod": new_lod.name
        })
    
    async def _on_memory_warning(self, budget_name: str, usage_pct: float):
        """Called when memory exceeds threshold."""
        await self._broadcast({
            "type": "memory_warning",
            "budget": budget_name,
            "usage_percent": usage_pct
        })
    
    async def _on_perf_warning(self, frame_time_ms: float):
        """Called when frame time exceeds threshold."""
        await self._broadcast({
            "type": "performance_warning",
            "frame_time_ms": frame_time_ms
        })


# ═══════════════════════════════════════════════════════════════════════════════
# C++ HEADER GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

class UnrealHeaderGenerator:
    """Generate C++ headers for Unreal Engine integration."""
    
    @staticmethod
    def generate_streaming_enums() -> str:
        """Generate C++ enums for streaming states."""
        return """
// Generated Level Streaming Enums
#pragma once

namespace LevelStreaming {

UENUM(BlueprintType)
enum class EStreamingState : uint8 {
    UNLOADED = 0 UMETA(DisplayName = "Unloaded"),
    LOADING = 1 UMETA(DisplayName = "Loading"),
    LOADED = 2 UMETA(DisplayName = "Loaded"),
    ACTIVE = 3 UMETA(DisplayName = "Active"),
    UNLOADING = 4 UMETA(DisplayName = "Unloading"),
    HIDDEN = 5 UMETA(DisplayName = "Hidden")
};

UENUM(BlueprintType)
enum class ELODLevel : uint8 {
    ULTRA = 0 UMETA(DisplayName = "Ultra"),
    HIGH = 1 UMETA(DisplayName = "High"),
    MEDIUM = 2 UMETA(DisplayName = "Medium"),
    LOW = 3 UMETA(DisplayName = "Low"),
    MINIMAL = 4 UMETA(DisplayName = "Minimal")
};

UENUM(BlueprintType)
enum class EMemoryPriority : uint8 {
    CRITICAL = 1 UMETA(DisplayName = "Critical"),
    HIGH = 2 UMETA(DisplayName = "High"),
    NORMAL = 3 UMETA(DisplayName = "Normal"),
    LOW = 4 UMETA(DisplayName = "Low"),
    BACKGROUND = 5 UMETA(DisplayName = "Background")
};

UENUM(BlueprintType)
enum class EOcclusionType : uint8 {
    NONE = 0 UMETA(DisplayName = "None"),
    SIMPLE = 1 UMETA(DisplayName = "Simple"),
    CONSERVATIVE = 2 UMETA(DisplayName = "Conservative"),
    AGGRESSIVE = 3 UMETA(DisplayName = "Aggressive")
};

} // namespace LevelStreaming
"""
    
    @staticmethod
    def generate_streaming_volume_header() -> str:
        """Generate streaming volume component header."""
        return """
// Generated Level Streaming Volume
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LevelStreamingEnums.h"
#include "StreamingVolume.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnVolumeLoadRequested, 
    const FString&, LevelName, bool, bShouldLoad);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_One_Param(FOnLODChanged,
    LevelStreaming::ELODLevel, NewLOD);

/**
 * Automatic streaming volume that loads/unloads levels based on camera distance
 */
UCLASS(Blueprintable, BlueprintType)
class AStreamingVolume : public AActor
{
    GENERATED_BODY()

public:
    AStreamingVolume();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;

    // Volume parameters
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    FString StreamedLevelName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    float LoadDistance = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    float UnloadDistance = 200.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    float Radius = 50.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    LevelStreaming::EMemoryPriority Priority = LevelStreaming::EMemoryPriority::NORMAL;

    // Current state
    UPROPERTY(BlueprintReadOnly, Category = "Streaming")
    LevelStreaming::EStreamingState CurrentState;

    UPROPERTY(BlueprintReadOnly, Category = "Streaming")
    LevelStreaming::ELODLevel CurrentLOD = LevelStreaming::ELODLevel::MEDIUM;

    // Events
    UPROPERTY(BlueprintAssignable, Category = "Streaming")
    FOnVolumeLoadRequested OnLoadRequested;

    UPROPERTY(BlueprintAssignable, Category = "Streaming")
    FOnLODChanged OnLODChanged;

    // Functions
    UFUNCTION(BlueprintCallable, Category = "Streaming")
    void RequestLoadLevel();

    UFUNCTION(BlueprintCallable, Category = "Streaming")
    void RequestUnloadLevel();

    UFUNCTION(BlueprintCallable, Category = "Streaming")
    void SetLOD(LevelStreaming::ELODLevel NewLOD);

    UFUNCTION(BlueprintPure, Category = "Streaming")
    float GetDistanceToCamera() const;

    UFUNCTION(BlueprintPure, Category = "Streaming")
    bool IsLevelInVolume() const;

private:
    class APawn* CachedPlayerPawn;
};
"""
    
    @staticmethod
    def generate_streaming_manager_header() -> str:
        """Generate level streaming manager component header."""
        return """
// Generated Level Streaming Manager Component
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LevelStreamingEnums.h"
#include "LevelStreamingStructs.h"
#include "WebSocketConnection.h"
#include "LevelStreamingManager.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnLevelStateChanged,
    const FString&, LevelName, LevelStreaming::EStreamingState, NewState);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnMemoryStateChanged,
    float, UsedMemory, float, TotalMemory);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_One_Param(FOnPerformanceWarning,
    float, FrameTime);

/**
 * Manager for level streaming, LOD, memory, and performance
 */
UCLASS(Blueprintable, BlueprintType)
class ALevelStreamingManager : public AActor
{
    GENERATED_BODY()

public:
    ALevelStreamingManager();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    // Configuration
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    float FrameTimeThresholdMs = 16.67f; // 60 FPS target

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    float MemoryWarningThreshold = 0.8f; // 80%

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Streaming")
    float MemoryCriticalThreshold = 0.95f; // 95%

    // Events
    UPROPERTY(BlueprintAssignable, Category = "Streaming")
    FOnLevelStateChanged OnLevelStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Streaming")
    FOnMemoryStateChanged OnMemoryStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Streaming")
    FOnPerformanceWarning OnPerformanceWarning;

    // Level Management
    UFUNCTION(BlueprintCallable, Category = "Streaming")
    void LoadLevel(const FString& LevelName);

    UFUNCTION(BlueprintCallable, Category = "Streaming")
    void UnloadLevel(const FString& LevelName);

    UFUNCTION(BlueprintCallable, Category = "Streaming")
    void SetLOD(const FString& LevelName, LevelStreaming::ELODLevel NewLOD);

    UFUNCTION(BlueprintPure, Category = "Streaming")
    LevelStreaming::EStreamingState GetLevelState(const FString& LevelName) const;

    // LOD Management
    UFUNCTION(BlueprintCallable, Category = "Streaming")
    LevelStreaming::ELODLevel CalculateOptimalLOD(
        float Distance,
        float AvailableMemory,
        float FrameTime) const;

    UFUNCTION(BlueprintPure, Category = "Streaming")
    void GetLODSettings(const FString& LevelName, 
        FLODSettings& OutSettings) const;

    // Memory Management
    UFUNCTION(BlueprintPure, Category = "Streaming")
    void GetMemoryStatus(float& OutUsedMemory, float& OutTotalMemory) const;

    UFUNCTION(BlueprintPure, Category = "Streaming")
    float GetMemoryUsagePercent() const;

    // Performance Profiling
    UFUNCTION(BlueprintCallable, Category = "Streaming")
    void RecordFrame(float FrameTime, float Memory, 
        int32 DrawCalls, int32 Triangles);

    UFUNCTION(BlueprintPure, Category = "Streaming")
    float GetAverageFrameTime() const;

    UFUNCTION(BlueprintPure, Category = "Streaming")
    FString GetPerformanceReport() const;

private:
    class FWebSocketConnection* WebSocketConnection;
    
    void ConnectToBackend();
    void DisconnectFromBackend();
    void SendToBackend(const FString& Message);
    void OnWebSocketMessage(const FString& Message);
};
"""
    
    @staticmethod
    def generate_streaming_structs_header() -> str:
        """Generate streaming data structures header."""
        return """
// Generated Level Streaming Structures
#pragma once

#include "CoreMinimal.h"
#include "LevelStreamingEnums.h"
#include "LevelStreamingStructs.generated.h"

/**
 * LOD Settings
 */
USTRUCT(BlueprintType)
struct FLODSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    LevelStreaming::ELODLevel CurrentLOD = LevelStreaming::ELODLevel::MEDIUM;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float TextureQuality = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float MeshQuality = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float DrawDistance = 5000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bEnableShadows = true;
};

/**
 * Memory Budget
 */
USTRUCT(BlueprintType)
struct FMemoryBudget
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString BudgetName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float MaxMemoryMB = 512.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float CurrentUsageMB = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    LevelStreaming::EMemoryPriority Priority = LevelStreaming::EMemoryPriority::NORMAL;
};

/**
 * Performance Metrics
 */
USTRUCT(BlueprintType)
struct FPerformanceMetrics
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly)
    float AverageFrameTime = 0.0f;

    UPROPERTY(BlueprintReadOnly)
    float MinFrameTime = 999.0f;

    UPROPERTY(BlueprintReadOnly)
    float MaxFrameTime = 0.0f;

    UPROPERTY(BlueprintReadOnly)
    float CurrentMemoryMB = 0.0f;

    UPROPERTY(BlueprintReadOnly)
    int32 DrawCalls = 0;

    UPROPERTY(BlueprintReadOnly)
    int32 TriangleCount = 0;
};
"""
    
    @staticmethod
    def generate_all_headers(output_dir: str = "Plugins/LevelStreaming/Source/LevelStreaming/Public"):
        """Generate all header files."""
        headers = {
            "LevelStreamingEnums.h": UnrealHeaderGenerator.generate_streaming_enums(),
            "StreamingVolume.h": UnrealHeaderGenerator.generate_streaming_volume_header(),
            "LevelStreamingManager.h": UnrealHeaderGenerator.generate_streaming_manager_header(),
            "LevelStreamingStructs.h": UnrealHeaderGenerator.generate_streaming_structs_header(),
        }
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for filename, content in headers.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            logger.info(f"Generated: {filepath}")
        
        return headers


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO & STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

async def run_unreal_bridge():
    """Run Unreal integration bridge."""
    manager = LevelStreamingManager()
    bridge = UnrealStreamingBridge(manager, port=8765)
    
    logger.info("═" * 80)
    logger.info("Unreal Level Streaming Bridge Started")
    logger.info("WebSocket Server: ws://localhost:8765")
    logger.info("Ready for Unreal Engine connections")
    logger.info("═" * 80)
    
    await bridge.start()


def generate_headers_for_unreal():
    """Generate all C++ headers for Unreal plugin."""
    logger.info("Generating Unreal C++ headers...")
    UnrealHeaderGenerator.generate_all_headers()
    logger.info("Headers generated successfully!")


if __name__ == "__main__":
    # Generate headers
    generate_headers_for_unreal()
    
    # Run bridge
    asyncio.run(run_unreal_bridge())
