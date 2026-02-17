"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        QUEST SYSTEM - UNREAL ENGINE INTEGRATION LAYER                       ║
║  Connects Quest Designer to Unreal Engine via HTTP/WebSockets               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import websockets
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from datetime import datetime
import uuid

from quest_mission_visual_designer import (
    AdvancedQuestSystem, Quest, Objective, Location, NPC,
    ObjectiveType, QuestStatus, Difficulty, RewardType
)


# ═══════════════════════════ EVENT SYSTEM ═════════════════════════════════════

class QuestEvent(Enum):
    """Events triggered by quest system."""
    QUEST_CREATED = "quest_created"
    QUEST_STARTED = "quest_started"
    QUEST_COMPLETED = "quest_completed"
    QUEST_FAILED = "quest_failed"
    OBJECTIVE_UPDATED = "objective_updated"
    OBJECTIVE_COMPLETED = "objective_completed"
    REWARD_GRANTED = "reward_granted"
    NPC_DIALOG = "npc_dialog"
    LOCATION_DISCOVERED = "location_discovered"
    CHAIN_PROGRESSED = "chain_progressed"


@dataclass
class QuestEventData:
    """Event data for quest system events."""
    event_type: QuestEvent
    timestamp: str
    player_id: str
    quest_id: str
    data: Dict[str, Any]
    
    def to_json(self) -> str:
        return json.dumps({
            "event": self.event_type.value,
            "timestamp": self.timestamp,
            "player_id": self.player_id,
            "quest_id": self.quest_id,
            "data": self.data
        })


# ═══════════════════════════ UNREAL ENGINE BRIDGE ══════════════════════════════

