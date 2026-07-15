import { app } from "/scripts/app.js";

app.registerExtension({
    name: "NovA.ClipTextButtons",
    async nodeCreated(node) {
        if (node.comfyClass === "NovAClipText") {
            
            setTimeout(() => {
                const textWidget = node.widgets?.find(w => w.name === "text");
                if (!textWidget) return;

                // Add button LOAD
                node.addWidget("button", "📂 Load Prompt", null, () => {
                    handleLoad(textWidget);
                });

                // Add button SAVE
                node.addWidget("button", "💾 Save Prompt", null, () => {
                    handleSave(textWidget.value);
                });

                // Calculating the minimum size required for the widgets.
                const minSize = node.computeSize();
                // Applying the maximum size among: what the user resized (node.size),
                // the minimum calculated by ComfyUI (minSize), and the default dimensions.
                node.size = [
                    Math.max(node.size[0], minSize[0], 400),
                    Math.max(node.size[1], minSize[1], 200)
                ];

                node.setDirtyCanvas(true, true);
            }, 1);
        }
    }
});

// --- Open / Save dedicated handlers ---

async function handleLoad(textWidget) {
    try {
        const [fileHandle] = await window.showOpenFilePicker({
            types: [{ description: 'Files Text', accept: { 'text/plain': ['.txt'] } }],
            multiple: false
        });
        const file = await fileHandle.getFile();
        const text = await file.text();
        
        textWidget.value = text;
        if (textWidget.callback) textWidget.callback(text);
    } catch (err) {
        if (err.name !== 'AbortError') console.error(err);
    }
}

async function handleSave(textContent) {
    try {
        const fileHandle = await window.showSaveFilePicker({
            suggestedName: 'prompt.txt',
            types: [{ description: 'Files Text', accept: { 'text/plain': ['.txt'] } }]
        });
        const writable = await fileHandle.createWritable();
        await writable.write(textContent);
        await writable.close();
    } catch (err) {
        if (err.name !== 'AbortError') console.error(err);
    }
}