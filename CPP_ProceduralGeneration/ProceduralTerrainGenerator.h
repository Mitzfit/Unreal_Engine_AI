#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Containers/Array.h"
#include "Math/Vector.h"
#include "ProceduralTerrainGenerator.generated.h"

/**
 * Terrain generation using Perlin noise and procedural algorithms
 */

UENUM(BlueprintType)
enum class EBiomeType : uint8
{
	Plains = 0,
	Forest = 1,
	Desert = 2,
	Mountain = 3,
	Tundra = 4,
	Volcanic = 5,
	Jungle = 6,
	Ocean = 7
};

USTRUCT(BlueprintType)
struct FTerrainCell
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Height = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Moisture = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Temperature = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	EBiomeType BiomeType = EBiomeType::Plains;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FString> Objects;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	bool bWalkable = true;
};

UCLASS()
class PROCEDURALADMIN_API AProceduralTerrainGenerator : public AActor
{
	GENERATED_BODY()

public:
	AProceduralTerrainGenerator();

	// Terrain generation parameters
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	int32 TerrainWidth = 256;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	int32 TerrainHeight = 256;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	float CellSize = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	float NoiseScale = 50.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	int32 NoiseOctaves = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	float NoisePersistence = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	float NoiseFrequency = 0.01f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Terrain")
	int32 RandomSeed = 12345;

	// Vegetation parameters
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Vegetation")
	float TreeDensity = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Vegetation")
	float RockDensity = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Vegetation")
	float BushDensity = 0.25f;

	virtual void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category = "Terrain Generation")
	void GenerateTerrain();

	UFUNCTION(BlueprintCallable, Category = "Terrain Generation")
	void GenerateVegetation();

	UFUNCTION(BlueprintCallable, Category = "Terrain Generation")
	float GetPerlinNoise(float X, float Y, int32 Seed) const;

	UFUNCTION(BlueprintCallable, Category = "Terrain Generation")
	EBiomeType DetermineBiome(float Height, float Moisture, float Temperature) const;

	UFUNCTION(BlueprintCallable, Category = "Terrain Generation")
	void ExportToBlender(const FString& FilePath);

	UFUNCTION(BlueprintCallable, Category = "Terrain Generation")
	void ClearTerrain();

protected:
	UPROPERTY(VisibleAnywhere, Category = "Terrain")
	TArray<FTerrainCell> TerrainGrid;

	UPROPERTY(VisibleAnywhere, Category = "Terrain")
	TArray<AActor*> VegetationActors;

	void GenerateHeightMap();
	void GenerateMoistureMap();
	void GenerateTemperatureMap();
	void PlaceVegetationObjects();
};
