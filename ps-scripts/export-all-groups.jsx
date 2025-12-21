// Photoshop Script to Export All Groups as PNG
// This script exports each top-level group in the active document as a separate PNG file

#target photoshop

// Check if a document is open
if (app.documents.length === 0) {
    alert("Please open a document first.");
} else {
    main();
}

function main() {
    var doc = app.activeDocument;
    var exportFolder = Folder.selectDialog("Select export folder");
    
    if (exportFolder == null) {
        return; // User cancelled
    }
    
    // Store original visibility states
    var originalStates = [];
    
    // Hide all top-level layers/groups first
    for (var i = 0; i < doc.layers.length; i++) {
        originalStates.push(doc.layers[i].visible);
        doc.layers[i].visible = false;
    }
    
    var exportCount = 0;
    
    // Process each top-level layer
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        
        // Check if it's a layer set (group)
        if (layer.typename == "LayerSet") {
            // Show only this group
            layer.visible = true;
            
            // Clean filename
            var filename = layer.name.replace(/[\/\\:*?"<>|]/g, "_");
            var exportFile = new File(exportFolder + "/" + filename + ".png");
            
            // Export as PNG
            exportPNG(doc, exportFile);
            
            exportCount++;
            
            // Hide this group again
            layer.visible = false;
        }
    }
    
    // Restore original visibility states
    for (var i = 0; i < doc.layers.length; i++) {
        doc.layers[i].visible = originalStates[i];
    }
    
    alert("Exported " + exportCount + " groups as PNG files to:\n" + exportFolder.fsName);
}

function exportPNG(doc, file) {
    var pngOptions = new PNGSaveOptions();
    pngOptions.compression = 9;
    pngOptions.interlaced = false;
    
    doc.saveAs(file, pngOptions, true, Extension.LOWERCASE);
}
