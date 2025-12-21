// Photoshop Script to Rename all Groups Based on Contained Text Layers
// This script renames each top-level group in the active document based on the text content of its first contained text layers

#target photoshop

(function () {

    // Ensure a document is open
    if (!app.documents.length) {
        alert("No document open!");
        return;
    }

    var doc = app.activeDocument;

    // Loop through *only* top-level layer sets (groups)
    for (var i = 0; i < doc.layerSets.length; i++) {

        var group = doc.layerSets[i];

        // Try to find a text layer inside this group
        var textContent = getTextFromGroup(group);

        if (textContent) {
            group.name = textContent;
        }
    }

    alert("Done!");

    // --- Helpers ---

    function getTextFromGroup(group) {

        // search direct children only
        for (var j = 0; j < group.artLayers.length; j++) {
            var lyr = group.artLayers[j];

            if (lyr.kind == LayerKind.TEXT) {
                return lyr.textItem.contents;
            }
        }

        // if not found, search nested groups (optional)
        for (var k = 0; k < group.layerSets.length; k++) {
            var result = getTextFromGroup(group.layerSets[k]);
            if (result) return result;
        }

        return null;
    }

})();
