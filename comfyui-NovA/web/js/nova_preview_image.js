import { app } from "/scripts/app.js";
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

                // Minimal size adjustment to cleanly accommodate the added save button
                const minSize = node.computeSize();
                node.size = [
                    Math.max(node.size[0], minSize[0]),
                    Math.max(node.size[1], minSize[1] + 60) // Add margin for the action button
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
                        // --- TRACK USER RESIZING VS PROGRAMMATIC RESIZING ---
                        // Update base reference only if the node size changed outside of the script (manual user resize)
                        if (!this.userBaseWidth || Math.abs(this.size[0] - (this.lastProgrammaticWidth || 0)) > 2) {
                            this.userBaseWidth = this.size[0];
                        }
                        if (!this.userBaseHeight || Math.abs(this.size[1] - (this.lastProgrammaticHeight || 0)) > 2) {
                            this.userBaseHeight = this.size[1];
                        }

                        const initialWidth = this.userBaseWidth; 
                        const initialHeight = this.userBaseHeight;
                        
                        // Compute raw physical dimensions and structural ratios
                        const imgWidth = img.naturalWidth;
                        const imgHeight = img.naturalHeight;
                        const imageAspect = imgHeight / imgWidth;

                        let targetWidth = initialWidth;
                        let targetHeight = initialHeight;

                        // --- ADAPTIVE ASPECT RATIO SCALING ---
                        if (imgWidth > imgHeight) {
                            // LANDSCAPE:
                            // Raw base calculation for landscape layout (mandatory)
                            const baseTargetWidth = initialHeight / imageAspect;
                            targetWidth = baseTargetWidth - 216;
							targetHeight = initialHeight;
                        } else if (imgWidth === imgHeight) {
                            // SQUARE
                            targetWidth = initialWidth - 96;
                            targetHeight = initialWidth * imageAspect;
                        } else {
                            // PORTRAIT:
                            targetWidth = initialWidth - 64;
                            targetHeight = initialWidth * imageAspect;
                        }

                        // Apply new proportional bounding dimensions using safe layout ceilings
                        this.size = [
                            Math.max(targetWidth, 120), 
                            Math.max(targetHeight, 120)
                        ];

                        // Cache the newly applied size to bypass shrinking loops on subsequent executions
                        this.lastProgrammaticWidth = this.size[0];
                        this.lastProgrammaticHeight = this.size[1];

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