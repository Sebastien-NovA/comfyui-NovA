import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
    name: "NovA.UnusedModelsManager",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovAUnusedModelsManager") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            const onExecuted = nodeType.prototype.onExecuted;
            const onConfigure = nodeType.prototype.onConfigure;
            const onResize = nodeType.prototype.onResize;

            // Initialize or retrieve the custom DOM container widget
            function ensureDisplayWidget(node) {
                let widget = node.widgets?.find(w => w.name === "unused_models_display");
                if (!widget) {
                    const container = document.createElement("div");
                    container.className = "nova-unused-models-container";
                    
                    // Flexbox layout and dynamic sizing rules
                    container.style.cssText = `
                        background-color: var(--comfy-input-bg);
                        color: #cccccc;
                        font-family: monospace;
                        font-size: 12px;
                        padding: 8px;
                        border-radius: 4px;
                        overflow-y: auto;
                        white-space: pre-wrap;
                        word-break: break-all;
                        box-sizing: border-box;
                        width: 100%;
                        height: 100%;
                        flex-grow: 1;
                    `;

                    widget = node.addDOMWidget("unused_models_display", "display", container, {
                        getValue: () => node.properties?.saved_display_text || "",
                        setValue: (val) => {
                            node.properties.saved_display_text = val;
                            updateWidgetContent(node, widget, val);
                        }
                    });

                    if (!node.properties) node.properties = {};
                }
                return widget;
            }

            // Update DOM content and calculate container height relative to available node space
            function updateWidgetContent(node, widget, rawText) {
                if (!rawText) return;
                
                widget.element.innerHTML = parseFormattedTextToHTML(rawText);

                // Attach security-validated API triggers for opening target directories
                const links = widget.element.querySelectorAll(".nova-folder-link");
                links.forEach(link => {
                    link.addEventListener("click", async (e) => {
                        e.preventDefault();
                        const folderName = link.getAttribute("data-folder");
                        
                        try {
                            await api.fetchApi("/nova/open_folder", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ folder_name: folderName })
                            });
                        } catch (err) {
                            console.error("[NovA Models Manager] Failed to open folder:", err);
                        }
                    });
                });

                // Auto-fit node dimensions dynamically based on scanned data height
                const linesCount = rawText.split("\n").length;
                const calculatedHeight = Math.min(600, Math.max(220, linesCount * 18 + 140));
                node.setSize([Math.max(500, node.size[0]), calculatedHeight]);
                
                adjustWidgetHeight(node, widget);
            }

            // Recalculate widget container height to match current node canvas dimensions
            function adjustWidgetHeight(node, widget) {
                if (!widget || !widget.element) return;
                
                // Estimate header and controls offset (title bar + inputs height)
                const topMarginOffset = 130; 
                const availableHeight = Math.max(100, node.size[1] - topMarginOffset);
                widget.element.style.height = `${availableHeight}px`;
            }

            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);
                ensureDisplayWidget(this);
            };

            nodeType.prototype.onConfigure = function(serializedData) {
                onConfigure?.apply(this, arguments);
                const widget = ensureDisplayWidget(this);
                if (this.properties?.saved_display_text) {
                    updateWidgetContent(this, widget, this.properties.saved_display_text);
                }
            };

            nodeType.prototype.onExecuted = function(message) {
                onExecuted?.apply(this, arguments);
                
                if (message?.text) {
                    const textPayload = message.text[0];
                    const widget = ensureDisplayWidget(this);
                    
                    this.properties.saved_display_text = textPayload;
                    updateWidgetContent(this, widget, textPayload);
                }
            };

            // Dynamically resize DOM element when user resizes node handle on canvas
            nodeType.prototype.onResize = function(size) {
                onResize?.apply(this, arguments);
                const widget = this.widgets?.find(w => w.name === "unused_models_display");
                if (widget) {
                    adjustWidgetHeight(this, widget);
                }
            };
        }
    }
});

/**
 * Format plain text into styled HTML elements (Headers = White, Folder Links = Blue, Files = Light Gray)
 */
function parseFormattedTextToHTML(text) {
    let safeText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const lines = safeText.split("\n");
    const regex = /Unused \[([^\]]+)\]\(([^)]+)\) \((\d+)\):/;

    const formattedLines = lines.map(line => {
        const headerMatch = line.match(regex);
        if (headerMatch) {
            const label = headerMatch[1];
            const folder = headerMatch[2];
            const count = headerMatch[3];
            
            return `<span style="color: #ffffff; font-weight: bold;">Unused </span>` +
                   `<span class="nova-folder-link" data-folder="${folder}" style="color: #0066cc; text-decoration: underline; cursor: pointer; font-weight: bold;" title="Open folder in system explorer">${label}</span>` +
                   `<span style="color: #ffffff; font-weight: bold;"> (${count}):</span>`;
        }
        
        return `<span style="color: #cccccc;">${line}</span>`;
    });

    return formattedLines.join("\n");
}
