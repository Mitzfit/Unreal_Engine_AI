"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     INVENTORY & CRAFTING UNREAL ENGINE INTEGRATION                          ║
║  Bidirectional sync · Event streaming · C++ bindings · WebSocket bridge     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import websockets
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import asdict
from enum import Enum

from inventory_crafting_system import (
    AdvancedInventorySystem, Item, PlayerInventory, ItemType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════ UNREAL EVENT TYPES ═════════════════════════════

class UnrealInventoryEvent(Enum):
    INVENTORY_OPENED     = "inventory_opened"
    INVENTORY_CLOSED     = "inventory_closed"
    ITEM_ADDED           = "item_added"
    ITEM_REMOVED         = "item_removed"
    ITEM_USED            = "item_used"
    ITEM_EQUIPPED        = "item_equipped"
    ITEM_UNEQUIPPED      = "item_unequipped"
    INVENTORY_FULL       = "inventory_full"
    DURABILITY_LOW       = "durability_low"
    DURABILITY_BROKEN    = "durability_broken"


class UnrealCraftingEvent(Enum):
    CRAFTING_STARTED     = "crafting_started"
    CRAFTING_PROGRESS    = "crafting_progress"
    CRAFTING_COMPLETED   = "crafting_completed"
    CRAFTING_FAILED      = "crafting_failed"
    RECIPE_UNLOCKED      = "recipe_unlocked"


class UnrealTradingEvent(Enum):
    TRADE_OFFERED        = "trade_offered"
    TRADE_ACCEPTED       = "trade_accepted"
    TRADE_REJECTED       = "trade_rejected"
    TRADE_COMPLETED      = "trade_completed"


# ═══════════════════════════ UNREAL BRIDGE ═════════════════════════════════

class UnrealInventoryBridge:
    """Bidirectional bridge between Python inventory system and Unreal Engine."""

    def __init__(self, system: AdvancedInventorySystem):
        self.system = system
        self.players_connected: Dict[str, Dict] = {}
        self.event_listeners: Dict[str, List[Callable]] = {
            event.value: [] for event in list(UnrealInventoryEvent) + 
                                         list(UnrealCraftingEvent) + 
                                         list(UnrealTradingEvent)
        }
        self.websocket_server = None

    def register_event_listener(self, event: str, callback: Callable):
        """Register listener for event."""
        if event in self.event_listeners:
            self.event_listeners[event].append(callback)

    async def broadcast_event(self, event_type: str, data: Dict, player_id: Optional[str] = None):
        """Broadcast event to connected players."""
        message = {
            "type": "event",
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        # Call registered listeners
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error calling event listener: {e}")

        logger.info(f"Event broadcasted: {event_type}")

    # ═══════════════════════════ INVENTORY EVENTS ═════════════════════════════

    async def on_inventory_opened(self, player_id: str):
        """Called when player opens inventory."""
        inventory = self.system.get_player_inventory(player_id)
        if inventory:
            await self.broadcast_event(
                UnrealInventoryEvent.INVENTORY_OPENED.value,
                {
                    "player_id": player_id,
                    "inventory": inventory.to_dict()
                },
                player_id
            )

    async def on_item_added(self, player_id: str, item_id: str, quantity: int):
        """Called when item is added to inventory."""
        inventory = self.system.get_player_inventory(player_id)
        item = self.system.item_db.get_item(item_id)
        
        if inventory and item:
            await self.broadcast_event(
                UnrealInventoryEvent.ITEM_ADDED.value,
                {
                    "player_id": player_id,
                    "item": item.to_dict(),
                    "quantity": quantity,
                    "inventory": inventory.to_dict()
                },
                player_id
            )

    async def on_item_equipped(self, player_id: str, item_id: str):
        """Called when item is equipped."""
        inventory = self.system.get_player_inventory(player_id)
        item = self.system.item_db.get_item(item_id)
        
        if inventory and item:
            stats = inventory.get_equipped_stats()
            await self.broadcast_event(
                UnrealInventoryEvent.ITEM_EQUIPPED.value,
                {
                    "player_id": player_id,
                    "item": item.to_dict(),
                    "equipment_slot": str(item.equipment_slot.value) if item.equipment_slot else None,
                    "character_stats": {s.value: v for s, v in stats.items()}
                },
                player_id
            )

    async def on_durability_low(self, player_id: str, item_id: str):
        """Called when item durability is low."""
        item = self.system.item_db.get_item(item_id)
        if item:
            await self.broadcast_event(
                UnrealInventoryEvent.DURABILITY_LOW.value,
                {
                    "player_id": player_id,
                    "item": item.to_dict(),
                    "durability_pct": item.durability_pct
                },
                player_id
            )

    async def on_inventory_full(self, player_id: str):
        """Called when inventory becomes full."""
        inventory = self.system.get_player_inventory(player_id)
        if inventory:
            await self.broadcast_event(
                UnrealInventoryEvent.INVENTORY_FULL.value,
                {
                    "player_id": player_id,
                    "slots_used": inventory.used_slots,
                    "slots_max": inventory.max_slots,
                    "weight": inventory.total_weight,
                    "weight_max": inventory.max_weight
                },
                player_id
            )

    # ═══════════════════════════ CRAFTING EVENTS ═════════════════════════════

    async def on_crafting_started(self, player_id: str, job_id: str, recipe_id: str):
        """Called when crafting job starts."""
        recipe = self.system.crafting_system.recipes.get(recipe_id)
        job = self.system.crafting_system.crafting_jobs.get(job_id)
        
        if recipe and job:
            await self.broadcast_event(
                UnrealCraftingEvent.CRAFTING_STARTED.value,
                {
                    "player_id": player_id,
                    "job_id": job_id,
                    "recipe": recipe.to_dict(),
                    "job": job.to_dict()
                },
                player_id
            )

    async def on_crafting_progress(self, player_id: str, job_id: str, progress_pct: float):
        """Called periodically during crafting."""
        job = self.system.crafting_system.crafting_jobs.get(job_id)
        if job:
            await self.broadcast_event(
                UnrealCraftingEvent.CRAFTING_PROGRESS.value,
                {
                    "player_id": player_id,
                    "job_id": job_id,
                    "progress": progress_pct,
                    "time_remaining": max(0, job.duration - int(job.progress_pct * job.duration / 100))
                },
                player_id
            )

    async def on_crafting_completed(self, player_id: str, job_id: str, result_item_id: str):
        """Called when crafting completes."""
        job = self.system.crafting_system.crafting_jobs.get(job_id)
        result_item = self.system.item_db.get_item(result_item_id)
        inventory = self.system.get_player_inventory(player_id)
        
        if job and result_item and inventory:
            await self.broadcast_event(
                UnrealCraftingEvent.CRAFTING_COMPLETED.value,
                {
                    "player_id": player_id,
                    "job_id": job_id,
                    "result_item": result_item.to_dict(),
                    "quality_tier": job.quality_tier,
                    "was_successful": job.was_successful,
                    "inventory": inventory.to_dict()
                },
                player_id
            )

    async def on_crafting_failed(self, player_id: str, job_id: str, reason: str):
        """Called when crafting fails."""
        await self.broadcast_event(
            UnrealCraftingEvent.CRAFTING_FAILED.value,
            {
                "player_id": player_id,
                "job_id": job_id,
                "reason": reason
            },
            player_id
        )

    # ═══════════════════════════ TRADING EVENTS ═════════════════════════════

    async def on_trade_completed(self, buyer_id: str, seller_id: str, offer_id: str):
        """Called when trade completes."""
        buyer_inv = self.system.get_player_inventory(buyer_id)
        seller_inv = self.system.get_player_inventory(seller_id)
        
        if buyer_inv and seller_inv:
            await self.broadcast_event(
                UnrealTradingEvent.TRADE_COMPLETED.value,
                {
                    "buyer_id": buyer_id,
                    "seller_id": seller_id,
                    "offer_id": offer_id,
                    "buyer_inventory": buyer_inv.to_dict(),
                    "seller_inventory": seller_inv.to_dict()
                }
            )

    # ═══════════════════════════ WEBSOCKET SERVER ═════════════════════════════

    async def start_websocket_server(self, host: str = "localhost", port: int = 8765):
        """Start WebSocket server for Unreal connections."""
        async def handler(websocket, path):
            player_id = None
            try:
                async for message in websocket:
                    data = json.loads(message)
                    command = data.get("command")
                    
                    if command == "connect":
                        player_id = data.get("player_id")
                        self.players_connected[player_id] = {
                            "websocket": websocket,
                            "connected_at": datetime.utcnow().isoformat()
                        }
                        logger.info(f"Player connected: {player_id}")
                        
                        # Send inventory data
                        inv = self.system.get_player_inventory(player_id)
                        if inv:
                            await websocket.send(json.dumps({
                                "type": "inventory",
                                "data": inv.to_dict()
                            }))
                    
                    elif command == "get_inventory" and player_id:
                        inv = self.system.get_player_inventory(player_id)
                        if inv:
                            await websocket.send(json.dumps({
                                "type": "inventory",
                                "data": inv.to_dict()
                            }))
                    
                    elif command == "get_recipes" and player_id:
                        level = data.get("level", 1)
                        skill = data.get("skill", 1)
                        recipes = self.system.crafting_system.get_available_recipes(level, skill)
                        await websocket.send(json.dumps({
                            "type": "recipes",
                            "data": [r.to_dict() for r in recipes]
                        }))
            
            except websockets.exceptions.ConnectionClosed:
                if player_id and player_id in self.players_connected:
                    del self.players_connected[player_id]
                    logger.info(f"Player disconnected: {player_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")

        self.websocket_server = await websockets.serve(handler, host, port)
        logger.info(f"WebSocket server started on ws://{host}:{port}")

    # ═══════════════════════════ C++ BINDING HEADERS ═══════════════════════════

    def generate_cpp_headers(self, output_dir: str = "./cpp"):
        """Generate C++ header files for Unreal integration."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # InventoryBridge.h
        inventory_bridge_h = """
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "WebSocketsModule.h"
#include "IWebSocket.h"
#include "InventoryBridge.generated.h"

UENUM(BlueprintType)
enum class EInventoryEventType : uint8 {
    InventoryOpened UMETA(DisplayName = "Inventory Opened"),
    InventoryFull UMETA(DisplayName = "Inventory Full"),
    ItemAdded UMETA(DisplayName = "Item Added"),
    ItemRemoved UMETA(DisplayName = "Item Removed"),
    ItemEquipped UMETA(DisplayName = "Item Equipped"),
    ItemUnequipped UMETA(DisplayName = "Item Unequipped"),
    DurabilityLow UMETA(DisplayName = "Durability Low"),
    CraftingStarted UMETA(DisplayName = "Crafting Started"),
    CraftingCompleted UMETA(DisplayName = "Crafting Completed"),
    TradeCompleted UMETA(DisplayName = "Trade Completed")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FInventoryEventDelegate, 
    EInventoryEventType, EventType, const FString&, EventData);

UCLASS()
class YOURPROJECT_API AInventoryBridge : public AActor {
    GENERATED_BODY()
    
public:
    UPROPERTY(BlueprintAssignable, Category = "Inventory")
    FInventoryEventDelegate OnInventoryEvent;
    
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void ConnectToSystem(const FString& PlayerId);
    
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void GetInventory();
    
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void GetAvailableRecipes(int32 PlayerLevel, int32 PlayerSkill);
    
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void StartCrafting(const FString& RecipeId);
    
private:
    TSharedPtr<IWebSocket> WebSocket;
    FString CurrentPlayerId;
    
    void OnWebSocketConnected();
    void OnWebSocketClosed(int32 StatusCode, const FString& Reason, bool bWasClean);
    void OnWebSocketMessage(const FString& Message);
    void OnWebSocketError(const FString& Error);
};
        """

        # InventoryItem.h
        inventory_item_h = """
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "InventoryItem.generated.h"

UENUM(BlueprintType)
enum class EItemRarity : uint8 {
    Common UMETA(DisplayName = "Common"),
    Uncommon UMETA(DisplayName = "Uncommon"),
    Rare UMETA(DisplayName = "Rare"),
    Epic UMETA(DisplayName = "Epic"),
    Legendary UMETA(DisplayName = "Legendary"),
    Mythic UMETA(DisplayName = "Mythic")
};

UENUM(BlueprintType)
enum class EEquipmentSlot : uint8 {
    Head, Neck, Chest, Back, Hands, Waist, Legs, Feet,
    FingerLeft, FingerRight, MainHand, OffHand, TwoHand
};

USTRUCT(BlueprintType)
struct FGameItem {
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    FString ItemId;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    FString ItemName;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    FString Description;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    EItemRarity Rarity;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    float Weight;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    int32 Value;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    float Durability;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
    float MaxDurability;
};

UCLASS()
class YOURPROJECT_API AGameInventory : public AActor {
    GENERATED_BODY()
    
public:
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void AddItem(const FGameItem& Item, int32 Quantity = 1);
    
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void RemoveItem(const FString& ItemId, int32 Quantity = 1);
    
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void EquipItem(const FString& ItemId, EEquipmentSlot Slot);
    
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void UnequipItem(EEquipmentSlot Slot);
    
private:
    UPROPERTY()
    TArray<FGameItem> InventoryItems;
    
    UPROPERTY()
    TMap<EEquipmentSlot, FGameItem> EquippedItems;
};
        """

        # Write files
        with open(f"{output_dir}/InventoryBridge.h", "w") as f:
            f.write(inventory_bridge_h)
        
        with open(f"{output_dir}/InventoryItem.h", "w") as f:
            f.write(inventory_item_h)

        logger.info(f"C++ headers generated in {output_dir}/")

    def to_dict(self) -> Dict:
        """Get bridge status."""
        return {
            "status": "active",
            "players_connected": len(self.players_connected),
            "websocket_server": self.websocket_server is not None,
            "event_listeners": {
                event: len(listeners)
                for event, listeners in self.event_listeners.items()
            }
        }


# ═══════════════════════════ UNREAL ADAPTER ════════════════════════════════

class UnrealInventoryAdapter:
    """High-level adapter for Unreal-specific operations."""

    def __init__(self, bridge: UnrealInventoryBridge):
        self.bridge = bridge

    async def player_use_item(self, player_id: str, item_id: str):
        """Handle player using an item."""
        inventory = self.bridge.system.get_player_inventory(player_id)
        if inventory:
            inventory.remove_item(item_id, 1)
            await self.bridge.broadcast_event(
                UnrealInventoryEvent.ITEM_USED.value,
                {
                    "player_id": player_id,
                    "item_id": item_id
                }
            )

    async def player_damaged_item(self, player_id: str, item_id: str, damage: float):
        """Handle item durability damage."""
        inventory = self.bridge.system.get_player_inventory(player_id)
        if inventory:
            for slot, item in inventory.equipment.items():
                if item.item_id == item_id:
                    item.damage_durability(damage)
                    
                    if item.durability_pct <= 0:
                        await self.bridge.on_durability_low(player_id, item_id)
                    
                    break

    async def get_item_by_name(self, name: str) -> Optional[Item]:
        """Get item from database by name."""
        for item in self.bridge.system.item_db.items.values():
            if item.name.lower() == name.lower():
                return item
        return None

    async def get_character_level(self, player_id: str) -> int:
        """Get character level from player data."""
        # This would integrate with your actual character system
        return 1

    def to_dict(self) -> Dict:
        return {
            "type": "UnrealInventoryAdapter",
            "bridge_status": self.bridge.to_dict()
        }


def demo_unreal_bridge():
    """Demonstrate Unreal bridge functionality."""
    system = AdvancedInventorySystem()
    bridge = UnrealInventoryBridge(system)
    
    # Create test inventory
    system.create_player_inventory("unreal_player_1", 24)
    
    # Register event listeners
    def on_item_added(event):
        print(f"Event received: {event['event']}")
    
    bridge.register_event_listener(
        UnrealInventoryEvent.ITEM_ADDED.value,
        on_item_added
    )
    
    # Generate C++ headers
    bridge.generate_cpp_headers()
    
    print("Unreal Bridge Demo:")
    print(f"Bridge Status: {bridge.to_dict()}")


if __name__ == "__main__":
    demo_unreal_bridge()
