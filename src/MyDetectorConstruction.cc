// =========================================================================
// MyDetectorConstruction.cc - Paper 10.2 Benchmark Geometry & Materials
// =========================================================================

#include "MyDetectorConstruction.hh"
#include "MySensitiveDetector.hh"

#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4Sphere.hh"
#include "G4LogicalVolume.hh"
#include "G4VPhysicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
#include "G4Region.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4RegionStore.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4RunManager.hh"
#include "G4ProductionCuts.hh"

// =========================================================================
// Geometry Dimensions (Paper 10.2 Fig. 3 / Fig. 5)
// =========================================================================
namespace GEO {
	const G4double WorldSize = 3.0 * m;
	const G4double Outer_Radius = 6.0 * cm; // outer lead shield / collar radius

	// 1. Source & Back Shield
	const G4double Source_Radius = 0.5 * cm;
	const G4double BackShield_Thickness = 2.0 * cm; // z = -2 to 0 cm

	// 2. Collimator 1
	const G4double Collimator1_InnerRadius = 0.5 * cm; // hole r = 0.5 cm
	const G4double Collimator1_Height = 15.0 * cm;      // z = 0 to 15 cm

	// 3. Sample Chamber
	const G4double Sample_Radius = 2.5 * cm;           // disc r = 2.5 cm (dia 5 cm)
	const G4double Chamber_InnerRadius = 3.0 * cm;     // collar inner r = 3.0 cm
	const G4double Chamber_Height = 3.0 * cm;          // z = 15 to 18 cm

	// 4. Collimator 2
	const G4double Collimator2_InnerRadius = 0.5 * cm; // hole r = 0.5 cm
	const G4double Collimator2_Height = 10.0 * cm;     // z = 18 to 28 cm

	// 5. Detector NaI & Shielding
	const G4double Solid_NaI_Radius = 2.5 * cm;        // NaI crystal r = 2.5 cm
	const G4double Solid_NaI_Height = 5.0 * cm;        // z = 28 to 33 cm
	const G4double DetBackCap_Thickness = 2.0 * cm;    // z = 33 to 35 cm

	// 6. Virtual Detector Plane
	const G4double DetPlane_Radius    = Solid_NaI_Radius;
	const G4double DetPlane_Thickness = 1.0e-3 * mm;
	const G4double DetPlane_To_NaI_Gap = 0.01 * mm;
}

// =========================================================================
// Constructor / Destructor
// =========================================================================
MyDetectorConstruction::MyDetectorConstruction()
	: G4VUserDetectorConstruction(),
	fMessenger(nullptr),
	fSample_Thickness(5.0 * mm),
	fSampleMaterial("TPCB00"),
	fCollimator2_Height(10.0 * cm)
{
	fMessenger = new G4GenericMessenger(this, "/DetectorConstruction/", "Detector Construction Control");
	fMessenger->DeclareProperty("Sample_Thickness", fSample_Thickness, "Set Sample_Thickness in mm or cm");
	fMessenger->DeclareProperty("Sample_Material", fSampleMaterial, "Set Sample material name (TPCB00, TPCB02, TPCB04, TPCB06, TPCB10, Blank)");
	fMessenger->DeclareProperty("Collimator2_Height", fCollimator2_Height, "Set Collimator2 height");
	fMessenger->DeclareMethod("update", &MyDetectorConstruction::UpdateGeometry, "Update geometry after parameter changes");
}

MyDetectorConstruction::~MyDetectorConstruction() {
	delete fMessenger;
}

