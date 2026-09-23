# Lora_by_index (ComfyUI Custom Nodes)

A set of custom nodes for ComfyUI that allows you to load LoRAs and models (checkpoints / diffusion models) **by numerical index** from a specified folder. Perfect for mass testing: you can quickly switch between hundreds of files during generation without modifying the graph structure.

## ✨ Features

- **Load LoRA by index** — select a folder and a number, the node automatically fetches the corresponding file.
- **Load models by index** — support for both `checkpoints` and `diffusion_models`.
- **Automatic previews** — if an image with the same name exists next to the LoRA or model, the node will display it.
- **File lists** — the node outputs a complete list of available LoRAs/models with their indices.
- **Flexible LoRA strength** — `lora_strength` parameter with a 0.05 step and support for negative values.
- **`control_after_generate` compatibility** — automatically increment, decrement, or randomize the index after each generation.

## 🛠 Installation

1. Clone the repository into your ComfyUI `custom_nodes` folder:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/arc1111111/Lora_by_index.git
Install the required dependency (see below).
Restart ComfyUI.

📦 Dependencies
This custom node pack requires the following additional custom nodes to function properly:

Comfyroll Custom Nodes (for CR String To Combo)

Repository: https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes

Installation: Clone it into your custom_nodes folder or install via ComfyUI Manager.

The CR String To Combo node is used to convert string outputs (such as model_name or lora_name) into combo/dropdown selections, which are then consumed by standard ComfyUI loader nodes.


<img width="917" height="685" alt="Image1" src="https://github.com/user-attachments/assets/6e05839e-2d01-418a-a13b-fb32691e2f2a" />

<img width="963" height="877" alt="Image2" src="https://github.com/user-attachments/assets/19d1f93f-24a0-4d1d-b3fa-42279508aa66" />

<img width="1674" height="813" alt="Image3" src="https://github.com/user-attachments/assets/6fde7d42-2186-497a-99ed-71ed168cc973" />


