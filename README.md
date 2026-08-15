# comfyui-NovA
Some (hopefully) useful nodes for ComfyUI, designed for Node 2.0, to simplify your workflows.

- The "NovAUnusedModelsManager" node allows you to view all your models (Diffusion, Text Encoder, VAE, etc.) that are not used by the workflows saved in `ComfyUI\user\default\workflows`. This lets you see at a glance which models can be safely deleted from your hard drive. Scanning for unused LoRA models is optional, as you might not be using them yet but still wish to keep them.
Deleting models remains a manual process, so there is no need to worry; the node simply provides an overview, while you retain full control.

- The all-in-one "NovAModelsLoader" node allows you to load the standard models required for text-to-image generation (Diffusion Model, Text Encoder, and VAE) within a single node, which means less "spaghetti" in your workflow.

- The all-in-one "NovALoraLoader" node allows you to stack LoRAs with a single click. For each loaded LoRA, the node includes a toggle switch to enable or disable it, as well as controls for adjusting the model and CLIP strength, which also means less "spaghetti" in your workflow.

- The "NovAText" and "NovAClipText" nodes add the ability to import or save your prompts as text files. The "NovAClipText" node also includes a "conditioning zero" output to simplify your workflows with Turbo models (cfg 1.0). Again, less "spaghetti" in your workflow.

- The "NovAKSampler" node, derived from the official node, incorporates new features: a VAE decoder is implemented directly within it (using the new "vae" input) , along with a resolution selector for the latent image. You can also chain other nodes thanks to its two new outputs "Model" and "Latent" (for instance, to perform a second upscaling pass). And again, less "spaghetti" in your workflow.

- The "NovAUltimateT2I" all-in-one node is designed to replace all other nodes used in a standard text-to-image workflow (including Krea2T-Enhancer-Advanced for K2T model). It is optimized to perform similarly to a standard workflow with multiple nodes. This node requires only a single "spaghetti" connection to link it to the final image preview.

List of the node features:
- Load/Save option for text prompt

__ Inputs__
- Diffusion Model loader
- Text Encoder loader
- VAE loader
- Multiple LoRA loader
- Resolution inputs
- All comon settings for standard KSampler

__ Outputs__
- Image
And optional, for subsequent operations:
- Conditioning
- Model
- Vae
- Latent
