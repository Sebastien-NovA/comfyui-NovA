import { app } from "/scripts/app.js";

app.registerExtension({
    name: "NovA.TextButtons",
    async nodeCreated(node) {
        if (node.comfyClass === "NovAText") {
            
            setTimeout(() => {
                const textWidget = node.widgets?.find(w => w.name === "text");
                if (!textWidget) return;

                // 1. Add button LOAD
                node.addWidget("button", "📂 Load Prompt", null, () => {
                    handleLoad(textWidget);
                });

                // 2. Add button SAVE
                node.addWidget("button", "💾 Save Prompt", null, () => {
                    handleSave(textWidget.value);
                });

                // On calcule la taille minimale requise pour les widgets
                const minSize = node.computeSize();
                
                // On applique la taille maximum entre : ce que l'utilisateur a redimensionné (node.size), 
                // le minimum calculé par ComfyUI (minSize), et nos dimensions par défaut.
                node.size = [
                    Math.max(node.size[0], minSize[0], 500),
                    Math.max(node.size[1], minSize[1], 400)
                ];

                node.setDirtyCanvas(true, true);
            }, 1);
        }
    }
});

// --- Gestionnaires d'ouverture / Sauvegarde ---

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