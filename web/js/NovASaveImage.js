import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

/**
 * Triggers a file download for the active image in a given node.
 * @param {Object} node - LiteGraph node instance containing rendered images.
 * @param {string} prefix - Filename prefix to prepend.
 * @returns {Promise<boolean>} True if an image was successfully downloaded, false otherwise.
 */
async function saveImageFromNode(node, prefix = "") {
    if (!node || node.mode === 2 || node.mode === 4) {
        return false;
    }

    if (node.imgs && node.imgs.length > 0) {
        const activeImgIndex = node.imageIndex || 0;
        const imgElement = node.imgs[activeImgIndex];

        if (imgElement && imgElement.src) {
            const url = new URL(imgElement.src, window.location.origin);
            const originalFilename = url.searchParams.get("filename") || `ComfyUI_temp_${Date.now()}.png`;
            const subfolder = url.searchParams.get("subfolder") || "";
            const type = url.searchParams.get("type") || "output";

            const trimmedPrefix = prefix.trim();
            const targetFilename = trimmedPrefix ? `${trimmedPrefix}_${originalFilename}` : originalFilename;

            const fetchUrl = api.apiURL(
                `/view?filename=${encodeURIComponent(originalFilename)}&subfolder=${encodeURIComponent(subfolder)}&type=${encodeURIComponent(type)}`
            );

            try {
                const response = await fetch(fetchUrl);
                if (!response.ok) throw new Error("Network response error during image fetch.");

                const blob = await response.blob();
                const objectUrl = URL.createObjectURL(blob);

                const downloadLink = document.createElement("a");
                downloadLink.href = objectUrl;
                downloadLink.download = targetFilename;

                document.body.appendChild(downloadLink);
                downloadLink.click();

                document.body.removeChild(downloadLink);
                URL.revokeObjectURL(objectUrl);
                return true;
            } catch (error) {
                console.error("NovASaveImage: Failed to download image", error);
                return false;
            }
        }
    }
    return false;
}

/**
 * Resolves whether the NovASaveImage node is connected to an upstream or sibling preview node.
 * @param {Object} node - The NovASaveImage LiteGraph node instance.
 * @returns {{ isConnected: boolean, previewNode: Object|null }} Connection status and target preview node.
 */
function findConnectedPreviewNode(node) {
    const input = node.inputs?.find((i) => i.name === "images" || i.type === "IMAGE");
    if (!input || input.link === null || input.link === undefined) {
        return { isConnected: false, previewNode: null };
    }

    const link = app.graph.links[input.link];
    if (!link) {
        return { isConnected: false, previewNode: null };
    }

    const upstreamNode = app.graph.getNodeById(link.origin_id);
    if (!upstreamNode) {
        return { isConnected: true, previewNode: null };
    }

    // Direct connection to a node with rendered preview images
    if (upstreamNode.imgs && upstreamNode.imgs.length > 0) {
        return { isConnected: true, previewNode: upstreamNode };
    }

    // Direct connection to a bypassed or muted node
    if (upstreamNode.mode === 2 || upstreamNode.mode === 4) {
        return { isConnected: true, previewNode: upstreamNode };
    }

    // Direct connection to a node sharing its output slot with a Preview Image node
    const outputSlot = upstreamNode.outputs?.[link.origin_slot];
    if (outputSlot && outputSlot.links) {
        for (const linkId of outputSlot.links) {
            const siblingLink = app.graph.links[linkId];
            if (!siblingLink) continue;

            const siblingNode = app.graph.getNodeById(siblingLink.target_id);
            if (siblingNode && siblingNode.id !== node.id) {
                if (
                    (siblingNode.imgs && siblingNode.imgs.length > 0) ||
                    siblingNode.comfyClass === "PreviewImage" ||
                    siblingNode.comfyClass === "SaveImage"
                ) {
                    return { isConnected: true, previewNode: siblingNode };
                }
            }
        }
    }

    return { isConnected: true, previewNode: upstreamNode };
}

/**
 * Fallback mechanism to find and save from the first active, non-bypassed preview node in the graph.
 * @param {string} prefix - Filename prefix to prepend.
 */
async function triggerSaveOnFirstActivePreview(prefix = "") {
    if (!app.graph || !app.graph._nodes) return;

    for (const node of app.graph._nodes) {
        // Skip bypassed (mode 2) or muted (mode 4) nodes
        if (node.mode === 2 || node.mode === 4) {
            continue;
        }

        const success = await saveImageFromNode(node, prefix);
        if (success) break;
    }
}

// Global hotkey event listener
window.addEventListener("keydown", (event) => {
    // Prevent execution while typing in text widgets
    const activeElem = document.activeElement;
    if (activeElem && (activeElem.tagName === "INPUT" || activeElem.tagName === "TEXTAREA")) {
        return;
    }

    if (!app.graph || !app.graph._nodes) {
        return;
    }

    const pressedKey = event.key.toLowerCase();

    for (const node of app.graph._nodes) {
        if (node.comfyClass === "NovASaveImage" && node.mode !== 2 && node.mode !== 4) {
            const shortcutWidget = node.widgets?.find((w) => w.name === "save_image_key");
            const prefixWidget = node.widgets?.find((w) => w.name === "add_prefix");

            const shortcutValue = String(shortcutWidget?.value || "").trim().toLowerCase();

            if (shortcutValue && pressedKey === shortcutValue) {
                event.preventDefault();
                const prefixValue = String(prefixWidget?.value || "").trim();

                const { isConnected, previewNode } = findConnectedPreviewNode(node);

                if (isConnected) {
                    if (previewNode) {
                        // Abort silently if connected preview node is bypassed or muted
                        if (previewNode.mode === 2 || previewNode.mode === 4) {
                            return;
                        }
                        saveImageFromNode(previewNode, prefixValue);
                    }
                } else {
                    // Fallback to graph-wide search when disconnected
                    triggerSaveOnFirstActivePreview(prefixValue);
                }
                break;
            }
        }
    }
});

// Extension registration core
app.registerExtension({
    name: "NovA.SaveImageKeyShortcut",

    async nodeCreated(node) {
        if (node.comfyClass === "NovASaveImage") {
            for (const widgetName of ["save_image_key", "add_prefix"]) {
                const widget = node.widgets?.find((w) => w.name === widgetName);
                if (widget && widget.inputEl) {
                    widget.inputEl.addEventListener("keydown", (e) => {
                        if (e.key === "Enter") widget.inputEl.blur();
                    });
                }
            }
        }
    }
});