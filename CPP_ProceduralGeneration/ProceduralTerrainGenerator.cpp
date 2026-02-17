#include "ProceduralTerrainGenerator.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/StaticMeshActor.h"
#include "Math/UnrealMathUtility.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AProceduralTerrainGenerator::AProceduralTerrainGenerator()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AProceduralTerrainGenerator::BeginPlay()
{
	Super::BeginPlay();
}

void AProceduralTerrainGenerator::GenerateTerrain()
{
	TerrainGrid.Empty();
	TerrainGrid.Reserve(TerrainWidth * TerrainHeight);

	FRandomStream RandomStream(RandomSeed);

	// Generate height map
	GenerateHeightMap();
	GenerateMoistureMap();
	GenerateTemperatureMap();

	// Fill terrain grid
	for (int32 X = 0; X < TerrainWidth; X++)
	{
		for (int32 Y = 0; Y < TerrainHeight; Y++)
		{
			FTerrainCell Cell;
			Cell.Height = GetPerlinNoise(X, Y, RandomSeed);
			Cell.Moisture = FMath::FRand();
			Cell.Temperature = FMath::Clamp(0.5f + (Cell.Height * 0.5f), 0.0f, 1.0f);
			Cell.BiomeType = DetermineBiome(Cell.Height, Cell.Moisture, Cell.Temperature);
			Cell.bWalkable = Cell.Height > -0.3f;

			TerrainGrid.Add(Cell);
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("Terrain generated: %d x %d cells"), TerrainWidth, TerrainHeight);
}

void AProceduralTerrainGenerator::GenerateHeightMap()
{
	// Perlin noise-based height generation
	for (int32 i = 0; i < TerrainGrid.Num(); i++)
	{
		TerrainGrid[i].Height = FMath::FRand() * 2.0f - 1.0f;
	}
}

void AProceduralTerrainGenerator::GenerateMoistureMap()
{
	// Moisture decreases with height
	for (int32 i = 0; i < TerrainGrid.Num(); i++)
	{
		TerrainGrid[i].Moisture = FMath::Max(0.0f, 1.0f - (TerrainGrid[i].Height * 0.5f));
	}
}

void AProceduralTerrainGenerator::GenerateTemperatureMap()
{
	// Temperature correlates with height and latitude
	for (int32 i = 0; i < TerrainGrid.Num(); i++)
	{
		float LatitudeFactor = static_cast<float>(i / TerrainHeight) / TerrainHeight;
		TerrainGrid[i].Temperature = 0.5f + (TerrainGrid[i].Height * 0.3f) - (LatitudeFactor * 0.4f);
		TerrainGrid[i].Temperature = FMath::Clamp(TerrainGrid[i].Temperature, 0.0f, 1.0f);
	}
}

float AProceduralTerrainGenerator::GetPerlinNoise(float X, float Y, int32 Seed) const
{
	// Simplified Perlin noise implementation
	FRandomStream Random(Seed + static_cast<int32>(X + Y * 1000));
	float Value = 0.0f;
	float Amplitude = 1.0f;
	float Frequency = 1.0f;
	float MaxValue = 0.0f;

	for (int32 i = 0; i < NoiseOctaves; i++)
	{
		Value += Random.FRand() * Amplitude;
		MaxValue += Amplitude;
		Amplitude *= NoisePersistence;
		Frequency *= 2.0f;
	}

	return Value / MaxValue;
}

EBiomeType AProceduralTerrainGenerator::DetermineBiome(float Height, float Moisture, float Temperature) const
{
	if (Height < -0.3f)
		return EBiomeType::Ocean;

	if (Height > 0.7f)
		return EBiomeType::Mountain;

	if (Temperature < 0.2f)
		return EBiomeType::Tundra;

	if (Temperature > 0.8f && Moisture > 0.6f)
		return EBiomeType::Jungle;

	if (Temperature > 0.8f && Moisture < 0.3f)
		return EBiomeType::Desert;

	if (Height > 0.4f && Moisture > 0.5f)
		return EBiomeType::Forest;

	if (Temperature > 0.6f && Height > 0.5f)
		return EBiomeType::Volcanic;

	return EBiomeType::Plains;
}

void AProceduralTerrainGenerator::GenerateVegetation()
{
	ClearTerrain();

	FRandomStream RandomStream(RandomSeed);

	for (int32 i = 0; i < TerrainGrid.Num(); i++)
	{
		FTerrainCell& Cell = TerrainGrid[i];
		
		if (!Cell.bWalkable) continue;

		int32 CellX = i % TerrainWidth;
		int32 CellY = i / TerrainWidth;
		FVector Location = FVector(CellX * CellSize, CellY * CellSize, Cell.Height * 1000.0f);

		// Place trees based on biome and density
		if (Cell.BiomeType == EBiomeType::Forest || Cell.BiomeType == EBiomeType::Jungle)
		{
			if (RandomStream.FRand() < TreeDensity)
			{
				Cell.Objects.Add(TEXT("tree"));
			}
		}

		// Place rocks
		if (RandomStream.FRand() < RockDensity)
		{
			Cell.Objects.Add(TEXT("rock"));
		}

		// Place bushes
		if (RandomStream.FRand() < BushDensity)
		{
			Cell.Objects.Add(TEXT("bush"));
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("Vegetation generated"));
}

void AProceduralTerrainGenerator::ExportToBlender(const FString& FilePath)
{
	// Create JSON export for Blender
	TSharedPtr<FJsonObject> RootObject = MakeShareable(new FJsonObject());
	
	TArray<TSharedPtr<FJsonValue>> TerrainArray;

	for (const FTerrainCell& Cell : TerrainGrid)
	{
		TSharedPtr<FJsonObject> CellObject = MakeShareable(new FJsonObject());
		CellObject->SetNumberField(TEXT("height"), Cell.Height);
		CellObject->SetNumberField(TEXT("moisture"), Cell.Moisture);
		CellObject->SetNumberField(TEXT("temperature"), Cell.Temperature);
		CellObject->SetStringField(TEXT("biome"), *UEnum::GetValueAsString(Cell.BiomeType));
		
		TArray<TSharedPtr<FJsonValue>> ObjectsArray;
		for (const FString& Obj : Cell.Objects)
		{
			ObjectsArray.Add(MakeShareable(new FJsonValueString(Obj)));
		}
		CellObject->SetArrayField(TEXT("objects"), ObjectsArray);

		TerrainArray.Add(MakeShareable(new FJsonValueObject(CellObject)));
	}

	RootObject->SetArrayField(TEXT("terrain"), TerrainArray);
	RootObject->SetNumberField(TEXT("width"), TerrainWidth);
	RootObject->SetNumberField(TEXT("height"), TerrainHeight);

	FString JsonString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(RootObject.ToSharedRef(), Writer);

	// Write to file
	FFileHelper::SaveStringToFile(JsonString, *FilePath);
	UE_LOG(LogTemp, Warning, TEXT("Terrain exported to: %s"), *FilePath);
}

void AProceduralTerrainGenerator::ClearTerrain()
{
	for (AActor* Actor : VegetationActors)
	{
		if (Actor)
		{
			Actor->Destroy();
		}
	}
	VegetationActors.Empty();
}
