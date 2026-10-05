// ============================================================================
// MyDetectorConstruction.hh
// Definition of the MyDetectorConstruction class for Paper 10.2
// ============================================================================

#ifndef MyDetectorConstruction_h
#define MyDetectorConstruction_h

#include "G4VUserDetectorConstruction.hh"
#include "G4LogicalVolume.hh"
#include "G4VPhysicalVolume.hh"
#include "G4GenericMessenger.hh"
#include "G4SystemOfUnits.hh"
#include "G4String.hh"

class MyDetectorConstruction : public G4VUserDetectorConstruction {
public:
	MyDetectorConstruction();
	~MyDetectorConstruction() override;

	G4VPhysicalVolume* Construct() override;
	void DefineMaterials();
	void ConstructSDandField() override;

	G4double GetSampleDetectorDistance() const { return fSample_Thickness; }
	G4String GetSampleMaterialName() const { return fSampleMaterial; }
	G4double GetSampleThickness() const { return fSample_Thickness; }

private:
	void UpdateGeometry();

	G4double fSample_Thickness;
	G4String fSampleMaterial;
	G4double fCollimator2_Height;

	G4VPhysicalVolume* World_Phys = nullptr;
	G4GenericMessenger* fMessenger = nullptr;
};

#endif // MyDetectorConstruction_h
