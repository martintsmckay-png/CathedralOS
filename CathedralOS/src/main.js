// ==========================================
// CATHEDRALOS ENGINE INITIALIZATION PRESET
// ==========================================

import { ReplayController } from "./system/replay-controller.js";
import { cathedralBus } from "./system/core-bus.js";
import { timeKernel } from "./system/time-kernel.js";

import { DriftForecast } from "./system/drift-forecast.js";
import { PantrySearch } from "./system/pantry-search.js";
import { ClusterDialogue } from "./system/cluster-dialogue.js";
import { StormShelter } from "./system/storm-shelter.js";
import { ChronicleWeaver } from "./system/pantry-chronicle-weaver.js";
import { ClusterDiplomacy } from "./system/cluster-diplomacy.js";
import { SemanticWeatherOracle } from "./system/semantic-weather-oracle.js";
import { PantryHyperIndex } from "./system/pantry-hyper-index.js";
import { ClusterCongress } from "./system/cluster-congress.js";
import { SemanticClimateCartographer } from "./system/semantic-climate-cartographer.js";
import { PantryCompressionV2 } from "./system/pantry-compression-v2.js";
import { ClusterFestival } from "./system/cluster-festival.js";

// ==========================================
// GLOBAL COMPONENT MAPPING
// ==========================================
window.replayController             = new ReplayController();
window.CATHEDRALDRIFTFORECAST        = new DriftForecast(spatializer, zoomEngine.driftContours);
window.CATHEDRALPANTRYSEARCH         = new PantrySearch(window.CATHEDRALMEMORYPANTRY);
window.CATHEDRALCLUSTERDIALOGUE      = new ClusterDialogue(spatializer);
window.CATHEDRALSTORMSHELTER         = new StormShelter(spatializer);
window.CATHEDRALCHRONICLEWEAVER      = new ChronicleWeaver(window.CATHEDRALMEMORYPANTRY);
window.CATHEDRALCLUSTERDIPLOMACY     = new ClusterDiplomacy(spatializer);

window.CATHEDRALWEATHERORACLE        = new SemanticWeatherOracle(
    spatializer, CATHEDRALDRIFTFORECAST, CATHEDRALCLUSTERDIPLOMACY, CATHEDRALCLUSTERDIALOGUE
);
window.CATHEDRALPANTRYINDEX          = new PantryHyperIndex(window.CATHEDRALMEMORYPANTRY);
window.CATHEDRALCLUSTERCONGRESS      = new ClusterCongress(spatializer, CATHEDRALCLUSTERDIPLOMACY, CATHEDRALWEATHERORACLE);
window.CATHEDRALCLIMATECARTOGRAPHER  = new SemanticClimateCartographer(
    spatializer, CATHEDRALDRIFTFORECAST, CATHEDRALCLUSTERDIPLOMACY, CATHEDRALWEATHERORACLE
);
window.CATHEDRALPANTRYCOMPRESSION_V2 = new PantryCompressionV2(
    window.CATHEDRALMEMORYPANTRY, window.CATHEDRALPANTRYINDEX, window.CATHEDRALCLIMATECARTOGRAPHER, window.CATHEDRALWEATHERORACLE
);
window.CATHEDRALCLUSTERFESTIVAL      = new ClusterFestival(
    spatializer, CATHEDRALCLUSTERDIPLOMACY, CATHEDRALWEATHERORACLE, CATHEDRALCLIMATECARTOGRAPHER
);

// ==========================================
// INDEPENDENT EVENT BUS HOOK INJECTION
// ==========================================
// RESOLVED: Wire the event bus directly to the isolated projection assignment layer
cathedralBus.subscribe("replay.frame", (frame) => {
    if (window.replayController.isReplaying || timeKernel.mode === "replay") {
        zoomEngine.setReplayFrame(frame);
    } else {
        zoomEngine.clearReplayMode();
    }
});