class UnrealQuestBridge:
    """
    Bidirectional bridge between Quest System and Unreal Engine.
    
    Handles:
    - HTTP requests from Unreal engine
    - WebSocket streaming for real-time updates
    - Event propagation
    - Player state synchronization
    """

    def __init__(self, quest_system: AdvancedQuestSystem, unreal_host: str = "localhost", unreal_port: int = 80):
        self.quest_system = quest_system
        self.unreal_host = unreal_host
        self.unreal_port = unreal_port
        self.websocket_clients: List[websockets.WebSocketServerProtocol] = []
        self.player_quests: Dict[str, Dict[str, Quest]] = {}  # Player ID -> Quest ID -> Quest
        self.active_events: List[QuestEventData] = []
        self.event_handlers: Dict[QuestEvent, List[Callable]] = {
            event: [] for event in QuestEvent
        }

    def subscribe_to_event(self, event_type: QuestEvent, handler: Callable):
        """Subscribe to a quest event."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    async def broadcast_event(self, event: QuestEventData):
        """Broadcast event to all connected clients."""
        self.active_events.append(event)
        event_json = event.to_json()
        
        # Call registered handlers
        for handler in self.event_handlers.get(event.event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

        # Broadcast to WebSocket clients
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send(event_json)
            except Exception:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.websocket_clients.remove(client)

    async def assign_quest_to_player(self, player_id: str, quest_id: str) -> bool:
        """Assign a quest to a player."""
        if quest_id not in self.quest_system.quests:
            return False

        if player_id not in self.player_quests:
            self.player_quests[player_id] = {}

        quest = self.quest_system.quests[quest_id]
        self.player_quests[player_id][quest_id] = quest
        quest.status = QuestStatus.ACTIVE

        # Broadcast event
        event = QuestEventData(
            event_type=QuestEvent.QUEST_STARTED,
            timestamp=datetime.utcnow().isoformat(),
            player_id=player_id,
            quest_id=quest_id,
            data={"quest_name": quest.name}
        )
        await self.broadcast_event(event)
        return True

    async def update_objective(self, player_id: str, objective_id: str, amount: int = 1) -> bool:
        """Update objective progress for a player."""
        self.quest_system.objective_tracker.update_objective(player_id, objective_id, amount)
        
        # Find which quest this objective belongs to
        for quest_id, quest in self.player_quests.get(player_id, {}).items():
            for obj in quest.objectives:
                if obj.objective_id == objective_id:
                    # Broadcast objective update
                    event = QuestEventData(
                        event_type=QuestEvent.OBJECTIVE_UPDATED,
                        timestamp=datetime.utcnow().isoformat(),
                        player_id=player_id,
                        quest_id=quest_id,
                        data={
                            "objective_id": objective_id,
                            "description": obj.description,
                            "current": obj.current_qty,
                            "required": obj.required_qty,
                            "completed": obj.completed,
                            "progress": obj.progress_pct
                        }
                    )
                    await self.broadcast_event(event)

                    # Check if quest is completed
                    if quest.all_required_complete:
                        await self.complete_quest(player_id, quest_id)
                    return True

        return False

    async def complete_quest(self, player_id: str, quest_id: str) -> Optional[Dict]:
        """Complete a quest for a player."""
        if player_id not in self.player_quests or quest_id not in self.player_quests[player_id]:
            return None

        quest = self.player_quests[player_id][quest_id]
        quest.status = QuestStatus.COMPLETED

        # Calculate rewards
        rewards_data = {}
        for reward in quest.rewards:
            reward_type = reward.reward_type.value
            value = reward.calculate_value(quest.difficulty)
            if reward_type not in rewards_data:
                rewards_data[reward_type] = 0
            rewards_data[reward_type] += value * reward.quantity

        # Broadcast quest completion
        event = QuestEventData(
            event_type=QuestEvent.QUEST_COMPLETED,
            timestamp=datetime.utcnow().isoformat(),
            player_id=player_id,
            quest_id=quest_id,
            data={
                "quest_name": quest.name,
                "rewards": rewards_data,
                "next_quest_id": quest.next_quest_id
            }
        )
        await self.broadcast_event(event)

        # Auto-start next quest in chain if exists
        if quest.next_quest_id:
            await self.assign_quest_to_player(player_id, quest.next_quest_id)

        return rewards_data

    async def send_to_unreal(self, endpoint: str, data: Dict, method: str = "POST") -> Optional[Dict]:
        """Send data to Unreal Engine."""
        url = f"http://{self.unreal_host}:{self.unreal_port}/api/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, json=data) as resp:
                        if resp.status == 200:
                            return await resp.json()
                elif method == "GET":
                    async with session.get(url, params=data) as resp:
                        if resp.status == 200:
                            return await resp.json()
        except Exception as e:
            print(f"Error sending to Unreal: {e}")
        
        return None

    async def receive_from_unreal(self, data: Dict):
        """Receive and process data from Unreal Engine."""
        action = data.get("action", "")
        player_id = data.get("player_id", "")
        
        if action == "get_quests":
            quests = list(self.player_quests.get(player_id, {}).values())
            return {"quests": [q.to_dict() for q in quests]}
        
        elif action == "assign_quest":
            quest_id = data.get("quest_id")
            success = await self.assign_quest_to_player(player_id, quest_id)
            return {"success": success}
        
        elif action == "update_objective":
            objective_id = data.get("objective_id")
            amount = data.get("amount", 1)
            success = await self.update_objective(player_id, objective_id, amount)
            return {"success": success}
        
        elif action == "complete_quest":
            quest_id = data.get("quest_id")
            rewards = await self.complete_quest(player_id, quest_id)
            return {"rewards": rewards}
        
        elif action == "get_location_quests":
            location_id = data.get("location_id")
            quests = []
            for quest in self.quest_system.quests.values():
                if quest.giver_location_id == location_id:
                    quests.append(quest.to_dict())
            return {"quests": quests}
        
        elif action == "get_npc_quests":
            npc_id = data.get("npc_id")
            if npc_id in self.quest_system.npc_system.npcs:
                npc = self.quest_system.npc_system.npcs[npc_id]
                quests = []
                for quest_id in npc.available_quests:
                    if quest_id in self.quest_system.quests:
                        quests.append(self.quest_system.quests[quest_id].to_dict())
                return {"quests": quests}
        
        return {"error": "Unknown action"}

    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections for real-time updates."""
        self.websocket_clients.append(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                response = await self.receive_from_unreal(data)
                await websocket.send(json.dumps(response))
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self.websocket_clients.remove(websocket)


# ═══════════════════════════ UNREAL C++ BINDINGS ═════════════════════════════

UNREAL_QUEST_PLUGIN_HEADER = """
// Unreal Engine Quest System Plugin Header
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Http.h"
#include "WebSocket.h"
#include "QuestTypes.generated.h"

// Quest Status Enum
UENUM(BlueprintType)
enum class EQuestStatus : uint8 {
    Locked UMETA(DisplayName = "Locked"),
    Available UMETA(DisplayName = "Available"),
    Active UMETA(DisplayName = "Active"),
    Completed UMETA(DisplayName = "Completed"),
    Failed UMETA(DisplayName = "Failed"),
    Abandoned UMETA(DisplayName = "Abandoned")
};

// Objective Type Enum
UENUM(BlueprintType)
enum class EObjectiveType : uint8 {
    Kill UMETA(DisplayName = "Kill"),
    Collect UMETA(DisplayName = "Collect"),
    Deliver UMETA(DisplayName = "Deliver"),
    Reach UMETA(DisplayName = "Reach"),
    Interact UMETA(DisplayName = "Interact"),
    Protect UMETA(DisplayName = "Protect")
};

// Quest Objective Structure
USTRUCT(BlueprintType)
struct FQuestObjective {
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString ObjectiveID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    EObjectiveType ObjectiveType;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 RequiredQuantity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 CurrentQuantity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Progress;
};

// Quest Reward Structure
USTRUCT(BlueprintType)
struct FQuestReward {
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString RewardType;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Value;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 Quantity;
};

// Quest Structure
USTRUCT(BlueprintType)
struct FQuest {
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString QuestID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Name;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    EQuestStatus Status;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FQuestObjective> Objectives;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FQuestReward> Rewards;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Progress;
};

// Quest Manager Actor
UCLASS()
class QUESTSYSTEM_API AQuestManager : public AActor {
    GENERATED_BODY()

public:
    AQuestManager();

    virtual void BeginPlay() override;

    // Blueprint callable functions
    UFUNCTION(BlueprintCallable, Category = "Quest")
    void GetPlayerQuests(const FString& PlayerID);

    UFUNCTION(BlueprintCallable, Category = "Quest")
    void AssignQuestToPlayer(const FString& PlayerID, const FString& QuestID);

    UFUNCTION(BlueprintCallable, Category = "Quest")
    void UpdateObjectiveProgress(const FString& PlayerID, const FString& ObjectiveID, int32 Amount);

    UFUNCTION(BlueprintCallable, Category = "Quest")
    void CompleteQuest(const FString& PlayerID, const FString& QuestID);

    // Event delegates
    DECLARE_EVENT_ThreeParams(AQuestManager, FOnQuestStarted, const FString&, const FString&, const FQuest&)
    FOnQuestStarted OnQuestStarted;

    DECLARE_EVENT_ThreeParams(AQuestManager, FOnObjectiveUpdated, const FString&, const FString&, const FQuestObjective&)
    FOnObjectiveUpdated OnObjectiveUpdated;

    DECLARE_EVENT_ThreeParams(AQuestManager, FOnQuestCompleted, const FString&, const FString&, const TArray<FQuestReward>&)
    FOnQuestCompleted OnQuestCompleted;

private:
    FString ServerURL;
    FString PlayerID;

    void OnQuestResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully);
    void ParseAndApplyQuestData(const FString& JsonData);
};
"""

UNREAL_QUEST_PLUGIN_CPP = """
// Unreal Engine Quest System Plugin Implementation
#include "QuestManager.h"
#include "Http.h"
#include "JsonUtilities.h"

AQuestManager::AQuestManager() {
    PrimaryActorTick.bCanEverTick = false;
    ServerURL = TEXT("http://localhost:8000/api");
}

void AQuestManager::BeginPlay() {
    Super::BeginPlay();
    
    if (ACharacter* Character = Cast<ACharacter>(GetOwner())) {
        PlayerID = Character->GetName();
    }
}

void AQuestManager::GetPlayerQuests(const FString& InPlayerID) {
    PlayerID = InPlayerID;
    
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->OnProcessRequestComplete().BindUObject(this, &AQuestManager::OnQuestResponse);
    Request->SetURL(ServerURL + TEXT("/quests"));
    Request->SetVerb(TEXT("GET"));
    Request->ProcessRequest();
}

void AQuestManager::AssignQuestToPlayer(const FString& InPlayerID, const FString& QuestID) {
    PlayerID = InPlayerID;
    
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField(TEXT("player_id"), PlayerID);
    JsonObject->SetStringField(TEXT("quest_id"), QuestID);
    JsonObject->SetStringField(TEXT("action"), TEXT("assign_quest"));
    
    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
    
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->OnProcessRequestComplete().BindUObject(this, &AQuestManager::OnQuestResponse);
    Request->SetURL(ServerURL + TEXT("/quests/assign"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(OutputString);
    Request->ProcessRequest();
}

void AQuestManager::UpdateObjectiveProgress(const FString& InPlayerID, const FString& ObjectiveID, int32 Amount) {
    PlayerID = InPlayerID;
    
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField(TEXT("player_id"), PlayerID);
    JsonObject->SetStringField(TEXT("objective_id"), ObjectiveID);
    JsonObject->SetNumberField(TEXT("amount"), Amount);
    JsonObject->SetStringField(TEXT("action"), TEXT("update_objective"));
    
    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
    
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->OnProcessRequestComplete().BindUObject(this, &AQuestManager::OnQuestResponse);
    Request->SetURL(ServerURL + TEXT("/objectives/update"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(OutputString);
    Request->ProcessRequest();
}

void AQuestManager::OnQuestResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully) {
    if (bConnectedSuccessfully && Response.IsValid()) {
        FString ResponseStr = Response->GetContentAsString();
        ParseAndApplyQuestData(ResponseStr);
    }
}

void AQuestManager::ParseAndApplyQuestData(const FString& JsonData) {
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonData);
    
    if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid()) {
        // Parse quest data and trigger events
        if (JsonObject->HasField(TEXT("event"))) {
            FString EventType = JsonObject->GetStringField(TEXT("event"));
            
            if (EventType == TEXT("quest_started")) {
                // Handle quest started event
            } else if (EventType == TEXT("objective_updated")) {
                // Handle objective update event
            } else if (EventType == TEXT("quest_completed")) {
                // Handle quest completed event
            }
        }
    }
}
"""


# ═══════════════════════════ EXAMPLE INTEGRATION ═════════════════════════════

async def integration_example():
    """Example of quest system integration with Unreal Engine."""
    
    # Initialize quest system
    quest_system = AdvancedQuestSystem()
    
    # Create bridge
    bridge = UnrealQuestBridge(quest_system)
    
    # Subscribe to events
    async def on_quest_completed(event: QuestEventData):
        print(f"Quest Completed: {event.data['quest_name']}")
        print(f"Rewards: {event.data['rewards']}")
        
        # Send to Unreal
        await bridge.send_to_unreal(
            "quest/completed",
            {
                "player_id": event.player_id,
                "quest_id": event.quest_id,
                "rewards": event.data["rewards"]
            }
        )
    
    bridge.subscribe_to_event(QuestEvent.QUEST_COMPLETED, on_quest_completed)
    
    # Create some test quests
    quest1 = quest_system.create_quest(
        name="Defeat the Goblin King",
        description="Slay the goblin king",
        difficulty=Difficulty.HARD
    )
    
    quest_system.add_objective_to_quest(
        quest1.quest_id,
        ObjectiveType.KILL,
        "Defeat Goblin King",
        required_qty=1
    )
    
    # Simulate player interaction
    player_id = "player_001"
    
    # Assign quest to player
    await bridge.assign_quest_to_player(player_id, quest1.quest_id)
    
    # Simulate objective update
    obj = quest1.objectives[0]
    await bridge.update_objective(player_id, obj.objective_id, 1)
    
    # Quest should auto-complete
    print(f"Quest Status: {quest1.status.value}")


# ═══════════════════════════ UTILITY FUNCTIONS ═════════════════════════════

def export_unreal_bindings(filepath: str = "UnrealQuestBindings.h"):
    """Export C++ bindings for Unreal Engine."""
    header = UNREAL_QUEST_PLUGIN_HEADER + "\n" + UNREAL_QUEST_PLUGIN_CPP
    with open(filepath, "w") as f:
        f.write(header)
    print(f"Exported Unreal bindings to {filepath}")


if __name__ == "__main__":
    asyncio.run(integration_example())
