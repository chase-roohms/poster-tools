#target photoshop

// Toggle visibility of layers by prefix
// Prompts user for a prefix and whether to show or hide matching layers

function toggleLayersByPrefix() {
    if (!app.documents.length) {
        alert("Please open a document first.");
        return;
    }
    
    var doc = app.activeDocument;
    
    // Prompt for layer name prefix
    var prefix = prompt("Enter layer name prefix:", "");
    if (!prefix) {
        alert("No prefix entered. Operation cancelled.");
        return;
    }
    
    // Prompt for show/hide action
    var action = prompt("Enter action (show or hide):", "show");
    if (!action) {
        alert("No action specified. Operation cancelled.");
        return;
    }
    
    action = action.toLowerCase();
    if (action !== "show" && action !== "hide") {
        alert("Invalid action. Please enter 'show' or 'hide'.");
        return;
    }
    
    var shouldShow = (action === "show");
    var matchCount = 0;
    
    // Process all layers in document
    matchCount = processLayers(doc.layers, prefix, shouldShow, matchCount);
    
    // Show results
    var actionText = shouldShow ? "shown" : "hidden";
    alert("Operation complete.\n" + matchCount + " layer(s) with prefix '" + prefix + "' were " + actionText + ".");
}

// Recursively process layers and layer sets
function processLayers(layers, prefix, shouldShow, matchCount) {
    for (var i = 0; i < layers.length; i++) {
        var layer = layers[i];
        
        // Check if layer name starts with prefix
        if (layer.name.indexOf(prefix) === 0) {
            layer.visible = shouldShow;
            matchCount++;
        }
        
        // If it's a layer set (group), process its children recursively
        if (layer.typename === "LayerSet") {
            matchCount = processLayers(layer.layers, prefix, shouldShow, matchCount);
        }
    }
    
    return matchCount;
}

// Run the script
toggleLayersByPrefix();
