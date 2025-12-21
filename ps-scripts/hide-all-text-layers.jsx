// Hide all text layers in the active document

function hideTextLayers(container) {
    for (var i = 0; i < container.layers.length; i++) {
        var layer = container.layers[i];

        // If it's a text layer, hide it
        if (layer.kind && layer.kind == LayerKind.TEXT) {
            layer.visible = false;
        }

        // If it's a group, recurse into it
        if (layer.typename == "LayerSet") {
            hideTextLayers(layer);
        }
    }
}

// Run
if (app.documents.length > 0) {
    hideTextLayers(app.activeDocument);
}