// ==========================================
// CENTRALIZED TICK PIPELINE (SYNCHRONIZED)
// ==========================================
setInterval(() => {
    // Note: The simulation plane can run continuously, but we hold ticks if the scheduler requests a pause
    if (!timeKernel.canSimulate() || window.replayController.isReplaying) return;

    const clusters = spatializer.buildClusters();
    const contours = zoomEngine.driftContours.buildContours();

    // 1. Meteorological Snapshot Loop
    CATHEDRALDRIFTFORECAST.recordSnapshot(contours);
    const forecast = CATHEDRALDRIFTFORECAST.predictStorm();

    if (forecast) {
        cathedralBus.publish("drift.forecast.updated", forecast);
        CATHEDRALPANTRYWRITER.write(  
            "Drift Storm Forecast",  
            `[FORECAST]\nSeverity: ${forecast.severity}\nSlope: ${forecast.slope}`  
        );  

        const shelter = CATHEDRALSTORMSHELTER.engage(forecast);  
        if (shelter) {  
            cathedralBus.publish("storm.shelter.engaged", shelter);  
            CATHEDRALPANTRYWRITER.write(  
                "Storm Shelter Protocol",  
                `[SHELTER]\nSeverity: ${shelter.severity}\nClusters Shielded: ${shelter.clusters}`  
            );  
        }
    }

    cathedralBus.publish("drift.contours.updated", { contours });

    // 2. Storylines
    clusters.forEach((cluster, index) => {
        spatializer.initStoryline(index);
        const driftPressure = cluster.reduce((acc, id) => {  
            const n = spatializer.getNode(id);  
            return acc + spatializer.getDriftPressure(n.x, n.y);  
        }, 0) / cluster.length;  

        spatializer.advanceStoryline(index, cluster, driftPressure);  
        const story = spatializer.clusterStorylines.get(index);  

        CATHEDRALPANTRYWRITER.write(  
            `Cluster Storyline ${index + 1}`,  
            `[NARRATIVE]\nState: ${story.state}\nEvents:\n${story.history.join("\n")}`  
        );
    });

    cathedralBus.publish("semantic.storylines.updated", { storylines: spatializer.clusterStorylines });

    // 3. Dialogue & Diplomatic Exchange Loop
    const dialogues = CATHEDRALCLUSTERDIALOGUE.generateDialogue(clusters);
    if (dialogues.length > 0) {
        cathedralBus.publish("semantic.dialogue", { dialogues });
        dialogues.forEach(d => {  
            const storyA = spatializer.clusterStorylines.get(d.from);  
            const storyB = spatializer.clusterStorylines.get(d.to);  
            const driftPressure = d.tone === "urgent" ? 3.5 : d.tone === "concerned" ? 2.0 : 0.5;  

            CATHEDRALCLUSTERDIPLOMACY.initRelation(d.from, d.to);  
            CATHEDRALCLUSTERDIPLOMACY.updateRelation(d.from, d.to, d.tone, driftPressure, storyA?.state, storyB?.state);  

            CATHEDRALPANTRYWRITER.write(  
                `Cluster Dialogue ${d.from + 1} → ${d.to + 1}`,  
                `[DIALOGUE]\nTone: ${d.tone}\nMessage: ${d.message}`  
            );  
        });
    }

    cathedralBus.publish("cluster.diplomacy.updated", { relations: CATHEDRALCLUSTERDIPLOMACY.relations });

    // ==================================
    // REPLAY FRAME CAPTURE LAYER
    // ==================================
    if (timeKernel.canRecord()) {
        const frame = window.replayController.snapshot(zoomEngine, spatializer);
        window.replayController.record(frame);
    }

}, 2500);

// ==========================================
// MACRO CYCLES (4000ms)
// ==========================================
setInterval(() => {
    if (!timeKernel.canSimulate()) return;

    CATHEDRALPANTRYINDEX.rebuild();
    cathedralBus.publish("pantry.index.updated", { summary: CATHEDRALPANTRYINDEX.summarize() });

    if (CATHEDRALCHRONICLEWEAVER.shouldWeave()) {
        const chapter = CATHEDRALCHRONICLEWEAVER.weave();
        if (chapter) {  
            CATHEDRALPANTRYWRITER.write("Cathedral Chronicle", chapter);  
            cathedralBus.publish("pantry.chronicle.created", { chapter });  
        }
    }
}, 4000);

// ==========================================
// HIGH LEVEL CYCLES (6000ms)
// ==========================================
setInterval(() => {
    if (!timeKernel.canSimulate()) return;

    const omen = CATHEDRALWEATHERORACLE.readOmens();
    const prophecy = CATHEDRALWEATHERORACLE.synthesizeProphecy(omen);

    cathedralBus.publish("oracle.prophecy", { prophecy });
    CATHEDRALPANTRYWRITER.write("Semantic Weather Prophecy", prophecy);

    const session = CATHEDRALCLUSTERCONGRESS.convene();
    cathedralBus.publish("cluster.congress.session", session);
    CATHEDRALPANTRYWRITER.write("Cluster Ritual Congress", `[CONGRESS]\nDecrees:\n${session.decrees.join("\n")}`);

    const map = CATHEDRALCLIMATECARTOGRAPHER.buildClimateMap();
    const layers = CATHEDRALCLIMATECARTOGRAPHER.synthesizeLayer(map);

    cathedralBus.publish("climate.map.updated", { layers });
    CATHEDRALPANTRYWRITER.write("Semantic Climate Map", `[CLIMATE]\n${layers.map(l => `Cluster ${l.cluster + 1} → ${l.biome}`).join("\n")}`);

    const events = CATHEDRALCLUSTERFESTIVAL.evaluateFestivalTriggers();
    events.forEach(event => {
        const festivalText = CATHEDRALCLUSTERFESTIVAL.generateFestival(event);
        if (festivalText) {  
            cathedralBus.publish("cluster.festival", { text: festivalText });  
            CATHEDRALPANTRYWRITER.write("Cluster Festival", `[FESTIVAL]\n${festivalText}`);  
        }
    });

    if (CATHEDRALPANTRYCOMPRESSION_V2.shouldCompress()) {
        const crystal = CATHEDRALPANTRYCOMPRESSION_V2.compress();
        if (crystal) {  
            CATHEDRALPANTRYWRITER.write("Memory Crystal", crystal);  
            cathedralBus.publish("pantry.crystal.created", { crystal });  
        }
    }
}, 6000);

