#include "ProceduralWeaponGenerator.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Math/UnrealMathUtility.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AProceduralWeaponGenerator::AProceduralWeaponGenerator()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AProceduralWeaponGenerator::BeginPlay()
{
	Super::BeginPlay();
	InitializeEnchantmentLibrary();
}

void AProceduralWeaponGenerator::InitializeEnchantmentLibrary()
{
	EnchantmentLibrary = {
		TEXT("Burning"),
		TEXT("Freezing"),
		TEXT("Shocking"),
		TEXT("Poisoned"),
		TEXT("Blessed"),
		TEXT("Cursed"),
		TEXT("Enchanted"),
		TEXT("Sharpened"),
		TEXT("Reinforced"),
		TEXT("Ethereal"),
		TEXT("Timeless"),
		TEXT("Wise"),
		TEXT("Mighty"),
		TEXT("Swift"),
		TEXT("Resilient")
	};
}

EWeaponRarity AProceduralWeaponGenerator::DetermineRarity()
{
	float Random = FMath::FRand();

	if (Random < LegendaryChance)
		return EWeaponRarity::Legendary;
	if (Random < LegendaryChance + EpicChance)
		return EWeaponRarity::Epic;
	if (Random < LegendaryChance + EpicChance + RareChance)
		return EWeaponRarity::Rare;
	if (Random < 0.4f)
		return EWeaponRarity::Uncommon;

	return EWeaponRarity::Common;
}

void AProceduralWeaponGenerator::CalculateWeaponStats(FWeapon& Weapon, int32 Level)
{
	FRandomStream RandomStream(RandomSeed + static_cast<int32>(Weapon.Type));

	float LevelMultiplier = 1.0f + (Level * 0.1f);
	float RarityMultiplier = 1.0f + (static_cast<int32>(Weapon.Rarity) * 0.3f);

	// Base damage varies by type
	switch (Weapon.Type)
	{
		case EWeaponType::Sword:
			Weapon.Stats.Damage = 25.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 1.0f;
			Weapon.Stats.Range = 200.0f;
			Weapon.Weight = 15.0f;
			break;

		case EWeaponType::Bow:
			Weapon.Stats.Damage = 20.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 1.2f;
			Weapon.Stats.Range = 1000.0f;
			Weapon.Weight = 5.0f;
			break;

		case EWeaponType::Staff:
			Weapon.Stats.Damage = 15.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.SpecialAbilityPower = 30.0f * RarityMultiplier;
			Weapon.Stats.Range = 500.0f;
			Weapon.Weight = 8.0f;
			break;

		case EWeaponType::Hammer:
			Weapon.Stats.Damage = 35.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 0.7f;
			Weapon.Stats.CriticalDamage = 2.0f;
			Weapon.Stats.Range = 150.0f;
			Weapon.Weight = 25.0f;
			break;

		case EWeaponType::Spear:
			Weapon.Stats.Damage = 22.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 1.1f;
			Weapon.Stats.Range = 300.0f;
			Weapon.Weight = 12.0f;
			break;

		case EWeaponType::Dagger:
			Weapon.Stats.Damage = 15.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 1.5f;
			Weapon.Stats.CriticalChance = 0.2f;
			Weapon.Stats.Range = 100.0f;
			Weapon.Weight = 3.0f;
			break;

		case EWeaponType::Rifle:
			Weapon.Stats.Damage = 30.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 0.9f;
			Weapon.Stats.Range = 2000.0f;
			Weapon.Weight = 7.0f;
			break;

		case EWeaponType::Pistol:
			Weapon.Stats.Damage = 18.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 1.3f;
			Weapon.Stats.Range = 800.0f;
			Weapon.Weight = 4.0f;
			break;

		case EWeaponType::Wand:
			Weapon.Stats.Damage = 12.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.SpecialAbilityPower = 40.0f * RarityMultiplier;
			Weapon.Stats.Range = 600.0f;
			Weapon.Weight = 2.0f;
			break;

		case EWeaponType::Axe:
			Weapon.Stats.Damage = 32.0f * LevelMultiplier * RarityMultiplier;
			Weapon.Stats.AttackSpeed = 0.8f;
			Weapon.Stats.Range = 180.0f;
			Weapon.Weight = 20.0f;
			break;
	}

	// Add rarity bonuses
	Weapon.Stats.CriticalChance += (static_cast<int32>(Weapon.Rarity) * 0.02f);
}

