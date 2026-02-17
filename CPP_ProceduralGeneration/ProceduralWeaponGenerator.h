#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Containers/Array.h"
#include "Math/Vector.h"
#include "ProceduralWeaponGenerator.generated.h"

/**
 * Procedural weapon and equipment generation
 */

UENUM(BlueprintType)
enum class EWeaponType : uint8
{
	Sword = 0,
	Bow = 1,
	Staff = 2,
	Hammer = 3,
	Spear = 4,
	Dagger = 5,
	Rifle = 6,
	Pistol = 7,
	Wand = 8,
	Axe = 9
};

UENUM(BlueprintType)
enum class EWeaponRarity : uint8
{
	Common = 0,
	Uncommon = 1,
	Rare = 2,
	Epic = 3,
	Legendary = 4
};

UENUM(BlueprintType)
enum class EElementalType : uint8
{
	Fire = 0,
	Ice = 1,
	Lightning = 2,
	Nature = 3,
	Holy = 4,
	Dark = 5,
	Pure = 6,
	Chaos = 7
};

USTRUCT(BlueprintType)
struct FWeaponStat
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Damage = 10.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float CriticalChance = 0.05f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float CriticalDamage = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float AttackSpeed = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Range = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float SpecialAbilityPower = 0.0f;
};

USTRUCT(BlueprintType)
struct FWeapon
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString WeaponId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString WeaponName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	EWeaponType Type = EWeaponType::Sword;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	EWeaponRarity Rarity = EWeaponRarity::Common;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	EElementalType Element = EElementalType::Pure;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FWeaponStat Stats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	int32 RequiredLevel = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FString> Enchantments;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Weight = 10.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	int32 GoldValue = 100;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	bool bIsUnique = false;
};

UCLASS()
class PROCEDURALADMIN_API AProceduralWeaponGenerator : public AActor
{
	GENERATED_BODY()

public:
	AProceduralWeaponGenerator();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon Generation")
	int32 RandomSeed = 999;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon Generation")
	int32 MaxEnchantments = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon Generation")
	float LegendaryChance = 0.01f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon Generation")
	float EpicChance = 0.05f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon Generation")
	float RareChance = 0.15f;

	virtual void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category = "Weapon Generation")
	FWeapon GenerateWeapon(EWeaponType Type = EWeaponType::Sword, int32 Level = 1);

	UFUNCTION(BlueprintCallable, Category = "Weapon Generation")
	FWeapon GenerateRandomWeapon(int32 Level = 1);

	UFUNCTION(BlueprintCallable, Category = "Weapon Generation")
	TArray<FWeapon> GenerateWeaponSet(int32 Count = 10, int32 Level = 1);

	UFUNCTION(BlueprintCallable, Category = "Weapon Generation")
	EWeaponRarity DetermineRarity();

	UFUNCTION(BlueprintCallable, Category = "Weapon Generation")
	void AddEnchantment(FWeapon& Weapon, EElementalType Element);

	UFUNCTION(BlueprintCallable, Category = "Weapon Generation")
	void ExportWeaponToJSON(const FWeapon& Weapon, const FString& FilePath);

	UFUNCTION(BlueprintCallable, Category = "Weapon Generation")
	void ExportWeaponSetToJSON(const TArray<FWeapon>& Weapons, const FString& FilePath);

protected:
	UPROPERTY(VisibleAnywhere, Category = "Weapon Generation")
	TArray<FWeapon> GeneratedWeapons;

	UPROPERTY(VisibleAnywhere, Category = "Weapon Generation")
	TArray<FString> EnchantmentLibrary;

	void InitializeEnchantmentLibrary();
	void CalculateWeaponStats(FWeapon& Weapon, int32 Level);
	FString GenerateWeaponName(EWeaponType Type, EWeaponRarity Rarity, EElementalType Element);
	int32 CalculateWeaponValue(const FWeapon& Weapon);
};
