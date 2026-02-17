#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Containers/Array.h"
#include "Math/Vector.h"
#include "ProceduralCityGenerator.generated.h"

/**
 * Procedural city and building generation
 */

UENUM(BlueprintType)
enum class EBuildingType : uint8
{
	Residential = 0,
	Commercial = 1,
	Industrial = 2,
	Government = 3,
	Religious = 4,
	Military = 5,
	Educational = 6,
	Entertainment = 7,
	Infrastructure = 8
};

USTRUCT(BlueprintType)
struct FBuilding
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString BuildingId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FVector Location;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FVector Size; // Width, Height, Depth

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	EBuildingType BuildingType = EBuildingType::Residential;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	int32 Floors = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Material;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Rotation = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	bool bHasGarden = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	int32 Population = 0;
};

USTRUCT(BlueprintType)
struct FRoad
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FVector StartPoint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FVector EndPoint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Width = 10.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString RoadType; // main, secondary, residential
};

USTRUCT(BlueprintType)
struct FDistrict
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString DistrictName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FVector Center;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Radius = 500.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FBuilding> Buildings;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	int32 Population = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString DistrictType; // residential, industrial, commercial, mixed
};

UCLASS()
class PROCEDURALADMIN_API AProceduralCityGenerator : public AActor
{
	GENERATED_BODY()

public:
	AProceduralCityGenerator();

	// City parameters
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "City")
	FString CityName = TEXT("ProceduralCity");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "City")
	int32 CityPopulation = 100000;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "City")
	float CityRadius = 5000.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "City")
	int32 NumberOfDistricts = 8;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "City")
	int32 BuildingsPerDistrict = 50;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "City")
	float BuildingDensity = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "City")
	int32 RandomSeed = 42;

	virtual void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category = "City Generation")
	void GenerateCity();

	UFUNCTION(BlueprintCallable, Category = "City Generation")
	void GenerateDistricts();

	UFUNCTION(BlueprintCallable, Category = "City Generation")
	void GenerateRoadNetwork();

	UFUNCTION(BlueprintCallable, Category = "City Generation")
	void PopulateDistricts();

	UFUNCTION(BlueprintCallable, Category = "City Generation")
	FBuilding GenerateBuilding(EBuildingType Type, FVector Location, int32 DistrictIndex);

	UFUNCTION(BlueprintCallable, Category = "City Generation")
	void ExportCityToBlender(const FString& FilePath);

	UFUNCTION(BlueprintCallable, Category = "City Generation")
	void ClearCity();

protected:
	UPROPERTY(VisibleAnywhere, Category = "City")
	TArray<FDistrict> Districts;

	UPROPERTY(VisibleAnywhere, Category = "City")
	TArray<FRoad> RoadNetwork;

	UPROPERTY(VisibleAnywhere, Category = "City")
	TArray<AActor*> CityActors;

	void CreateDistrict(int32 Index);
	FVector GenerateRandomLocationInDistrict(const FDistrict& District);
	bool IsValidBuildingLocation(const FVector& Location, float BuildingSize);
};