FString AProceduralWeaponGenerator::GenerateWeaponName(EWeaponType Type, EWeaponRarity Rarity, EElementalType Element)
{
	FString ElementName;
	switch (Element)
	{
		case EElementalType::Fire: ElementName = TEXT("Flaming"); break;
		case EElementalType::Ice: ElementName = TEXT("Frozen"); break;
		case EElementalType::Lightning: ElementName = TEXT("Thundering"); break;
		case EElementalType::Nature: ElementName = TEXT("Natural"); break;
		case EElementalType::Holy: ElementName = TEXT("Holy"); break;
		case EElementalType::Dark: ElementName = TEXT("Dark"); break;
		default: ElementName = TEXT(""); break;
	}

	FString TypeName;
	switch (Type)
	{
		case EWeaponType::Sword: TypeName = TEXT("Sword"); break;
		case EWeaponType::Bow: TypeName = TEXT("Bow"); break;
		case EWeaponType::Staff: TypeName = TEXT("Staff"); break;
		case EWeaponType::Hammer: TypeName = TEXT("Hammer"); break;
		case EWeaponType::Spear: TypeName = TEXT("Spear"); break;
		case EWeaponType::Dagger: TypeName = TEXT("Dagger"); break;
		case EWeaponType::Rifle: TypeName = TEXT("Rifle"); break;
		case EWeaponType::Pistol: TypeName = TEXT("Pistol"); break;
		case EWeaponType::Wand: TypeName = TEXT("Wand"); break;
		case EWeaponType::Axe: TypeName = TEXT("Axe"); break;
	}

	FString RarityPrefix;
	switch (Rarity)
	{
		case EWeaponRarity::Legendary: RarityPrefix = TEXT("Legendary "); break;
		case EWeaponRarity::Epic: RarityPrefix = TEXT("Epic "); break;
		case EWeaponRarity::Rare: RarityPrefix = TEXT("Rare "); break;
		case EWeaponRarity::Uncommon: RarityPrefix = TEXT(""); break;
		default: RarityPrefix = TEXT(""); break;
	}

	return RarityPrefix + ElementName + TEXT(" ") + TypeName;
}

FWeapon AProceduralWeaponGenerator::GenerateWeapon(EWeaponType Type, int32 Level)
{
	FWeapon Weapon;
	Weapon.WeaponId = FString::Printf(TEXT("WPN_%d"), FMath::Rand());
	Weapon.Type = Type;
	Weapon.Rarity = DetermineRarity();
	Weapon.RequiredLevel = Level;

	// Random element
	Weapon.Element = static_cast<EElementalType>(FMath::RandRange(0, 7));

	// Generate name
	Weapon.WeaponName = GenerateWeaponName(Type, Weapon.Rarity, Weapon.Element);

	// Calculate stats
	CalculateWeaponStats(Weapon, Level);

	// Add enchantments based on rarity
	int32 NumEnchantments = 0;
	switch (Weapon.Rarity)
	{
		case EWeaponRarity::Legendary: NumEnchantments = 4; break;
		case EWeaponRarity::Epic: NumEnchantments = 3; break;
		case EWeaponRarity::Rare: NumEnchantments = 2; break;
		case EWeaponRarity::Uncommon: NumEnchantments = 1; break;
		default: NumEnchantments = 0; break;
	}

	for (int32 i = 0; i < NumEnchantments && i < MaxEnchantments; i++)
	{
		AddEnchantment(Weapon, Weapon.Element);
	}

	// Calculate value
	Weapon.GoldValue = CalculateWeaponValue(Weapon);

	return Weapon;
}

FWeapon AProceduralWeaponGenerator::GenerateRandomWeapon(int32 Level)
{
	EWeaponType RandomType = static_cast<EWeaponType>(FMath::RandRange(0, 9));
	return GenerateWeapon(RandomType, Level);
}

TArray<FWeapon> AProceduralWeaponGenerator::GenerateWeaponSet(int32 Count, int32 Level)
{
	TArray<FWeapon> WeaponSet;

	for (int32 i = 0; i < Count; i++)
	{
		FWeapon NewWeapon = GenerateRandomWeapon(Level);
		WeaponSet.Add(NewWeapon);
		GeneratedWeapons.Add(NewWeapon);
	}

	return WeaponSet;
}

