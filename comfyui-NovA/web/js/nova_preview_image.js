import { app } from "../../../scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
    name: "NovA.PreviewImage",
    async nodeCreated(node) {
        if (node.comfyClass === "NovAPreviewImage") {
            
            // Wait for core widgets initialization to append our action button at the very bottom
            setTimeout(() => {
                // Add the action button dedicated to image export
                const saveButton = node.addWidget("button", "💾 Save Image As...", null, () => {
                    const currentImage = node.images?.[0];
                    if (!currentImage) {
                        alert("No image available to save. Please queue a prompt first.");
                        return;
                    }
                    handleImageSave(currentImage);
                });

                // Prevent this runtime UI action widget from cluttering workflow JSON serialization
                saveButton.serialize = false;

                // INITIAL SIZE SETUP: Set default width for new nodes
                const minSize = node.computeSize();
                const defaultWidth = 704;
                const defaultHeight = 256;
                node.size = [
                    Math.max(node.size[0], minSize[0], defaultWidth),
                    Math.max(node.size[1], minSize[1], defaultHeight)
                ];
                node.setDirtyCanvas(true, true);
            }, 1);

            // DYNAMIC RESIZING: Intercept execution to calculate dimensions based on specific aspect ratio constraints
            const originalOnExecuted = node.onExecuted;
            node.onExecuted = function (output) {
                if (originalOnExecuted) originalOnExecuted.apply(this, arguments);

                // Check if images are returned in the UI output
                const images = output?.images;
                if (images && images.length > 0) {
                    const imgMetadata = images[0];
                    const img = new Image();
                    
                    // Construct the view URL to preload the image metadata
                    img.src = `/view?filename=${encodeURIComponent(imgMetadata.filename)}&type=${imgMetadata.type}&subfolder=${encodeURIComponent(imgMetadata.subfolder)}`;
                    
                    img.onload = () => {
                        // Capture pre-execution boundaries configured by the user[cite: 2]
                        const initialWidth = this.size[0]; 
                        const initialHeight = this.size[1];
                        
                        // Vertical layout offset for the title bar and custom export button[cite: 2]
                        const widgetPadding = 60; 
                        
                        // Compute raw physical dimensions and structural ratios
                        const imgWidth = img.naturalWidth;
                        const imgHeight = img.naturalHeight;
                        const imageAspect = imgHeight / imgWidth;

                        let targetWidth = initialWidth;
                        let targetHeight = initialHeight;

                        // STRICT ASPECT RATIO DIRECTIONAL SCALING
                        if (imgWidth > imgHeight) {
                            // LANDSCAPE: Keep initial height, scale width proportionally based on clean canvas area
                            const activeCanvasHeight = Math.max(initialHeight - widgetPadding, 64);
                            targetWidth = activeCanvasHeight / imageAspect;
                            targetHeight = initialHeight; 
                        } else {
                            // PORTRAIT & SQUARE: Keep initial width, scale height proportionally and add layout padding
                            targetWidth = initialWidth;
                            targetHeight = (initialWidth * imageAspect) + widgetPadding;
                        }

                        // Apply new proportional bounding dimensions using safe layout ceilings
                        this.size = [
                            Math.max(targetWidth, 120), 
                            Math.max(targetHeight, 120)
                        ];
                        this.setDirtyCanvas(true, true);
                    };
                }
            };
        }
    }
});

// --- Dedicated Asynchronous Save Handler ---
async function handleImageSave(imageMetadata) {
    try {
        const url = `/view?filename=${encodeURIComponent(imageMetadata.filename)}&type=${imageMetadata.type}&subfolder=${encodeURIComponent(imageMetadata.subfolder)}`;
        const response = await api.fetchApi(url);
        if (!response.ok) throw new Error("Failed to retrieve image data from server");
        
        const blob = await response.blob();
        
        const now = new Date();
        const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
        const dynamicSuggestedName = `Comfyui_Image_${timestamp}.png`;
        
        const fileHandle = await window.showSaveFilePicker({
            suggestedName: dynamicSuggestedName,
            types: [{
                description: 'PNG Image File',
                accept: { 'image/png': ['.png'] }
            }]
        });
        
        const writable = await fileHandle.createWritable();
        await writable.write(blob);
        await writable.close();
        
    } catch (err) {
        if (err.name === 'AbortError') {
            console.log("NovA Tools: Save operation canceled by user.");
            return;
        }
        console.error("NovA Tools Error:", err);
        alert("An error occurred while saving the image.");
    }
}