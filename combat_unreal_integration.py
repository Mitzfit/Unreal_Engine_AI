"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     COMBAT SYSTEM UNREAL ENGINE INTEGRATION                                 ║
║  Real-time sync · Event broadcasting · C++ bindings · Combat simulation   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import websockets
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum

from combat_system import (
    CombatSystem, CombatEntity, DamageType, CombatSession
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════ UNREAL EVENTS ═════════════════════════════════

class UnrealCombatEvent(Enum):
    COMBAT_STARTED         = "combat_started"
    COMBAT_ENDED           = "combat_ended"
    ATTACK_EXECUTED        = "attack_executed"
    DAMAGE_TAKEN           = "damage_taken"
    STATUS_EFFECT_APPLIED  = "status_effect_applied"
    COMBO_STARTED          = "combo_started"
    COMBO_COMPLETED        = "combo_completed"
    COMBO_BROKEN           = "combo_broken"
    CRITICAL_HIT           = "critical_hit"
    ENTITY_DIED            = "entity_died"
    COOLDOWN_READY         = "cooldown_ready"
    SKILL_POINT_GAINED     = "skill_point_gained"


# ═══════════════════════════ UNREAL BRIDGE ═════════════════════════════════

class UnrealCombatBridge:
    """Bidirectional bridge for Unreal Engine combat integration."""

    def __init__(self, system: CombatSystem):
        self.system = system
        self.players_connected: Dict[str, Dict] = {}
        self.event_listeners: Dict[str, List[Callable]] = {
            event.value: [] for event in UnrealCombatEvent
        }
        self.websocket_server = None
        self.character_combat_state: Dict[str, Dict] = {}

    def register_event_listener(self, event: str, callback: Callable):
        """Register event listener."""
        if event in self.event_listeners:
            self.event_listeners[event].append(callback)

    async def broadcast_event(self, event_type: str, data: Dict, player_id: Optional[str] = None):
        """Broadcast event."""
        message = {
            "type": "event",
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Event listener error: {e}")

        logger.info(f"Combat event broadcasted: {event_type}")

    # ═══════════════════════════ COMBAT EVENTS ═════════════════════════════

    async def on_combat_started(self, session: CombatSession):
        """Called when combat starts."""
        await self.broadcast_event(
            UnrealCombatEvent.COMBAT_STARTED.value,
            {
                "session_id": session.session_id,
                "attacker": session.attacker.name,
                "defender": session.defender.name,
                "attacker_health": session.attacker.health,
                "defender_health": session.defender.health
            }
        )

    async def on_attack_executed(
        self,
        session: CombatSession,
        formula_name: str,
        hit_type: str,
        damage: float,
        is_critical: bool
    ):
        """Called when attack is executed."""
        await self.broadcast_event(
            UnrealCombatEvent.ATTACK_EXECUTED.value,
            {
                "session_id": session.session_id,
                "attacker": session.attacker.name,
                "defender": session.defender.name,
                "formula": formula_name,
                "hit_type": hit_type,
                "damage": damage,
                "critical": is_critical
            }
        )

    async def on_damage_taken(
        self,
        entity: CombatEntity,
        damage: float,
        damage_type: str
    ):
        """Called when damage is taken."""
        await self.broadcast_event(
            UnrealCombatEvent.DAMAGE_TAKEN.value,
            {
                "entity": entity.name,
                "damage": damage,
                "damage_type": damage_type,
                "health": entity.health,
                "health_pct": entity.health_pct,
                "is_alive": entity.is_alive
            }
        )

    async def on_status_effect_applied(
        self,
        entity: CombatEntity,
        effect_name: str,
        duration: float
    ):
        """Called when status effect is applied."""
        await self.broadcast_event(
            UnrealCombatEvent.STATUS_EFFECT_APPLIED.value,
            {
                "entity": entity.name,
                "effect": effect_name,
                "duration": duration,
                "active_effects": [e.to_dict() for e in entity.active_effects]
            }
        )

    async def on_combo_started(self, entity: CombatEntity, combo_name: str):
        """Called when combo starts."""
        await self.broadcast_event(
            UnrealCombatEvent.COMBO_STARTED.value,
            {
                "entity": entity.name,
                "combo": combo_name,
                "combo_count": entity.combo_counter
            }
        )

    async def on_combo_completed(
        self,
        entity: CombatEntity,
        combo_name: str,
        damage_bonus: float,
        total_damage: float
    ):
        """Called when combo completes."""
        await self.broadcast_event(
            UnrealCombatEvent.COMBO_COMPLETED.value,
            {
                "entity": entity.name,
                "combo": combo_name,
                "damage_bonus": damage_bonus,
                "total_damage": total_damage,
                "combo_count": entity.combo_counter
            }
        )

    async def on_critical_hit(
        self,
        attacker: CombatEntity,
        target: CombatEntity,
        damage: float
    ):
        """Called when critical hit occurs."""
        await self.broadcast_event(
            UnrealCombatEvent.CRITICAL_HIT.value,
            {
                "attacker": attacker.name,
                "target": target.name,
                "damage": damage,
                "target_health": target.health
            }
        )

    async def on_entity_died(self, entity: CombatEntity, killer: Optional[CombatEntity] = None):
        """Called when entity dies."""
        await self.broadcast_event(
            UnrealCombatEvent.ENTITY_DIED.value,
            {
                "entity": entity.name,
                "killer": killer.name if killer else "environment",
                "total_damage_taken": entity.max_health - entity.health
            }
        )

    # ═══════════════════════════ WEBSOCKET SERVER ═════════════════════════════

    async def start_websocket_server(self, host: str = "localhost", port: int = 8765):
        """Start WebSocket server."""
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
                        logger.info(f"Combat player connected: {player_id}")

                    elif command == "attack":
                        attacker_id = data.get("attacker_id")
                        target_id = data.get("target_id")
                        formula_id = data.get("formula_id")
                        # Process attack
                        pass

                    elif command == "get_status":
                        # Send current combat state
                        if player_id in self.character_combat_state:
                            state = self.character_combat_state[player_id]
                            await websocket.send(json.dumps({
                                "type": "status",
                                "data": state
                            }))

            except websockets.exceptions.ConnectionClosed:
                if player_id and player_id in self.players_connected:
                    del self.players_connected[player_id]
                    logger.info(f"Combat player disconnected: {player_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")

        self.websocket_server = await websockets.serve(handler, host, port)
        logger.info(f"Combat WebSocket server started on ws://{host}:{port}")

    # ═══════════════════════════ C++ HEADERS ═══════════════════════════════

    def generate_cpp_headers(self, output_dir: str = "./cpp"):
        """Generate C++ headers for Unreal."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        combat_bridge_h = """
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "WebSocketsModule.h"
#include "IWebSocket.h"
#include "CombatBridge.generated.h"

UENUM(BlueprintType)
enum class ECombatEventType : uint8 {
    CombatStarted UMETA(DisplayName = "Combat Started"),
    AttackExecuted UMETA(DisplayName = "Attack Executed"),
    DamageTaken UMETA(DisplayName = "Damage Taken"),
    StatusEffectApplied UMETA(DisplayName = "Status Effect Applied"),
    ComboStarted UMETA(DisplayName = "Combo Started"),
    ComboCompleted UMETA(DisplayName = "Combo Completed"),
    CriticalHit UMETA(DisplayName = "Critical Hit"),
    EntityDied UMETA(DisplayName = "Entity Died")
};

UENUM(BlueprintType)
enum class EDamageType : uint8 {
    Physical UMETA(DisplayName = "Physical"),
    Fire UMETA(DisplayName = "Fire"),
    Ice UMETA(DisplayName = "Ice"),
    Lightning UMETA(DisplayName = "Lightning"),
    Poison UMETA(DisplayName = "Poison")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FCombatEventDelegate, 
    ECombatEventType, EventType, const FString&, EventData);

UCLASS()
class YOURPROJECT_API ACombatBridge : public AActor {
    GENERATED_BODY()
    
public:
    UPROPERTY(BlueprintAssignable, Category = "Combat")
    FCombatEventDelegate OnCombatEvent;
    
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void ConnectToSystem(const FString& PlayerId);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void ExecuteAttack(const FString& AttackerId, const FString& TargetId, const FString& FormulaId);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void ApplyDamage(float Damage, EDamageType DamageType);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void ApplyStatusEffect(const FString& EffectId, float Duration);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void StartCombo(const FString& ComboName);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void ValidateCombo(const TArray<FString>& ExecutedMoves);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void EndCombat();
    
private:
    TSharedPtr<IWebSocket> WebSocket;
    FString CurrentPlayerId;
    
    void OnWebSocketConnected();
    void OnWebSocketClosed(int32 StatusCode, const FString& Reason, bool bWasClean);
    void OnWebSocketMessage(const FString& Message);
};
        """

        combat_entity_h = """
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CombatEntity.generated.h"

USTRUCT(BlueprintType)
struct FCombatStats {
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float Health = 100.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float MaxHealth = 100.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float Resource = 100.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float MaxResource = 100.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float AttackPower = 10.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float Armor = 0.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float Evasion = 0.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    int32 Level = 1;
};

UCLASS()
class YOURPROJECT_API UCombatComponent : public UActorComponent {
    GENERATED_BODY()
    
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    FCombatStats CombatStats;
    
    UPROPERTY(BlueprintReadOnly, Category = "Combat")
    int32 ComboCount = 0;
    
    UPROPERTY(BlueprintReadOnly, Category = "Combat")
    bool bInCombat = false;
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void TakeDamage(float Damage, FVector HitLocation);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void Heal(float Amount);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void AddStatusEffect(const FString& EffectId);
    
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void UpdateCombatState(float DeltaTime);
    
private:
    void UpdateActiveEffects(float DeltaTime);
};
        """

        damage_formula_h = """
#pragma once

#include "CoreMinimal.h"
#include "DamageFormula.generated.h"

UENUM(BlueprintType)
enum class EDamageFormula : uint8 {
    Physical UMETA(DisplayName = "Physical"),
    Magical UMETA(DisplayName = "Magical"),
    Hybrid UMETA(DisplayName = "Hybrid")
};

USTRUCT(BlueprintType)
struct FDamageCalculation {
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage")
    float BaseDamage = 10.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage")
    float StatMultiplier = 0.5f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage")
    float CriticalMultiplier = 2.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage")
    float CriticalChance = 5.0f;
    
    float CalculateDamage(
        float AttackerStat,
        float TargetArmor,
        bool bIsCritical
    ) const;
};
        """

        # Write files
        with open(f"{output_dir}/CombatBridge.h", "w") as f:
            f.write(combat_bridge_h)
        with open(f"{output_dir}/CombatEntity.h", "w") as f:
            f.write(combat_entity_h)
        with open(f"{output_dir}/DamageFormula.h", "w") as f:
            f.write(damage_formula_h)

        logger.info(f"C++ headers generated in {output_dir}/")

    def to_dict(self) -> Dict:
        return {
            "status": "active",
            "players_connected": len(self.players_connected),
            "websocket_active": self.websocket_server is not None,
            "event_types": len(self.event_listeners)
        }


def demo_unreal_bridge():
    """Demonstrate Unreal combat bridge."""
    system = CombatSystem()
    bridge = UnrealCombatBridge(system)

    # Generate C++ headers
    bridge.generate_cpp_headers()

    print("Unreal Combat Bridge Demo:")
    print(f"Bridge Status: {bridge.to_dict()}")


if __name__ == "__main__":
    demo_unreal_bridge()
