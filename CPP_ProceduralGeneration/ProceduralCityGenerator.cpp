#include "ProceduralCityGenerator.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Math/UnrealMathUtility.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AProceduralCityGenerator::AProceduralCityGenerator()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AProceduralCityGenerator::BeginPlay()
{
	Super::BeginPlay();
}

void AProceduralCityGenerator::GenerateCity()
{
	ClearCity();
	GenerateDistricts();
	GenerateRoadNetwork();
	PopulateDistricts();

	UE_LOG(LogTemp, Warning, TEXT("City '%s' generated with %d districts"), *CityName, Districts.Num());
}

void AProceduralCityGenerator::GenerateDistricts()
{
	Districts.Empty();
	FRandomStream RandomStream(RandomSeed);

	float AngleBetweenDistricts = 360.0f / NumberOfDistricts;

	for (int32 i = 0; i < NumberOfDistricts; i++)
	{
		FDistrict District;
		District.DistrictName = FString::Printf(TEXT("District_%d"), i);

		float Angle = FMath::DegreesToRadians(i * AngleBetweenDistricts);
		float DistanceFromCenter = CityRadius * 0.6f;

		District.Center = GetActorLocation() + FVector(
			FMath::Cos(Angle) * DistanceFromCenter,
			FMath::Sin(Angle) * DistanceFromCenter,
			0.0f
		);

		District.Radius = CityRadius / (NumberOfDistricts * 0.5f);
		District.Population = CityPopulation / NumberOfDistricts;

		// Randomize district type
		int32 TypeChoice = RandomStream.RandRange(0, 3);
		switch (TypeChoice)
		{
			case 0: District.DistrictType = TEXT("residential"); break;
			case 1: District.DistrictType = TEXT("commercial"); break;
			case 2: District.DistrictType = TEXT("industrial"); break;
			case 3: District.DistrictType = TEXT("mixed"); break;
		}

		CreateDistrict(i);
		Districts.Add(District);
	}
}

void AProceduralCityGenerator::CreateDistrict(int32 Index)
{
	if (Districts.IsValidIndex(Index))
	{
		FDistrict& District = Districts[Index];
		District.Buildings.Empty();
	}
}

void AProceduralCityGenerator::GenerateRoadNetwork()
{
	RoadNetwork.Empty();
	FRandomStream RandomStream(RandomSeed + 1);

	// Connect district centers with main roads
	for (int32 i = 0; i < Districts.Num(); i++)
	{
		int32 NextDistrict = (i + 1) % Districts.Num();

		FRoad MainRoad;
		MainRoad.StartPoint = Districts[i].Center;
		MainRoad.EndPoint = Districts[NextDistrict].Center;
		MainRoad.RoadType = TEXT("main");
		MainRoad.Width = 25.0f;

		RoadNetwork.Add(MainRoad);

		// Add secondary roads to city center
		FRoad SecondaryRoad;
		SecondaryRoad.StartPoint = Districts[i].Center;
		SecondaryRoad.EndPoint = GetActorLocation();
		SecondaryRoad.RoadType = TEXT("secondary");
		SecondaryRoad.Width = 15.0f;

		RoadNetwork.Add(SecondaryRoad);
	}

	UE_LOG(LogTemp, Warning, TEXT("Road network generated: %d roads"), RoadNetwork.Num());
}