// =========================================================================
// Define Materials (Paper 10.2 Table 10 Wt%)
// =========================================================================
void MyDetectorConstruction::DefineMaterials() {
	G4NistManager* NIST = G4NistManager::Instance();

	NIST->FindOrBuildMaterial("G4_AIR");
	NIST->FindOrBuildMaterial("G4_Galactic");
	NIST->FindOrBuildMaterial("G4_SODIUM_IODIDE");
	NIST->FindOrBuildMaterial("G4_Pb");

	G4Element* elB  = NIST->FindOrBuildElement("B");
	G4Element* elO  = NIST->FindOrBuildElement("O");
	G4Element* elCa = NIST->FindOrBuildElement("Ca");
	G4Element* elZr = NIST->FindOrBuildElement("Zr");
	G4Element* elTe = NIST->FindOrBuildElement("Te");
	G4Element* elPb = NIST->FindOrBuildElement("Pb");

	// Blank / S0 placeholder: vacuum
	if (!G4Material::GetMaterial("Blank", false)) {
		new G4Material("Blank", 1, 1.008 * g / mole, 1e-25 * g / cm3,
			kStateGas, 2.73 * kelvin, 3e-18 * pascal);
	}

	// 1. TPCB-00 (rho = 4.720 g/cm3)
	if (!G4Material::GetMaterial("TPCB00", false)) {
		G4Material* mat = new G4Material("TPCB00", 4.720 * g / cm3, 5);
		mat->AddElement(elB,  0.12423);
		mat->AddElement(elO,  0.38728);
		mat->AddElement(elCa, 0.14294);
		mat->AddElement(elTe, 0.15990);
		mat->AddElement(elPb, 0.18566);
	}

	// 2. TPCB-02 (rho = 4.784 g/cm3)
	if (!G4Material::GetMaterial("TPCB02", false)) {
		G4Material* mat = new G4Material("TPCB02", 4.784 * g / cm3, 6);
		mat->AddElement(elB,  0.11801);
		mat->AddElement(elO,  0.37868);
		mat->AddElement(elCa, 0.14294);
		mat->AddElement(elZr, 0.01481);
		mat->AddElement(elTe, 0.15990);
		mat->AddElement(elPb, 0.18566);
	}

	// 3. TPCB-04 (rho = 4.849 g/cm3)
	if (!G4Material::GetMaterial("TPCB04", false)) {
		G4Material* mat = new G4Material("TPCB04", 4.849 * g / cm3, 6);
		mat->AddElement(elB,  0.11180);
		mat->AddElement(elO,  0.37009);
		mat->AddElement(elCa, 0.14294);
		mat->AddElement(elZr, 0.02961);
		mat->AddElement(elTe, 0.15990);
		mat->AddElement(elPb, 0.18566);
	}

	// 4. TPCB-06 (rho = 4.913 g/cm3)
	if (!G4Material::GetMaterial("TPCB06", false)) {
		G4Material* mat = new G4Material("TPCB06", 4.913 * g / cm3, 6);
		mat->AddElement(elB,  0.10559);
		mat->AddElement(elO,  0.36149);
		mat->AddElement(elCa, 0.14294);
		mat->AddElement(elZr, 0.04442);
		mat->AddElement(elTe, 0.15990);
		mat->AddElement(elPb, 0.18566);
	}

	// 5. TPCB-10 (rho = 5.042 g/cm3)
	if (!G4Material::GetMaterial("TPCB10", false)) {
		G4Material* mat = new G4Material("TPCB10", 5.042 * g / cm3, 6);
		mat->AddElement(elB,  0.09317);
		mat->AddElement(elO,  0.34430);
		mat->AddElement(elCa, 0.14294);
		mat->AddElement(elZr, 0.07403);
		mat->AddElement(elTe, 0.15990);
		mat->AddElement(elPb, 0.18566);
	}
}

