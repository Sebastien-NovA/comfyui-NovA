import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
    name: "NovA.UnusedNodesManager",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "NovAUnusedNodesManager") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            const onExecuted = nodeType.prototype.onExecuted;
            const onConfigure = nodeType.prototype.onConfigure;
            const onResize = nodeType.prototype.onResize;

            // Initialize or retrieve custom DOM container widget
            function ensureDisplayWidget(node) {
                let widget = node.widgets?.find(w => w.name === "unused_nodes_display");
                if (!widget) {
                    const container = document.createElement("div");
                    container.className = "nova-unused-nodes-container";

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

                    widget = node.addDOMWidget("unused_nodes_display", "display", container, {
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

            // Update DOM content and calculate container height relative to node size
            function updateWidgetContent(node, widget, rawText) {
                if (!rawText) return;

                widget.element.innerHTML = parseTextToCollapsibleHTML(rawText);

                const linesCount = rawText.split("\n").length;
                const calculatedHeight = Math.min(600, Math.max(220, linesCount * 18 + 140));
                node.setSize([Math.max(500, node.size[0]), calculatedHeight]);

                adjustWidgetHeight(node, widget);
            }

            // Recalculate widget height according to node container dimensions
            function adjustWidgetHeight(node, widget) {
                if (!widget || !widget.element) return;

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

            nodeType.prototype.onResize = function(size) {
                onResize?.apply(this, arguments);
                const widget = this.widgets?.find(w => w.name === "unused_nodes_display");
                if (widget) {
                    adjustWidgetHeight(this, widget);
                }
            };
        }
    }
});

/**
 * Parses raw text and structures package blocks into collapsible HTML <details> and <summary> elements.
 */
function parseTextToCollapsibleHTML(text) {
    // Sanitize input to prevent HTML injection attacks
    let safeText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    
    // Return standard text if no header patterns exist
    if (!safeText.includes(":")) {
        return `<span style="color: #cccccc;">${safeText}</span>`;
    }

    const lines = safeText.split("\n");
    let htmlOutput = "";
    let currentFolderHeader = null;
    let currentNodesList = [];

    function appendCurrentGroup() {
        if (currentFolderHeader) {
            const folderMatch = currentFolderHeader.match(/^(.+?)\s*\((.+?)\):$/);
            let title = currentFolderHeader;
            let stats = "";

            if (folderMatch) {
                title = folderMatch[1];
                stats = `(${folderMatch[2]})`;
            }

            const nodesContent = currentNodesList.map(n => `<div style="padding-left: 12px; color: #aaaaaa;">${n}</div>`).join("");

            htmlOutput += `
                <details style="margin-bottom: 6px; cursor: pointer;">
                    <summary style="font-weight: bold; color: #4ba3e3; outline: none; user-select: none;">
                        <span>${title}</span>
                        <span style="color: #888888; font-weight: normal; font-size: 11px; margin-left: 6px;">${stats}</span>
                    </summary>
                    <div style="margin-top: 4px; border-left: 2px solid #333333; margin-left: 4px;">
                        ${nodesContent}
                    </div>
                </details>
            `;
        }
    }

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (trimmed.endsWith(":")) {
            appendCurrentGroup();
            currentFolderHeader = trimmed;
            currentNodesList = [];
        } else if (trimmed.startsWith("-")) {
            currentNodesList.push(trimmed);
        }
    }

    appendCurrentGroup();
    return htmlOutput;
}