void AProceduralCityGenerator::PopulateDistricts()
{
	FRandomStream RandomStream(RandomSeed + 2);

	for (int32 i = 0; i < Districts.Num(); i++)
	{
		FDistrict& District = Districts[i];

		for (int32 j = 0; j < BuildingsPerDistrict; j++)
		{
			if (RandomStream.FRand() > BuildingDensity) continue;

			FVector BuildingLocation = GenerateRandomLocationInDistrict(District);

			EBuildingType BuildingType;
			if (District.DistrictType == TEXT("residential"))
				BuildingType = EBuildingType::Residential;
			else if (District.DistrictType == TEXT("commercial"))
				BuildingType = EBuildingType::Commercial;
			else if (District.DistrictType == TEXT("industrial"))
				BuildingType = EBuildingType::Industrial;
			else
				BuildingType = static_cast<EBuildingType>(RandomStream.RandRange(0, 8));

			FBuilding Building = GenerateBuilding(BuildingType, BuildingLocation, i);
			District.Buildings.Add(Building);
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("Districts populated"));
}

FVector AProceduralCityGenerator::GenerateRandomLocationInDistrict(const FDistrict& District)
{
	FRandomStream RandomStream(RandomSeed + 3);

	float RandomAngle = FMath::DegreesToRadians(RandomStream.FRand() * 360.0f);
	float RandomDistance = RandomStream.FRand() * District.Radius * 0.8f;

	FVector Location = District.Center + FVector(
		FMath::Cos(RandomAngle) * RandomDistance,
		FMath::Sin(RandomAngle) * RandomDistance,
		0.0f
	);

	return Location;
}

FBuilding AProceduralCityGenerator::GenerateBuilding(EBuildingType Type, FVector Location, int32 DistrictIndex)
{
	FRandomStream RandomStream(RandomSeed + DistrictIndex * 100);

	FBuilding Building;
	Building.BuildingId = FString::Printf(TEXT("Building_%d"), RandomStream.RandRange(10000, 99999));
	Building.Location = Location;
	Building.BuildingType = Type;
	Building.Rotation = RandomStream.FRand() * 360.0f;
	Building.Population = RandomStream.RandRange(10, 500);

	// Size varies by type
	switch (Type)
	{
		case EBuildingType::Residential:
			Building.Size = FVector(RandomStream.FRandRange(20, 50), RandomStream.FRandRange(20, 50), RandomStream.FRandRange(30, 100));
			Building.Floors = RandomStream.RandRange(1, 5);
			Building.Material = TEXT("Brick");
			break;

		case EBuildingType::Commercial:
			Building.Size = FVector(RandomStream.FRandRange(50, 100), RandomStream.FRandRange(50, 100), RandomStream.FRandRange(50, 150));
			Building.Floors = RandomStream.RandRange(3, 10);
			Building.Material = TEXT("Glass");
			break;

		case EBuildingType::Industrial:
			Building.Size = FVector(RandomStream.FRandRange(100, 200), RandomStream.FRandRange(100, 200), RandomStream.FRandRange(30, 80));
			Building.Floors = 1;
			Building.Material = TEXT("Concrete");
			break;

		case EBuildingType::Government:
			Building.Size = FVector(RandomStream.FRandRange(80, 120), RandomStream.FRandRange(80, 120), RandomStream.FRandRange(80, 200));
			Building.Floors = RandomStream.RandRange(5, 8);
			Building.Material = TEXT("Marble");
			break;

		default:
			Building.Size = FVector(RandomStream.FRandRange(30, 60), RandomStream.FRandRange(30, 60), RandomStream.FRandRange(40, 120));
			Building.Floors = RandomStream.RandRange(2, 6);
			Building.Material = TEXT("Mixed");
	}

	return Building;
}

bool AProceduralCityGenerator::IsValidBuildingLocation(const FVector& Location, float BuildingSize)
{
	// Check distance from other buildings
	for (const FDistrict& District : Districts)
	{
		for (const FBuilding& Building : District.Buildings)
		{
			float Distance = FVector::Dist(Location, Building.Location);
			if (Distance < BuildingSize + FMath::Max(Building.Size.X, Building.Size.Y))
			{
				return false;
			}
		}
	}
	return true;
}

void AProceduralCityGenerator::ExportCityToBlender(const FString& FilePath)
{
	TSharedPtr<FJsonObject> RootObject = MakeShareable(new FJsonObject());

	RootObject->SetStringField(TEXT("city_name"), CityName);
	RootObject->SetNumberField(TEXT("population"), CityPopulation);
	RootObject->SetNumberField(TEXT("radius"), CityRadius);

	TArray<TSharedPtr<FJsonValue>> DistrictsArray;
	for (const FDistrict& District : Districts)
	{
		TSharedPtr<FJsonObject> DistrictObj = MakeShareable(new FJsonObject());
		DistrictObj->SetStringField(TEXT("name"), District.DistrictName);
		DistrictObj->SetStringField(TEXT("type"), District.DistrictType);
		DistrictObj->SetNumberField(TEXT("population"), District.Population);

		TArray<TSharedPtr<FJsonValue>> BuildingsArray;
		for (const FBuilding& Building : District.Buildings)
		{
			TSharedPtr<FJsonObject> BuildingObj = MakeShareable(new FJsonObject());
			BuildingObj->SetStringField(TEXT("id"), Building.BuildingId);
			BuildingObj->SetNumberField(TEXT("floors"), Building.Floors);
			BuildingObj->SetStringField(TEXT("material"), Building.Material);
			BuildingObj->SetNumberField(TEXT("population"), Building.Population);

			BuildingsArray.Add(MakeShareable(new FJsonValueObject(BuildingObj)));
		}

		DistrictObj->SetArrayField(TEXT("buildings"), BuildingsArray);
		DistrictsArray.Add(MakeShareable(new FJsonValueObject(DistrictObj)));
	}

	RootObject->SetArrayField(TEXT("districts"), DistrictsArray);

	FString JsonString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(RootObject.ToSharedRef(), Writer);

	FFileHelper::SaveStringToFile(JsonString, *FilePath);
	UE_LOG(LogTemp, Warning, TEXT("City exported to: %s"), *FilePath);
}

void AProceduralCityGenerator::ClearCity()
{
	Districts.Empty();
	RoadNetwork.Empty();

	for (AActor* Actor : CityActors)
	{
		if (Actor)
		{
			Actor->Destroy();
		}
	}
	CityActors.Empty();
}