// =========================================================================
// Construct Geometry (Paper 10.2 Fig. 3 / Fig. 5)
// =========================================================================
G4VPhysicalVolume* MyDetectorConstruction::Construct() {
	DefineMaterials();
	G4NistManager* NIST = G4NistManager::Instance();
	G4Material* vacuumMat = NIST->FindOrBuildMaterial("G4_Galactic");
	G4Material* pbMat = NIST->FindOrBuildMaterial("G4_Pb");

	// 1. World Volume
	G4Box* solidWorld = new G4Box("World", GEO::WorldSize / 2, GEO::WorldSize / 2, GEO::WorldSize / 2);
	G4LogicalVolume* World_LV = new G4LogicalVolume(solidWorld, vacuumMat, "WorldLV");
	World_Phys = new G4PVPlacement(nullptr, {}, World_LV, "World", nullptr, false, 0, true);

	// 2. Lead Back Shield (z = -2 to 0 cm, r = 6.0 cm)
	G4Tubs* solidBackShield = new G4Tubs("BackShield", 0, GEO::Outer_Radius, GEO::BackShield_Thickness / 2, 0, 360 * deg);
	G4LogicalVolume* BackShield_LV = new G4LogicalVolume(solidBackShield, pbMat, "BackShield_LV");
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, -GEO::BackShield_Thickness / 2), BackShield_LV, "BackShield", World_LV, false, 0, true);

	// 3. Collimator 1 (z = 0 to 15 cm, hole r = 0.5 cm, outer r = 6.0 cm)
	G4Tubs* solidCollimator1 = new G4Tubs("Collimator1", GEO::Collimator1_InnerRadius, GEO::Outer_Radius, GEO::Collimator1_Height / 2, 0, 360 * deg);
	G4LogicalVolume* Collimator1_LV = new G4LogicalVolume(solidCollimator1, pbMat, "Collimator1_LV");
	G4double Collimator1_PosZ = GEO::Collimator1_Height / 2;
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, Collimator1_PosZ), Collimator1_LV, "Collimator1", World_LV, false, 0, true);

	// 4. Sample Chamber Collar Pb (z = 15 to 18 cm, inner r = 3.0 cm, outer r = 6.0 cm)
	G4Tubs* solidChamberCollar = new G4Tubs("ChamberCollar", GEO::Chamber_InnerRadius, GEO::Outer_Radius, GEO::Chamber_Height / 2, 0, 360 * deg);
	G4LogicalVolume* ChamberCollar_LV = new G4LogicalVolume(solidChamberCollar, pbMat, "ChamberCollar_LV");
	G4double ChamberCollar_PosZ = 15.0 * cm + GEO::Chamber_Height / 2;
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, ChamberCollar_PosZ), ChamberCollar_LV, "ChamberCollar", World_LV, false, 0, true);

	// 5. Sample Disc (z = 15 to 15 + thickness, r = 2.5 cm)
	G4Tubs* solidSample = new G4Tubs("Sample", 0, GEO::Sample_Radius, fSample_Thickness / 2, 0, 360 * deg);
	G4String matLookup = fSampleMaterial;
	G4Material* sampleMat = G4Material::GetMaterial(matLookup, false);
	if (!sampleMat) {
		sampleMat = vacuumMat;
	}
	G4LogicalVolume* Sample_LV = new G4LogicalVolume(solidSample, sampleMat, "Sample_LV");
	G4double Sample_PosZ = 15.0 * cm + fSample_Thickness / 2;
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, Sample_PosZ), Sample_LV, "Sample", World_LV, false, 0, true);

	// 6. Collimator 2 (z = 18 to 28 cm, hole r = 0.5 cm, outer r = 6.0 cm)
	G4Tubs* solidCollimator2 = new G4Tubs("Collimator2", GEO::Collimator2_InnerRadius, GEO::Outer_Radius, GEO::Collimator2_Height / 2, 0, 360 * deg);
	G4LogicalVolume* Collimator2_LV = new G4LogicalVolume(solidCollimator2, pbMat, "Collimator2_LV");
	G4double Collimator2_PosZ = 18.0 * cm + GEO::Collimator2_Height / 2;
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, Collimator2_PosZ), Collimator2_LV, "Collimator2", World_LV, false, 0, true);

	// 7. NaI Detector (z = 28 to 33 cm, r = 2.5 cm)
	G4Tubs* solidNaI = new G4Tubs("NaI", 0, GEO::Solid_NaI_Radius, GEO::Solid_NaI_Height / 2, 0, 360 * deg);
	G4LogicalVolume* NaI_LV = new G4LogicalVolume(solidNaI, NIST->FindOrBuildMaterial("G4_SODIUM_IODIDE"), "NaI_LV");
	G4double NaI_PosZ = 28.0 * cm + GEO::Solid_NaI_Height / 2;
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, NaI_PosZ), NaI_LV, "NaI", World_LV, false, 0, true);

	// 8. NaI Side Shield Pb (z = 28 to 33 cm, inner r = 2.5 cm, outer r = 6.0 cm)
	G4Tubs* solidDetSideShield = new G4Tubs("DetSideShield", GEO::Solid_NaI_Radius, GEO::Outer_Radius, GEO::Solid_NaI_Height / 2, 0, 360 * deg);
	G4LogicalVolume* DetSideShield_LV = new G4LogicalVolume(solidDetSideShield, pbMat, "DetSideShield_LV");
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, NaI_PosZ), DetSideShield_LV, "DetSideShield", World_LV, false, 0, true);

	// 9. Detector Back Cap Pb (z = 33 to 35 cm, r = 6.0 cm)
	G4Tubs* solidDetBackCap = new G4Tubs("DetBackCap", 0, GEO::Outer_Radius, GEO::DetBackCap_Thickness / 2, 0, 360 * deg);
	G4LogicalVolume* DetBackCap_LV = new G4LogicalVolume(solidDetBackCap, pbMat, "DetBackCap_LV");
	G4double DetBackCap_PosZ = 33.0 * cm + GEO::DetBackCap_Thickness / 2;
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, DetBackCap_PosZ), DetBackCap_LV, "DetBackCap", World_LV, false, 0, true);

	// 10. Virtual Detector Plane (z = 28 cm entrance face)
	G4Tubs* solidDetPlane = new G4Tubs("DetPlane", 0, GEO::DetPlane_Radius, GEO::DetPlane_Thickness / 2, 0, 360 * deg);
	G4LogicalVolume* DetPlane_LV = new G4LogicalVolume(solidDetPlane, vacuumMat, "DetPlane_LV");
	G4double DetPlane_PosZ = 28.0 * cm - GEO::DetPlane_Thickness / 2 - GEO::DetPlane_To_NaI_Gap;
	new G4PVPlacement(nullptr, G4ThreeVector(0, 0, DetPlane_PosZ), DetPlane_LV, "DetPlane", World_LV, false, 0, true);

	// Visual attributes
	G4VisAttributes* visPb = new G4VisAttributes(G4Colour(0.5, 0.5, 0.5, 0.8));
	Collimator1_LV->SetVisAttributes(visPb);
	ChamberCollar_LV->SetVisAttributes(visPb);
	Collimator2_LV->SetVisAttributes(visPb);
	BackShield_LV->SetVisAttributes(visPb);
	DetSideShield_LV->SetVisAttributes(visPb);
	DetBackCap_LV->SetVisAttributes(visPb);

	G4VisAttributes* visSample = new G4VisAttributes(G4Colour(0.0, 0.8, 1.0, 0.9));
	Sample_LV->SetVisAttributes(visSample);

	G4VisAttributes* visNaI = new G4VisAttributes(G4Colour(0.0, 1.0, 0.0, 0.8));
	NaI_LV->SetVisAttributes(visNaI);

	G4VisAttributes* visPlane = new G4VisAttributes(G4Colour(1.0, 1.0, 0.0, 0.5));
	visPlane->SetVisibility(false);
	DetPlane_LV->SetVisAttributes(visPlane);

	// Production cuts in Sample
	G4Region* Sample_Region = G4RegionStore::GetInstance()->FindOrCreateRegion("SampleRegion");
	Sample_Region->AddRootLogicalVolume(Sample_LV);
	G4ProductionCuts* sampleCuts = new G4ProductionCuts();
	sampleCuts->SetProductionCut(1 * nm, G4ProductionCuts::GetIndex("gamma"));
	sampleCuts->SetProductionCut(1 * nm, G4ProductionCuts::GetIndex("e-"));
	sampleCuts->SetProductionCut(1 * nm, G4ProductionCuts::GetIndex("e+"));
	Sample_Region->SetProductionCuts(sampleCuts);

	return World_Phys;
}

void MyDetectorConstruction::UpdateGeometry() {
	auto runManager = G4RunManager::GetRunManager();
	runManager->ReinitializeGeometry();
	ConstructSDandField();
	G4cout << "\n================ Updated Geometry ================\n";
	G4cout << " Sample Thickness: " << fSample_Thickness / mm << " mm\n";
	G4cout << " Sample Material : " << fSampleMaterial << "\n";
}

void MyDetectorConstruction::ConstructSDandField() {
	auto sdManager = G4SDManager::GetSDMpointer();
	auto LVS = G4LogicalVolumeStore::GetInstance();

	G4String SDname = "NaI_SD";
	auto NaI_Detector = dynamic_cast<MySensitiveDetector*>(sdManager->FindSensitiveDetector(SDname, false));
	if (!NaI_Detector) {
		NaI_Detector = new MySensitiveDetector(SDname, "NaIHitsCollection");
		sdManager->AddNewDetector(NaI_Detector);
	}

	for (auto lv : *LVS) {
		if (lv->GetName() == "NaI_LV" || lv->GetName() == "DetPlane_LV") {
			lv->SetSensitiveDetector(NaI_Detector);
		}
	}
}