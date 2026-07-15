# comfyui-NovA
Some (hopefully) useful nodes for ComfyUI, designed for Node 2.0, to simplify your workflows.

- The all-in-one "NovAModelsLoader" node allows you to load the standard models required for text-to-image generation (Diffusion Model, Text Encoder, and VAE) within a single node.

- The all-in-one "NovALoraLoader" node allows you to stack LoRAs with a single click. For each loaded LoRA, the node includes a toggle switch to enable or disable it, as well as controls for adjusting the model and CLIP strength, which also means less "spaghetti" in your workflow!

- The "NovAText" and "NovAClipText" nodes add the ability to import or save your prompts as text files. The "NovAClipText" node also includes a "conditioning zero" output to simplify your workflows with Turbo models (cfg 1.0). Again, less "spaghetti" in your workflow.

- The "NovAKSampler" node, derived from the official node, incorporates new features: a VAE decoder is implemented directly within it (using the new "vae" input) , along with an advanced resolution selector for the latent image. You can also chain other nodes thanks to its two new outputs "Model" and "Latent" (for instance, to perform a second upscaling pass). And again, less "spaghetti" in your workflow (yes, it's an obsession).

- The "NovAUltimateT2I" all-in-one node is designed to replace all other nodes used in a standard text-to-image workflow (including Krea2T-Enhancer-Advanced for K2T model, and ModelSamplingAuraFlow for ZiT & Flux model). It is still under development, but you can try it out nonetheless; notably, this node requires only a single "spaghetti" connection to link it to an image preview.
