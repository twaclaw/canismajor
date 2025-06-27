core.clear("starchart");
core.setGuiVisible(false);

GridLinesMgr.setFlagEquatorGrid(false);
NebulaMgr.setFlagHints(false);

ConstellationMgr.setConstellationDisplayStyle(1); // native style

ConstellationMgr.deselectConstellations();

ConstellationMgr.setFlagArt(false);
ConstellationMgr.setFlagBoundaries(false);
ConstellationMgr.setFlagLines(false);
ConstellationMgr.setFlagLabels(false);
ConstellationMgr.setFlagIsolateSelected(true);
ConstellationMgr.setArtIntensity(0.6);
ConstellationMgr.setConstellationLineThickness(1);
SolarSystem.setFlagLabels(false);
GridLinesMgr.setFlagEclipticLine(false);

StarMgr.setFlagLabels(false);
LandscapeMgr.setFlagLandscape(false);
LandscapeMgr.setFlagCardinalPoints(false);

core.setSkyCulture("modern");
StarMgr.setFlagLabels(false);

MarkerMgr.deleteAllMarkers();
core.setMountMode("azimuthal");
LabelMgr.deleteAllLabels();