void AProceduralWeaponGenerator::AddEnchantment(FWeapon& Weapon, EElementalType Element)
{
	if (Weapon.Enchantments.Num() >= MaxEnchantments)
		return;

	int32 RandomIndex = FMath::RandRange(0, EnchantmentLibrary.Num() - 1);
	if (RandomIndex >= 0 && RandomIndex < EnchantmentLibrary.Num())
	{
		Weapon.Enchantments.Add(EnchantmentLibrary[RandomIndex]);
	}
}

int32 AProceduralWeaponGenerator::CalculateWeaponValue(const FWeapon& Weapon)
{
	int32 BaseValue = 100;
	int32 RarityValue = static_cast<int32>(Weapon.Rarity) * 200;
	int32 StatsValue = static_cast<int32>(Weapon.Stats.Damage * 5);
	int32 EnchantmentValue = Weapon.Enchantments.Num() * 150;

	return BaseValue + RarityValue + StatsValue + EnchantmentValue;
}

void AProceduralWeaponGenerator::ExportWeaponToJSON(const FWeapon& Weapon, const FString& FilePath)
{
	TSharedPtr<FJsonObject> WeaponObject = MakeShareable(new FJsonObject());

	WeaponObject->SetStringField(TEXT("id"), Weapon.WeaponId);
	WeaponObject->SetStringField(TEXT("name"), Weapon.WeaponName);
	WeaponObject->SetStringField(TEXT("type"), *UEnum::GetValueAsString(Weapon.Type));
	WeaponObject->SetStringField(TEXT("rarity"), *UEnum::GetValueAsString(Weapon.Rarity));
	WeaponObject->SetStringField(TEXT("element"), *UEnum::GetValueAsString(Weapon.Element));

	TSharedPtr<FJsonObject> StatsObject = MakeShareable(new FJsonObject());
	StatsObject->SetNumberField(TEXT("damage"), Weapon.Stats.Damage);
	StatsObject->SetNumberField(TEXT("critical_chance"), Weapon.Stats.CriticalChance);
	StatsObject->SetNumberField(TEXT("attack_speed"), Weapon.Stats.AttackSpeed);
	StatsObject->SetNumberField(TEXT("range"), Weapon.Stats.Range);
	WeaponObject->SetObjectField(TEXT("stats"), StatsObject);

	WeaponObject->SetNumberField(TEXT("required_level"), Weapon.RequiredLevel);
	WeaponObject->SetNumberField(TEXT("weight"), Weapon.Weight);
	WeaponObject->SetNumberField(TEXT("value"), Weapon.GoldValue);

	TArray<TSharedPtr<FJsonValue>> EnchantmentsArray;
	for (const FString& Ench : Weapon.Enchantments)
	{
		EnchantmentsArray.Add(MakeShareable(new FJsonValueString(Ench)));
	}
	WeaponObject->SetArrayField(TEXT("enchantments"), EnchantmentsArray);

	FString JsonString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(WeaponObject.ToSharedRef(), Writer);

	FFileHelper::SaveStringToFile(JsonString, *FilePath);
	UE_LOG(LogTemp, Warning, TEXT("Weapon exported to: %s"), *FilePath);
}

void AProceduralWeaponGenerator::ExportWeaponSetToJSON(const TArray<FWeapon>& Weapons, const FString& FilePath)
{
	TSharedPtr<FJsonObject> RootObject = MakeShareable(new FJsonObject());

	TArray<TSharedPtr<FJsonValue>> WeaponsArray;
	for (const FWeapon& Weapon : Weapons)
	{
		TSharedPtr<FJsonObject> WeaponObject = MakeShareable(new FJsonObject());
		WeaponObject->SetStringField(TEXT("id"), Weapon.WeaponId);
		WeaponObject->SetStringField(TEXT("name"), Weapon.WeaponName);
		WeaponObject->SetNumberField(TEXT("damage"), Weapon.Stats.Damage);
		WeaponObject->SetNumberField(TEXT("value"), Weapon.GoldValue);

		WeaponsArray.Add(MakeShareable(new FJsonValueObject(WeaponObject)));
	}

	RootObject->SetArrayField(TEXT("weapons"), WeaponsArray);
	RootObject->SetNumberField(TEXT("total_weapons"), Weapons.Num());

	FString JsonString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(RootObject.ToSharedRef(), Writer);

	FFileHelper::SaveStringToFile(JsonString, *FilePath);
	UE_LOG(LogTemp, Warning, TEXT("Weapon set exported to: %s"), *FilePath);
}
